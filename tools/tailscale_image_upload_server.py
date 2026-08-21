#!/usr/bin/env python3
"""Small single-user image upload server for Tailscale and loopback transfers."""

from __future__ import annotations

import argparse
import html
import ipaddress
import os
import re
import subprocess
import tempfile
from email.message import Message
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable


MAX_UPLOAD_BYTES = 100 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
TAILSCALE_NETWORK = ipaddress.ip_network("100.64.0.0/10")
TAILSCALE_EXECUTABLES = (
    Path("/usr/local/bin/tailscale"),
    Path("/opt/homebrew/bin/tailscale"),
    Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale"),
    Path("/usr/bin/tailscale"),
)
TAILSCALE_COMMAND_TIMEOUT_SECONDS = 3
MAX_MULTIPART_BOUNDARY_BYTES = 70


class UploadTooLarge(ValueError):
    """Raised when a declared request body exceeds the upload limit."""


def clean_name(name: str) -> str:
    base = os.path.basename(name).strip() or "upload"
    base = re.sub(r"[^A-Za-z0-9._ -]+", "_", base)
    base = base.lstrip(".").strip()
    return base[:180] or "upload"


def save_unique(directory: Path, filename: str, payload: bytes) -> Path:
    cleaned = clean_name(filename)
    parsed = Path(cleaned)
    stem = parsed.stem or "upload"
    suffix = parsed.suffix
    for count in range(10_000):
        target_name = cleaned if count == 0 else f"{stem}-{count}{suffix}"
        candidate = directory / target_name
        try:
            descriptor = os.open(
                candidate,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            continue
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
        except Exception:
            candidate.unlink(missing_ok=True)
            raise
        return candidate
    raise RuntimeError("too many uploads use the same filename")


def supported_filename(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def upload_size_allowed(size: int) -> bool:
    return 0 < size <= MAX_UPLOAD_BYTES


def parse_content_length(value: str | None) -> int:
    try:
        size = int(value or "0")
    except ValueError as error:
        raise ValueError("invalid Content-Length") from error
    if size <= 0:
        raise ValueError("Content-Length must be positive")
    if size > MAX_UPLOAD_BYTES:
        raise UploadTooLarge("upload too large")
    return size


def parse_multipart_boundary(content_type: str) -> bytes:
    if "\r" in content_type or "\n" in content_type:
        raise ValueError("multipart boundary is invalid")
    message = Message()
    message["content-type"] = content_type
    if message.get_content_type().lower() != "multipart/form-data":
        raise ValueError("multipart/form-data required")
    token = message.get_param("boundary", header="content-type")
    if not isinstance(token, str) or not token:
        raise ValueError("multipart boundary required")
    try:
        encoded = token.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("multipart boundary must be ASCII") from error
    if not 1 <= len(encoded) <= MAX_MULTIPART_BOUNDARY_BYTES:
        raise ValueError("multipart boundary length is invalid")
    if token != token.strip() or "\r" in token or "\n" in token:
        raise ValueError("multipart boundary is invalid")
    return encoded


def classify_host(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as error:
        raise ValueError(
            "host must be exact 127.0.0.1 or a Tailscale IPv4 address"
        ) from error
    if not isinstance(address, ipaddress.IPv4Address):
        raise ValueError("IPv6 bind targets are not supported")
    if address == ipaddress.ip_address("127.0.0.1"):
        return "loopback"
    if address in TAILSCALE_NETWORK:
        return "tailscale"
    raise ValueError("host must be exact 127.0.0.1 or a Tailscale IPv4 address")


def parse_tailscale_ipv4s(output: str) -> list[str]:
    addresses: list[str] = []
    for token in output.split():
        try:
            address = ipaddress.ip_address(token)
        except ValueError:
            continue
        if not isinstance(address, ipaddress.IPv4Address):
            continue
        normalized = str(address)
        if address in TAILSCALE_NETWORK and normalized not in addresses:
            addresses.append(normalized)
    return addresses


def tailscale_executable() -> str:
    for candidate in TAILSCALE_EXECUTABLES:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise RuntimeError("Tailscale CLI is unavailable; install or start Tailscale first")


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def resolve_tailscale_ipv4(
    *,
    executable: str | None = None,
    runner: CommandRunner = subprocess.run,
) -> str:
    command = [executable or tailscale_executable(), "ip", "-4"]
    try:
        result = runner(
            command,
            capture_output=True,
            text=True,
            timeout=TAILSCALE_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Tailscale CLI is unavailable") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Tailscale address lookup timed out") from error
    except OSError as error:
        raise RuntimeError("Tailscale address lookup could not run") from error
    if result.returncode != 0:
        raise RuntimeError("Tailscale address lookup failed; ensure Tailscale is running")
    addresses = parse_tailscale_ipv4s(result.stdout)
    if not addresses:
        raise RuntimeError("Tailscale did not return a valid private IPv4 address")
    if len(addresses) != 1:
        raise RuntimeError(
            "Tailscale returned multiple private IPv4 addresses; choose one with --host"
        )
    return addresses[0]


def resolve_bind_host(
    explicit_host: str | None,
    *,
    resolver: Callable[[], str] = resolve_tailscale_ipv4,
) -> str:
    host = explicit_host if explicit_host is not None else resolver()
    classify_host(host)
    return host


def runtime_options(
    host: str | None,
    port: int,
    directory: str | None,
    *,
    resolver: Callable[[], str] = resolve_tailscale_ipv4,
) -> tuple[str, int, Path]:
    bind_host = resolve_bind_host(host, resolver=resolver)
    if not 1 <= port <= 65_535:
        raise ValueError("port must be between 1 and 65535")
    if not directory:
        raise ValueError("--dir is required outside --selftest")
    return bind_host, port, Path(directory).expanduser().resolve()


class UploadHandler(BaseHTTPRequestHandler):
    server_version = "CodeXImageUpload/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def do_GET(self) -> None:
        if self.path not in {"/", "/index.html"}:
            self.send_error(404)
            return
        self._send_html(self._page())

    def do_POST(self) -> None:
        if self.path != "/upload":
            self.send_error(404)
            return
        content_type = self.headers.get("Content-Type", "")
        try:
            boundary_token = parse_multipart_boundary(content_type)
        except ValueError as error:
            self.send_error(400, str(error))
            return
        try:
            content_length = parse_content_length(self.headers.get("Content-Length"))
        except UploadTooLarge as error:
            self.send_error(413, str(error))
            return
        except ValueError as error:
            self.send_error(400, str(error))
            return

        body = self.rfile.read(content_length)
        boundary = b"--" + boundary_token
        saved = []

        for part in body.split(boundary):
            if b"Content-Disposition:" not in part or b"filename=" not in part:
                continue
            header, _, payload = part.partition(b"\r\n\r\n")
            if not payload:
                continue
            payload = payload.rsplit(b"\r\n", 1)[0]
            header_text = header.decode("utf-8", "replace")
            match = re.search(r'filename="([^"]*)"', header_text)
            filename = clean_name(match.group(1) if match else "upload")
            if not supported_filename(filename):
                continue
            if not payload:
                continue
            try:
                target = save_unique(  # type: ignore[attr-defined]
                    self.server.upload_dir,
                    filename,
                    payload,
                )
            except (OSError, RuntimeError):
                self.send_error(500, "could not save upload")
                return
            saved.append(target.name)

        if not saved:
            self.send_error(400, "no supported image files uploaded")
            return
        self._send_html(self._page(saved=saved))

    def _send_html(self, content: str) -> None:
        encoded = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _page(self, saved: list[str] | None = None) -> str:
        directory = html.escape(str(self.server.upload_dir))  # type: ignore[attr-defined]
        saved_html = ""
        if saved:
            items = "".join(f"<li>{html.escape(name)}</li>" for name in saved)
            saved_html = f"<section><h2>Uploaded</h2><ul>{items}</ul></section>"
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CodeX ComfyUI Upload</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 24px; line-height: 1.4; }}
    form {{ display: grid; gap: 16px; max-width: 520px; }}
    input, button {{ font-size: 18px; padding: 12px; }}
    button {{ background: #0a84ff; color: white; border: 0; border-radius: 8px; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <h1>ComfyUI iPhone Upload</h1>
  <p>Saving images into <code>{directory}</code>.</p>
  {saved_html}
  <form action="/upload" method="post" enctype="multipart/form-data">
    <input type="file" name="files" accept="image/*" multiple>
    <button type="submit">Upload Images</button>
  </form>
</body>
</html>"""


def run_selftest(*, require_live: bool = False) -> int:
    pure_cases = 0

    def check(condition: bool, label: str) -> None:
        nonlocal pure_cases
        pure_cases += 1
        if not condition:
            raise AssertionError(label)

    for host, expected in (
        ("127.0.0.1", "loopback"),
        ("100.64.0.1", "tailscale"),
        ("100.127.255.254", "tailscale"),
    ):
        check(classify_host(host) == expected, f"host class: {host}")
    for host in (
        "0.0.0.0",
        "127.0.0.2",
        "100.63.255.255",
        "100.128.0.1",
        "192.168.1.20",
        "8.8.8.8",
        "::1",
        "localhost",
        "not-an-address",
    ):
        try:
            classify_host(host)
        except ValueError:
            check(True, f"reject host: {host}")
        else:
            check(False, f"reject host: {host}")

    class Result:
        def __init__(self, returncode: int, stdout: str) -> None:
            self.returncode = returncode
            self.stdout = stdout

    def runner_for(
        *, returncode: int = 0, stdout: str = "", error: BaseException | None = None
    ) -> CommandRunner:
        def fake_runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            check(command[1:] == ["ip", "-4"], "fixed command")
            check(kwargs.get("capture_output") is True, "capture output")
            check(kwargs.get("text") is True, "text output")
            check(kwargs.get("timeout") == TAILSCALE_COMMAND_TIMEOUT_SECONDS, "timeout")
            check(kwargs.get("check") is False, "no implicit exception")
            if error is not None:
                raise error
            return Result(returncode, stdout)  # type: ignore[return-value]

        return fake_runner

    failure_cases = (
        runner_for(error=FileNotFoundError()),
        runner_for(returncode=1),
        runner_for(error=subprocess.TimeoutExpired(["tailscale", "ip", "-4"], 3)),
        runner_for(stdout=""),
        runner_for(stdout="malformed output\n"),
        runner_for(stdout="100.64.0.1\n100.64.0.2\n"),
    )
    for runner in failure_cases:
        try:
            resolve_tailscale_ipv4(executable="tailscale", runner=runner)
        except RuntimeError:
            check(True, "fail-closed command outcome")
        else:
            check(False, "fail-closed command outcome")

    check(
        classify_host(
            resolve_tailscale_ipv4(
                executable="tailscale",
                runner=runner_for(stdout="100.64.0.8\n"),
            )
        )
        == "tailscale",
        "one valid address",
    )
    check(
        resolve_tailscale_ipv4(
            executable="tailscale",
            runner=runner_for(stdout="100.64.0.8\n100.64.0.8\n"),
        )
        == "100.64.0.8",
        "identical duplicate address",
    )

    check(clean_name("../../camera snow.png") == "camera snow.png", "path sanitization")
    check(clean_name("../bad/<name>.heic") == "_name_.heic", "filename sanitization")
    check(clean_name("..") == "upload", "parent directory filename")
    check(clean_name(".hidden.jpg") == "hidden.jpg", "leading dot filename")
    check(supported_filename("photo.JPEG"), "supported extension")
    check(not supported_filename("payload.txt"), "unsupported extension")
    check(upload_size_allowed(1), "minimum upload size")
    check(upload_size_allowed(MAX_UPLOAD_BYTES), "maximum upload size")
    check(not upload_size_allowed(0), "zero upload size")
    check(not upload_size_allowed(MAX_UPLOAD_BYTES + 1), "oversized upload")
    check(parse_content_length("1") == 1, "content length")
    for content_length in (None, "", "0", "-1", "not-a-number"):
        try:
            parse_content_length(content_length)
        except ValueError:
            check(True, "invalid content length")
        else:
            check(False, "invalid content length")
    try:
        parse_content_length(str(MAX_UPLOAD_BYTES + 1))
    except UploadTooLarge:
        check(True, "content length over limit")
    else:
        check(False, "content length over limit")

    check(
        parse_multipart_boundary('multipart/form-data; boundary="upload-boundary"')
        == b"upload-boundary",
        "quoted multipart boundary",
    )
    for content_type in (
        "",
        "text/plain",
        "multipart/form-data",
        "multipart/form-data; boundary=",
        "multipart/form-data; boundary=has\nnewline",
        f"multipart/form-data; boundary={'x' * (MAX_MULTIPART_BOUNDARY_BYTES + 1)}",
    ):
        try:
            parse_multipart_boundary(content_type)
        except ValueError:
            check(True, "invalid multipart boundary")
        else:
            check(False, "invalid multipart boundary")

    with tempfile.TemporaryDirectory() as temporary_directory:
        upload_dir = Path(temporary_directory)
        first = save_unique(upload_dir, "same.jpg", b"first")
        second = save_unique(upload_dir, "same.jpg", b"second")
        check(first.name == "same.jpg", "first unique filename")
        check(second.name == "same-1.jpg", "second unique filename")
        check(first.read_bytes() == b"first", "first upload preserved")
        check(second.read_bytes() == b"second", "second upload preserved")
        check(first.stat().st_mode & 0o777 == 0o600, "private upload mode")

    resolver_called = False

    def forbidden_resolver() -> str:
        nonlocal resolver_called
        resolver_called = True
        raise AssertionError("resolver called for explicit host")

    try:
        runtime_options("0.0.0.0", 8769, "/unused", resolver=forbidden_resolver)
    except ValueError:
        check(not resolver_called, "invalid explicit host fails before resolver or side effects")
    else:
        check(False, "invalid explicit host")

    try:
        live_address = resolve_tailscale_ipv4()
        live_class = classify_host(live_address)
    except RuntimeError as error:
        status = "BLOCKED" if require_live else "PASS"
        print(
            f"selftest={status} pure_status=PASS pure_cases={pure_cases} "
            f"live_status=BLOCKED live_required={str(require_live).lower()} "
            f"reason={error}"
        )
        return 1 if require_live else 0
    print(
        f"selftest=PASS pure_status=PASS pure_cases={pure_cases} "
        f"live_status=PASS live_class={live_class} live_count=1"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Receive images on the current Tailscale IPv4 address. "
            "The default fails closed if exactly one tailnet address is unavailable."
        )
    )
    parser.add_argument(
        "--host",
        help="exact 127.0.0.1 for local smoke use, or an IPv4 in 100.64.0.0/10",
    )
    parser.add_argument("--port", type=int, default=8769)
    parser.add_argument("--dir", help="directory where accepted images are saved")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run pure policy checks and report the live Tailscale class if available",
    )
    parser.add_argument(
        "--require-live",
        action="store_true",
        help="make --selftest fail unless the live Tailscale address check passes",
    )
    args = parser.parse_args()

    if args.selftest:
        return run_selftest(require_live=args.require_live)
    if args.require_live:
        parser.error("--require-live requires --selftest")
    try:
        bind_host, port, upload_dir = runtime_options(args.host, args.port, args.dir)
    except (RuntimeError, ValueError) as error:
        parser.error(str(error))
    upload_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    server = ThreadingHTTPServer((bind_host, port), UploadHandler)
    server.upload_dir = upload_dir  # type: ignore[attr-defined]
    print(f"serving http://{bind_host}:{port}/ -> {upload_dir}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopped", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
