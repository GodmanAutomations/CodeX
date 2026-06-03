#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the bridge command."""
    parser = argparse.ArgumentParser(
        description="Send a message to a Codex Cloud HTTP endpoint."
    )
    parser.add_argument("message", nargs="?", help="Message to send. Reads stdin if omitted.")
    return parser.parse_args()


def _read_message(cli_message: str | None) -> str:
    """Return message from CLI argument or stdin, or exit with a usage error."""
    if cli_message:
        return cli_message
    if not sys.stdin.isatty():
        piped = sys.stdin.read().strip()
        if piped:
            return piped
    raise SystemExit("No message provided. Pass one as an argument or via stdin.")


def _build_request(url: str, api_key: str | None, message: str) -> urllib.request.Request:
    """Create an authenticated HTTP request to the Codex Cloud endpoint."""
    payload = json.dumps({"message": message}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        if any(ord(char) < 32 or ord(char) == 127 for char in api_key):
            raise SystemExit(
                "CODEX_API_KEY must not contain control characters."
            )
        headers["Authorization"] = "Bearer " + api_key
    return urllib.request.Request(url=url, data=payload, headers=headers, method="POST")


def _validate_url(url: str) -> None:
    """Ensure endpoint URL is absolute and includes scheme and host."""
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise SystemExit("CODEX_CLOUD_URL must be a valid absolute URL.")


def main() -> int:
    """Send a user message to Codex Cloud and return a process exit code."""
    args = _parse_args()
    message = _read_message(args.message)
    url = os.getenv("CODEX_CLOUD_URL")
    if not url:
        raise SystemExit("CODEX_CLOUD_URL is required.")
    _validate_url(url)
    api_key = os.getenv("CODEX_API_KEY")
    timeout_raw = os.getenv("CODEX_CLOUD_TIMEOUT", "30")
    try:
        timeout = float(timeout_raw)
    except ValueError:
        raise SystemExit(f"CODEX_CLOUD_TIMEOUT must be a number, got: {timeout_raw!r}")
    if timeout <= 0:
        raise SystemExit(f"CODEX_CLOUD_TIMEOUT must be > 0, got: {timeout_raw!r}")

    request = _build_request(url=url, api_key=api_key, message=message)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            try:
                body = response.read().decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                print("Response body is not valid UTF-8.", file=sys.stderr)
                return 1
            print(body)
            return 0
    except urllib.error.HTTPError as exc:
        try:
            details = exc.read().decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            details = "<non-UTF-8 error body>"
        print(f"Request failed ({exc.code}): {details}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Unable to reach Codex Cloud endpoint: {exc.reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
