#!/usr/bin/env python3
"""CodeX's isolated headless Camoufox browser lane."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse


ARTIFACTS = Path("/Users/stephengodman/CodeX/browser/artifacts")
DEFAULT_ENGINE = "camoufox"


def extract_headlines_camoufox(url: str, limit: int) -> dict:
    from camoufox.sync_api import Camoufox

    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        headlines = page.locator(".titleline > a").evaluate_all(
            f"(els) => els.slice(0, {limit}).map(a => a.innerText)"
        )
        return {
            "engine": "camoufox",
            "browser": "Camoufox",
            "url": url,
            "headlines": headlines or [],
        }


def read_page_camoufox(url: str, limit: int) -> dict:
    from camoufox.sync_api import Camoufox

    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        payload = page.evaluate(
            """(limit) => {
              const clean = (text) => (text || '').replace(/\\s+/g, ' ').trim();
              const headings = Array.from(document.querySelectorAll('h1,h2,h3'))
                .map((node) => clean(node.innerText || node.textContent))
                .filter(Boolean)
                .slice(0, limit);
              const links = Array.from(document.querySelectorAll('a[href]'))
                .map((a) => ({
                  text: clean(a.innerText || a.textContent),
                  href: a.href
                }))
                .filter((item) => item.text && item.href)
                .slice(0, limit);
              const paragraphs = Array.from(document.querySelectorAll('p,li,article,main,section,td,blockquote,.quote,.text,[class*="content"]'))
                .map((node) => clean(node.innerText || node.textContent))
                .filter((text) => text.length >= 25)
                .slice(0, limit);
              return {
                title: document.title,
                url: location.href,
                headings,
                links,
                paragraphs
              };
            }""",
            limit,
        )
        return {
            "engine": "camoufox",
            "browser": "Camoufox",
            **payload,
        }


def slugify_url(url: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in url)
    clean = "-".join(part for part in clean.split("-") if part)
    return clean[:90] or "page"


def same_domain(seed_url: str, candidate_url: str) -> bool:
    seed = urlparse(seed_url)
    candidate = urlparse(candidate_url)
    return candidate.scheme in {"http", "https"} and candidate.netloc == seed.netloc


def normalize_url(seed_url: str, href: str) -> str | None:
    if not href:
        return None
    if href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    joined = urljoin(seed_url, href)
    joined, _fragment = urldefrag(joined)
    parsed = urlparse(joined)
    if parsed.scheme not in {"http", "https"}:
        return None
    return joined


def screenshot_camoufox(url: str, full_page: bool = True) -> dict:
    from camoufox.sync_api import Camoufox

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    path = ARTIFACTS / f"{stamp}-{slugify_url(url)}.png"
    with Camoufox(headless=True) as browser:
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.screenshot(path=str(path), full_page=full_page)
        return {
            "engine": "camoufox",
            "browser": "Camoufox",
            "url": page.url,
            "screenshot": str(path),
        }


def capture_page_camoufox(page, url: str, limit: int, screenshot_dir: Path) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    payload = page.evaluate(
        """(limit) => {
          const clean = (text) => (text || '').replace(/\\s+/g, ' ').trim();
          const headings = Array.from(document.querySelectorAll('h1,h2,h3'))
            .map((node) => clean(node.innerText || node.textContent))
            .filter(Boolean)
            .slice(0, limit);
          const links = Array.from(document.querySelectorAll('a[href]'))
            .map((a) => ({
              text: clean(a.innerText || a.textContent),
              href: a.getAttribute('href'),
              absolute: a.href
            }))
            .filter((item) => item.absolute)
            .slice(0, 80);
          const snippets = Array.from(document.querySelectorAll('p,li,article,main,section,td,blockquote,.quote,.text,[class*="content"]'))
            .map((node) => clean(node.innerText || node.textContent))
            .filter((text) => text.length >= 25)
            .slice(0, limit);
          return {
            title: document.title,
            url: location.href,
            headings,
            snippets,
            links
          };
        }""",
        limit,
    )
    screenshot = screenshot_dir / f"{slugify_url(payload.get('url', url))}.png"
    page.screenshot(path=str(screenshot), full_page=True)
    payload["screenshot"] = str(screenshot)
    return payload


def crawl_lite_camoufox(seed_url: str, max_pages: int, limit: int) -> dict:
    from camoufox.sync_api import Camoufox

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    crawl_dir = ARTIFACTS / f"{stamp}-crawl-{slugify_url(seed_url)}"
    crawl_dir.mkdir(parents=True, exist_ok=True)
    report_path = crawl_dir / "crawl-lite-report.md"

    queue = [seed_url]
    seen: set[str] = set()
    pages: list[dict] = []

    with Camoufox(headless=True) as browser:
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        while queue and len(pages) < max_pages:
            current = queue.pop(0)
            normalized_current = normalize_url(seed_url, current)
            if not normalized_current or normalized_current in seen:
                continue
            if not same_domain(seed_url, normalized_current):
                continue
            seen.add(normalized_current)
            try:
                captured = capture_page_camoufox(page, normalized_current, limit, crawl_dir)
            except Exception as exc:  # noqa: BLE001 - report page-level crawl failures
                pages.append(
                    {
                        "url": normalized_current,
                        "title": "",
                        "headings": [],
                        "snippets": [f"ERROR: {exc}"],
                        "links": [],
                        "screenshot": "",
                    }
                )
                continue
            pages.append(captured)
            for link in captured.get("links", []):
                next_url = normalize_url(captured["url"], link.get("absolute") or link.get("href") or "")
                if next_url and same_domain(seed_url, next_url) and next_url not in seen and next_url not in queue:
                    queue.append(next_url)

    lines = [
        "# CodeX Crawl Lite Report",
        "",
        f"- UTC: {stamp}",
        "- Engine: camoufox",
        f"- Seed URL: {seed_url}",
        f"- Pages visited: {len(pages)}",
        f"- Max pages: {max_pages}",
        "- Scope: same-domain only, read-only, no forms/submits/downloads",
        "",
    ]
    for index, page_data in enumerate(pages, start=1):
        lines.extend(
            [
                f"## Page {index}: {page_data.get('title') or '(untitled)'}",
                "",
                f"- URL: {page_data.get('url')}",
                f"- Screenshot: {page_data.get('screenshot')}",
                "",
                "### Headings",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in page_data.get("headings", []))
        lines.extend(["", "### Text Snippets", ""])
        lines.extend(f"- {item}" for item in page_data.get("snippets", []))
        lines.extend(["", "### Same-domain Links Seen", ""])
        same_site_links = []
        for link in page_data.get("links", []):
            next_url = normalize_url(page_data.get("url", seed_url), link.get("absolute") or link.get("href") or "")
            if next_url and same_domain(seed_url, next_url):
                same_site_links.append((link.get("text") or next_url, next_url))
        lines.extend(f"- [{text}]({href})" for text, href in same_site_links[:limit])
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "engine": "camoufox",
        "seed_url": seed_url,
        "pages_visited": len(pages),
        "report": str(report_path),
        "artifact_dir": str(crawl_dir),
        "pages": [
            {
                "title": page.get("title"),
                "url": page.get("url"),
                "screenshot": page.get("screenshot"),
            }
            for page in pages
        ],
    }


def write_report_camoufox(url: str, limit: int) -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{stamp}-{slugify_url(url)}"
    report_path = ARTIFACTS / f"{stem}.md"
    shot = screenshot_camoufox(url)
    page = read_page_camoufox(url, limit)
    lines = [
        "# CodeX Browser Report",
        "",
        f"- UTC: {stamp}",
        f"- Engine: {page['engine']}",
        f"- Browser: {page['browser']}",
        f"- Title: {page.get('title', '')}",
        f"- URL: {page.get('url', url)}",
        f"- Screenshot: {shot['screenshot']}",
        "",
        "## Headings",
        "",
    ]
    lines.extend(f"- {item}" for item in page.get("headings", []))
    lines.extend(["", "## Text Snippets", ""])
    lines.extend(f"- {item}" for item in page.get("paragraphs", []))
    lines.extend(["", "## Links", ""])
    lines.extend(f"- [{item['text']}]({item['href']})" for item in page.get("links", []))
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "engine": page["engine"],
        "browser": page["browser"],
        "url": page.get("url", url),
        "title": page.get("title", ""),
        "report": str(report_path),
        "screenshot": shot["screenshot"],
    }


def extract_headlines(url: str, limit: int, engine: str) -> dict:
    if engine == "camoufox":
        return extract_headlines_camoufox(url, limit)
    raise ValueError(f"Unknown engine: {engine}")


def read_page(url: str, limit: int, engine: str) -> dict:
    if engine != "camoufox":
        raise ValueError("read currently supports --engine camoufox")
    return read_page_camoufox(url, limit)


def screenshot_page(url: str, engine: str) -> dict:
    if engine != "camoufox":
        raise ValueError("screenshot currently supports --engine camoufox")
    return screenshot_camoufox(url)


def report_page(url: str, limit: int, engine: str) -> dict:
    if engine != "camoufox":
        raise ValueError("report currently supports --engine camoufox")
    return write_report_camoufox(url, limit)


def crawl_lite(seed_url: str, max_pages: int, limit: int, engine: str) -> dict:
    if engine != "camoufox":
        raise ValueError("crawl-lite currently supports --engine camoufox")
    return crawl_lite_camoufox(seed_url, max(1, min(max_pages, 10)), max(1, min(limit, 25)))


def main() -> int:
    parser = argparse.ArgumentParser(description="CodeX headless browser smoke tools.")
    sub = parser.add_subparsers(dest="command", required=True)

    headlines = sub.add_parser("headlines", help="Extract first visible headlines/links from a page.")
    headlines.add_argument("url", nargs="?", default="https://news.ycombinator.com")
    headlines.add_argument("--limit", type=int, default=3)
    headlines.add_argument("--engine", choices=["camoufox"], default=DEFAULT_ENGINE)
    headlines.add_argument("--json", action="store_true")

    read = sub.add_parser("read", help="Read title, headings, snippets, and links from a page.")
    read.add_argument("url")
    read.add_argument("--limit", type=int, default=8)
    read.add_argument("--engine", choices=["camoufox"], default="camoufox")
    read.add_argument("--json", action="store_true")

    screenshot = sub.add_parser("screenshot", help="Capture a page screenshot with Camoufox.")
    screenshot.add_argument("url")
    screenshot.add_argument("--engine", choices=["camoufox"], default="camoufox")
    screenshot.add_argument("--json", action="store_true")

    report = sub.add_parser("report", help="Write a markdown page report and screenshot.")
    report.add_argument("url")
    report.add_argument("--limit", type=int, default=8)
    report.add_argument("--engine", choices=["camoufox"], default="camoufox")
    report.add_argument("--json", action="store_true")

    crawl = sub.add_parser("crawl-lite", help="Bounded same-domain page scout with reports/screenshots.")
    crawl.add_argument("url")
    crawl.add_argument("--max-pages", type=int, default=5)
    crawl.add_argument("--limit", type=int, default=6)
    crawl.add_argument("--engine", choices=["camoufox"], default="camoufox")
    crawl.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.command == "headlines":
        payload = extract_headlines(args.url, max(1, min(args.limit, 25)), args.engine)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"engine: {payload['engine']}")
            print(f"browser: {payload.get('browser')}")
            print(f"url: {payload['url']}")
            for index, headline in enumerate(payload["headlines"], start=1):
                print(f"{index}. {headline}")
        return 0

    if args.command == "read":
        payload = read_page(args.url, max(1, min(args.limit, 25)), args.engine)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"engine: {payload['engine']}")
            print(f"browser: {payload.get('browser')}")
            print(f"title: {payload.get('title')}")
            print(f"url: {payload.get('url')}")
            print("\nheadings:")
            for item in payload.get("headings", []):
                print(f"- {item}")
            print("\ntext snippets:")
            for item in payload.get("paragraphs", []):
                print(f"- {item}")
            print("\nlinks:")
            for item in payload.get("links", []):
                print(f"- {item['text']} -> {item['href']}")
        return 0

    if args.command == "screenshot":
        payload = screenshot_page(args.url, args.engine)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"engine: {payload['engine']}")
            print(f"url: {payload['url']}")
            print(f"screenshot: {payload['screenshot']}")
        return 0

    if args.command == "report":
        payload = report_page(args.url, max(1, min(args.limit, 25)), args.engine)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"engine: {payload['engine']}")
            print(f"title: {payload['title']}")
            print(f"url: {payload['url']}")
            print(f"report: {payload['report']}")
            print(f"screenshot: {payload['screenshot']}")
        return 0

    if args.command == "crawl-lite":
        payload = crawl_lite(args.url, args.max_pages, args.limit, args.engine)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"engine: {payload['engine']}")
            print(f"seed_url: {payload['seed_url']}")
            print(f"pages_visited: {payload['pages_visited']}")
            print(f"report: {payload['report']}")
            print(f"artifact_dir: {payload['artifact_dir']}")
            for index, page in enumerate(payload["pages"], start=1):
                print(f"{index}. {page.get('title')} — {page.get('url')}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
