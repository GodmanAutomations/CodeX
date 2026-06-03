#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a message to a Codex Cloud HTTP endpoint."
    )
    parser.add_argument("message", nargs="?", help="Message to send. Reads stdin if omitted.")
    return parser.parse_args()


def _read_message(cli_message: str | None) -> str:
    if cli_message:
        return cli_message
    if not sys.stdin.isatty():
        piped = sys.stdin.read().strip()
        if piped:
            return piped
    raise SystemExit("No message provided. Pass one as an argument or via stdin.")


def _build_request(url: str, api_key: str | None, message: str) -> urllib.request.Request:
    payload = json.dumps({"message": message}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        if "\r" in api_key or "\n" in api_key:
            raise SystemExit("CODEX_API_KEY contains invalid characters.")
        headers["Authorization"] = "Bearer " + api_key
    return urllib.request.Request(url=url, data=payload, headers=headers, method="POST")


def main() -> int:
    args = _parse_args()
    message = _read_message(args.message)
    url = os.getenv("CODEX_CLOUD_URL")
    if not url:
        raise SystemExit("CODEX_CLOUD_URL is required.")
    api_key = os.getenv("CODEX_API_KEY")
    timeout_raw = os.getenv("CODEX_CLOUD_TIMEOUT", "30")
    try:
        timeout = float(timeout_raw)
        if timeout <= 0:
            raise ValueError
    except ValueError:
        raise SystemExit("CODEX_CLOUD_TIMEOUT must be a positive number.")

    request = _build_request(url=url, api_key=api_key, message=message)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(body)
            return 0
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        print(f"Request failed ({exc.code}): {details}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Unable to reach Codex Cloud endpoint: {exc.reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
