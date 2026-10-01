# -*- coding: utf-8 -*-
"""Pulls the latest posts from blog.valorahq.com (a real, live Ghost blog
under Bhavya Barot's byline) at build time, for the "advisor acquisition"
proof section on advisors.html: Valora's own AEO/GEO content marketing is
part of the pitch to advisors, so this embeds real posts, not placeholders.

Network access is a nice-to-have at build time, not a hard dependency —
if the feed can't be reached (offline, blog down), FALLBACK below is used
so `python3 _build/build.py` never breaks. FALLBACK is a snapshot taken
2026-09-27; refresh it occasionally by re-running with network access and
copying the printed result.
"""
import html
import re
import urllib.request

FEED_URL = "https://blog.valorahq.com/rss/"

FALLBACK = [
    {"title": "Video Builds the Most Trust in Advisor Marketing. It Also Costs $37,170 a Client.",
     "url": "https://blog.valorahq.com/advisor-video-marketing-cost-37170-trust/",
     "excerpt": "The Kitces 2026 study says video builds the most trust in advisor marketing at a $37,170 client acquisition cost. Here is the cheaper trust channel most RIAs are missing."},
    {"title": "GEO vs SEO: What Actually Changes for an Advisory Firm's Website",
     "url": "https://blog.valorahq.com/geo-vs-seo-advisory-firm-website/",
     "excerpt": "What actually changes when you optimize an advisory firm's site for AI answer engines instead of, or alongside, traditional search."},
    {"title": "How to Get Your Firm Recommended by ChatGPT and Perplexity",
     "url": "https://blog.valorahq.com/how-to-get-your-firm-recommended-by-chatgpt-and-perplexity/",
     "excerpt": "A practical look at what makes an advisory firm citable by AI search and chat assistants."},
]


def _text(pattern, block, default=""):
    m = re.search(pattern, block, re.S)
    if not m:
        return default
    return html.unescape(m.group(1)).strip()


def latest_posts(n=3):
    try:
        req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Valora-site-build/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            xml = r.read().decode("utf-8", errors="replace")
    except Exception:
        return FALLBACK[:n]

    items = re.findall(r"<item>(.*?)</item>", xml, re.S)
    posts = []
    for it in items[:n]:
        title = _text(r"<title><!\[CDATA\[(.*?)\]\]></title>", it)
        link = _text(r"<link>(.*?)</link>", it)
        excerpt = _text(r"<description><!\[CDATA\[(.*?)\]\]></description>", it)
        if title and link:
            posts.append({"title": title, "url": link, "excerpt": excerpt})
    return posts or FALLBACK[:n]


if __name__ == "__main__":
    import json
    print(json.dumps(latest_posts(6), indent=2))
