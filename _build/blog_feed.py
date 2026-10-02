# -*- coding: utf-8 -*-
"""Pulls the latest posts from insights.spacesos.com (blog.valorahq.com
redirects there; a real, live Ghost blog
under Bhavya Barot's byline) at build time, for the "advisor acquisition"
proof section on advisors.html: Valora's own AEO/GEO content marketing is
part of the pitch to advisors, so this embeds real posts, not placeholders.

Network access is a nice-to-have at build time, not a hard dependency —
if the feed can't be reached (offline, blog down), FALLBACK below is used
so `python3 _build/build.py` never breaks. FALLBACK is a snapshot taken
2026-10-02; refresh it occasionally by re-running with network access and
copying the printed result.
"""
import html
import re
import urllib.request
from email.utils import parsedate_to_datetime

FEED_URL = "https://insights.spacesos.com/rss/"
BLOG_URL = "https://insights.spacesos.com/"

FALLBACK = [
    {"title": "How should an RIA turn a client service model into a written service calendar?", "url": "https://insights.spacesos.com/how-should-an-ria-turn-a-client-service-model-into-a-written-service-calendar/", "excerpt": "Turn an RIA service model into deliverables, triggers and responsibilities. Use a written calendar without treating meeting frequency as the whole engagement.", "image": "https://insights.spacesos.com/content/images/2026/10/14-hero.jpg", "date": "Oct 2, 2026"},
    {"title": "What should a solo RIA include in a business-continuity handoff?", "url": "https://insights.spacesos.com/what-should-a-solo-ria-include-in-a-business-continuity-handoff/", "excerpt": "Prepare a solo RIA continuity handoff with scenarios, authorized backups and alternate contact paths. Test permissions and records before a disruption.", "image": "https://insights.spacesos.com/content/images/2026/10/13-hero.jpg", "date": "Oct 2, 2026"},
    {"title": "What should an RIA request before a first prospect call?", "url": "https://insights.spacesos.com/what-should-an-ria-request-before-a-first-prospect-call/", "excerpt": "Stage prospect information requests around purpose, handling and the next decision. Use a request worksheet without treating it as a compliance certificate.", "image": "https://insights.spacesos.com/content/images/2026/10/what-should-an-ria-request-before-a-first-prospect-call/hero.jpg", "date": "Oct 1, 2026"},
    {"title": "How should an RIA build a website claim-review ledger?", "url": "https://insights.spacesos.com/how-should-an-ria-build-a-website-claim-review-ledger/", "excerpt": "Connect website claims to evidence, limitations and exact reviewed versions. Use a claim ledger to check what readers infer, not only whether citations exist.", "image": "https://insights.spacesos.com/content/images/2026/10/how-should-an-ria-build-a-website-claim-review-ledger/hero.jpg", "date": "Oct 1, 2026"},
    {"title": "When should an RIA update, merge or retire an old article?", "url": "https://insights.spacesos.com/when-should-an-ria-update-merge-or-retire-an-old-article/", "excerpt": "Choose which RIA articles to keep, update, merge or retire using a reader-first worksheet, current sources and truthful revision dates.", "image": "https://insights.spacesos.com/content/images/2026/09/sep30-maintenance-header-1600x840.jpg", "date": "Sep 30, 2026"},
    {"title": "What should an RIA check before using a client testimonial?", "url": "https://insights.spacesos.com/what-should-an-ria-check-before-using-a-client-testimonial/", "excerpt": "Review the quote, permission, compensation, disclosures, oversight and records before using a client testimonial in RIA marketing.", "image": "https://insights.spacesos.com/content/images/2026/09/sep30-testimonials-header-1600x840.jpg", "date": "Sep 30, 2026"},
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
        image = _text(r'<media:content url="([^"]+)"', it)
        date = _date(_text(r"<pubDate>(.*?)</pubDate>", it))
        # Only ever link/hotlink the blog's own https origin.
        if not link.startswith(BLOG_URL):
            continue
        if not image.startswith(BLOG_URL):
            image = ""
        if title:
            posts.append({"title": title, "url": link, "excerpt": excerpt, "image": image, "date": date})
    return posts or FALLBACK[:n]


def _date(rfc822):
    try:
        return parsedate_to_datetime(rfc822).strftime("%b %-d, %Y")
    except Exception:
        return ""


if __name__ == "__main__":
    import json
    print(json.dumps(latest_posts(6), indent=2))
