#!/usr/bin/env python3
"""Small single-user image upload server for Tailscale-only transfers."""

from __future__ import annotations

import argparse
import html
import os
import re
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs


MAX_UPLOAD_BYTES = 100 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


def clean_name(name: str) -> str:
    base = os.path.basename(name).strip() or "upload"
    base = re.sub(r"[^A-Za-z0-9._ -]+", "_", base)
    return base[:180]


def unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / clean_name(filename)
    stem = candidate.stem or "upload"
    suffix = candidate.suffix
    count = 1
    while candidate.exists():
        candidate = directory / f"{stem}-{count}{suffix}"
        count += 1
    return candidate


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
        if "multipart/form-data" not in content_type:
            self.send_error(400, "multipart/form-data required")
            return
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0 or content_length > MAX_UPLOAD_BYTES:
            self.send_error(413, "upload too large")
            return

        body = self.rfile.read(content_length)
        boundary_token = content_type.split("boundary=", 1)[-1].strip().strip('"')
        boundary = ("--" + boundary_token).encode()
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
            filename = match.group(1) if match else "upload"
            suffix = Path(filename).suffix.lower()
            if suffix not in ALLOWED_EXTENSIONS:
                continue
            target = unique_path(self.server.upload_dir, filename)  # type: ignore[attr-defined]
            target.write_bytes(payload)
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


def tailscale_ip() -> str:
    candidates = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
    for item in candidates:
        ip = item[4][0]
        if ip.startswith("100."):
            return ip
    return "127.0.0.1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=tailscale_ip())
    parser.add_argument("--port", type=int, default=8769)
    parser.add_argument("--dir", required=True)
    args = parser.parse_args()

    upload_dir = Path(args.dir).expanduser().resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer((args.host, args.port), UploadHandler)
    server.upload_dir = upload_dir  # type: ignore[attr-defined]
    print(f"serving http://{args.host}:{args.port}/ -> {upload_dir}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
