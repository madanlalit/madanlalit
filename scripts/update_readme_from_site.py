#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin
from urllib.request import Request, urlopen


README_MARKER_START = "<!-- latest-posts:start -->"
README_MARKER_END = "<!-- latest-posts:end -->"
DEFAULT_SITE_URL = "https://lalitmadan.com"
DEFAULT_POST_LIMIT = 5
USER_AGENT = "madanlalit-readme-updater/1.0"


def fetch_html(site_url: str) -> str:
    request = Request(site_url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def read_html_from_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(title: str) -> str:
    title = strip_tags(title)
    title = title.replace("→", "").strip()
    return title


def recent_heading_before(html_text: str, anchor_start: int) -> str:
    window = html_text[max(0, anchor_start - 500) : anchor_start]
    headings = re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", window, flags=re.IGNORECASE | re.DOTALL)
    for heading in reversed(headings):
        title = normalize_title(heading)
        if title:
            return title
    return ""


def extract_posts(html_text: str, site_url: str, limit: int) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"<a[^>]+href=[\"'](?P<href>/post/[^\"'#?]+)[^\"']*[\"'][^>]*>(?P<body>.*?)</a>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    seen: set[str] = set()
    posts: list[tuple[str, str]] = []

    for match in pattern.finditer(html_text):
        href = match.group("href").strip()
        if href in seen:
            continue

        title = normalize_title(match.group("body"))
        if not title or title.lower() == "read entry":
            title = recent_heading_before(html_text, match.start())
        if not title or title.lower() == "read entry":
            continue

        seen.add(href)
        posts.append((title, urljoin(site_url, href)))
        if len(posts) >= limit:
            break

    return posts


def render_posts(posts: Iterable[tuple[str, str]], site_url: str) -> str:
    lines = [
        README_MARKER_START,
    ]

    for title, url in posts:
        lines.append(f"[{title}]({url})  ")

    if lines[-1] == README_MARKER_START:
        lines.append(f"No posts found — visit [{site_url}]({site_url})")

    lines.extend(
        [
            README_MARKER_END,
        ]
    )
    return "\n".join(lines)


def update_readme(readme_path: Path, rendered_posts: str) -> None:
    original = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(README_MARKER_START)}.*?{re.escape(README_MARKER_END)}",
        flags=re.DOTALL,
    )

    if not pattern.search(original):
        raise ValueError(
            "README.md is missing the Latest Posts markers. "
            f"Expected {README_MARKER_START} and {README_MARKER_END}."
        )

    updated = pattern.sub(rendered_posts, original, count=1)
    readme_path.write_text(updated.rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update profile README with latest blog links.")
    parser.add_argument("--readme", default="README.md", help="Path to the README file.")
    parser.add_argument("--site-url", default=os.getenv("SITE_URL", DEFAULT_SITE_URL), help="Website URL.")
    parser.add_argument("--limit", type=int, default=DEFAULT_POST_LIMIT, help="Number of blog posts to include.")
    parser.add_argument("--html-file", help="Use a local HTML file instead of fetching the site.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    readme_path = Path(args.readme)

    html_text = read_html_from_file(Path(args.html_file)) if args.html_file else fetch_html(args.site_url)
    posts = extract_posts(html_text, args.site_url, args.limit)
    if not posts:
        print("No blog posts found in site HTML.", file=sys.stderr)
        return 1

    rendered_posts = render_posts(posts, args.site_url)
    update_readme(readme_path, rendered_posts)
    print(f"Updated {readme_path} with {len(posts)} blog links from {args.site_url}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
