# -*- coding: utf-8 -*-
"""Flag on-page markup the AEO audit called out.

Scans public HTML (not _release snapshots, generator sources, or the admin tool).
Redirect stubs are skipped. Exits 1 when it finds:

- a missing Open Graph or Twitter card tag
- a <title> longer than 65 characters
- a meta description longer than 160 characters
- more than one <h1> in the static HTML
- the retired homepage title or the retired public inbox

    python3 _build/check_markup.py
"""
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"_release", "_build", "_insights-site", ".git", "admin"}
OG_KEYS = ("og:title", "og:description", "og:url", "og:type", "og:image")
TWITTER_KEYS = ("twitter:card", "twitter:title", "twitter:description", "twitter:image")
TITLE_LIMIT = 65
DESCRIPTION_LIMIT = 160
STALE = (
    "AI-Powered Outbound Infrastructure for B2B Sales",
    "barot@valorahq.com",
)


def _pages():
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if set(rel.parts) & SKIP_DIRS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        head = text[:2000].lower()
        if "http-equiv=\"refresh\"" in head or "http-equiv='refresh'" in head:
            continue
        yield rel.as_posix(), text


def _meta_keys(html):
    found = set()
    for match in re.finditer(r"<meta\b[^>]*>", html, flags=re.I):
        key = re.search(r"(?:name|property)\s*=\s*[\"']([^\"']+)[\"']", match.group(0), flags=re.I)
        if key:
            found.add(key.group(1).lower())
    return found


def _title(html):
    match = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    if not match:
        return None
    return unescape(re.sub(r"\s+", " ", match.group(1))).strip()


def _description(html):
    for match in re.finditer(r"<meta\b[^>]*>", html, flags=re.I):
        tag = match.group(0)
        if not re.search(r"name\s*=\s*[\"']description[\"']", tag, flags=re.I):
            continue
        content = re.search(r"content\s*=\s*[\"'](.*?)[\"']", tag, flags=re.I | re.S)
        if content:
            return unescape(re.sub(r"\s+", " ", content.group(1))).strip()
    return None


def _h1_count(html):
    cleaned = re.sub(r"<script\b[\s\S]*?</script>|<style\b[\s\S]*?</style>", "", html, flags=re.I)
    return len(re.findall(r"<h1\b", cleaned, flags=re.I))


def main():
    problems = []
    scanned = 0
    for rel, html in _pages():
        scanned += 1
        keys = _meta_keys(html)
        for key in OG_KEYS + TWITTER_KEYS:
            if key not in keys:
                problems.append(f"missing {key}: {rel}")
        title = _title(html)
        if title is not None and len(title) > TITLE_LIMIT:
            problems.append(f"title {len(title)}>{TITLE_LIMIT}: {rel}: {title}")
        description = _description(html)
        if description is not None and len(description) > DESCRIPTION_LIMIT:
            problems.append(f"description {len(description)}>{DESCRIPTION_LIMIT}: {rel}: {description}")
        h1s = _h1_count(html)
        if h1s > 1:
            problems.append(f"h1 count {h1s}: {rel}")
        for stale in STALE:
            if stale in html:
                problems.append(f"stale string {stale!r}: {rel}")
    if problems:
        print(f"FAIL {len(problems)} issue(s) in {scanned} pages")
        for line in problems:
            print(line)
        return 1
    print(f"PASS {scanned} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
