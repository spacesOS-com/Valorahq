# -*- coding: utf-8 -*-
"""Build Valora's static pages.

    python _build/build.py

Writes:
  /for-advisors/                 "For advisors" page (plus an /advisors.html redirect for old links)
and refreshes the <!-- @build:... --> regions in index.html
(head, header, hero card, contact form, footer, opening modal).
"""
import os
import re
import sys
from xml.sax.saxutils import escape as xml_escape

sys.path.insert(0, os.path.dirname(__file__))
from partials import (BRAND, head, page, header, footer, gate, hero_card, contact_section, RB2B_SNIPPET,
                       faq_schema, client_faq_section, CLIENT_FAQ, SCRIPT_VER)
from advisors_page import for_advisors_body, FOR_ADVISORS_FAQ
from advisor_pages import ADVISORS
from directory_pages import build_directory_pages, build_cities_index, build_specialties_index, build_professions_index, build_asset_types_index, SPECIALTIES, CITIES, NICHES, ASSET_TYPES, real_pages, real_combos
from us_directory_pages import build_us_directory, real_pages as us_real_pages, all_states as us_all_states
from insights_pages import build_insights_pages, ARTICLES
from calculator_pages import build_calculator_pages, CALCULATORS, CATEGORIES
from content_pages import build_content_pages
from intake_page import build_intake_page
from concierge_page import build_concierge_page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = "https://www.valorahq.com"

# Every live page, one line each. Add a page here when it goes live and the
# sitemap, llms.txt and llms-full.txt all pick it up on the next build.
PAGES = [
    # (path, one-line description for llms.txt)
    ("/", "Home — how Valora matches people with independent, fiduciary financial advisors."),
    ("/for-advisors/", "For advisors — how independent advisors join Valora's network."),
    ("/find-your-advisor/", "Find your advisor — four-question intake; each request is reviewed by hand."),
    ("/guides/", "Financial advice guides for tech employees, physicians and business owners."),
    ("/calculators/", "Browse financial calculators by topic."),
    ("/cities/", "Browse financial advisors by city."),
    ("/specialties/", "Browse financial advisors by specialty."),
    ("/professions/", "Browse financial advisors by profession."),
    ("/asset-types/", "Browse financial advisors by investable-asset range."),
    ("/top-financial-advisors/", "Top financial advisors in the U.S., by state and city."),
] + [(f"/top-financial-advisors/{slug}/", f"Top financial advisors in {name}.") for slug, name in us_all_states()
] + [
    # only pages with a real advisor match — see directory_pages.real_pages().
    # Empty-state specialty/city/niche/asset-type pages still get built (as
    # useful scaffolding for a visitor who lands on them) but are marked
    # noindex and left out of the sitemap/llms.txt on purpose.
    (f"/find-a-financial-advisor/{slug}/", desc) for slug, desc in real_pages()
] + [
    # /top-financial-advisors/[state]/[city]/ — only real matches (same rule)
    (path, desc) for path, desc in us_real_pages()
] + [(f"/insights/{a['slug']}/", a["summary"]) for a in ARTICLES
] + [(f"/calculators/{c['slug']}/", c["summary"]) for c in CALCULATORS if not c.get("noindex")
] + [(f"/calculators/{cat.lower().replace(' ', '-')}/", f"{cat} calculators on Valora.") for cat in CATEGORIES]


def write(path, html):
    out = os.path.join(ROOT, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(ROOT, path.strip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)


def build_for_advisors():
    html = page(head(f"For Advisors | {BRAND} — Practice Growth & Infrastructure Platform",
                     "Valora for independent financial advisors: verified fiduciary introductions to prospective clients, "
                     "turnkey digital onboarding, tax-intelligent rebalancing, and a practice that stays 100% yours.",
                     path="/for-advisors/", schema=faq_schema(FOR_ADVISORS_FAQ)),
                for_advisors_body(), active="advisors")
    html = html.replace('<a class="btn btn--dark" href="/#contact" data-gate-open>Ask a question</a>',
                        '<a class="btn btn--dark" href="#apply">Apply to join</a>', 1)
    write("/for-advisors/", html)

    # keep the old /advisors.html URL alive as a redirect, so existing
    # links/bookmarks to it still land on the real page
    write("/advisors.html", f"""<!DOCTYPE html>
<html lang="en-US"><head><meta charset="UTF-8">
<meta http-equiv="refresh" content="0; url=/for-advisors/">
<link rel="canonical" href="{SITE_URL}/for-advisors/">
<title>Redirecting… | {BRAND}</title>
{RB2B_SNIPPET}
</head><body>
<p>This page has moved to <a href="/for-advisors/">/for-advisors/</a>.</p>
</body></html>
""")


# ====================================================================== index.html regions
def refresh_index():
    p = os.path.join(ROOT, "index.html")
    with open(p, encoding="utf-8") as f:
        html = f.read()
    regions = {
        "head": head(f"{BRAND} — Your money has a purpose",
                     "Explore independent financial advisors. Valora helps you find advisors who work with "
                     "situations like yours — you decide who you'd like to contact.",
                     path="/", schema=faq_schema(CLIENT_FAQ)),
        "header": header(None, banner=True),
        "hero-card": hero_card(),
        "faq": client_faq_section(),
        "contact": contact_section(),
        "footer": footer(),
        "gate": gate(),
    }
    for name, content in regions.items():
        pat = re.compile(r"(<!-- @build:%s -->)(.*?)(<!-- /@build:%s -->)" % (re.escape(name), re.escape(name)), re.S)
        if not pat.search(html):
            raise SystemExit(f"index.html is missing the @build:{name} markers")
        html = pat.sub(lambda m: m.group(1) + "\n" + content + "\n" + m.group(3), html)
    html = re.sub(r'<script src="/(?:assets/)?script\.js(?:\?v=[a-f0-9]+)?"></script>',
                  f'<script src="/assets/script.js?v={SCRIPT_VER}"></script>', html)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)


# ====================================================================== robots.txt / sitemap.xml / llms.txt
def build_robots():
    write("/robots.txt", f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
""")


def build_sitemap():
    import datetime
    today = datetime.date.today().isoformat()
    urls = "\n".join(
        f"""  <url>
    <loc>{xml_escape(SITE_URL + path)}</loc>
    <lastmod>{today}</lastmod>
  </url>""" for path, _ in PAGES
    )
    write("/sitemap.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
""")


def build_llms():
    lines = "\n".join(f"- [{SITE_URL}{path}]({SITE_URL}{path}): {desc}" for path, desc in PAGES)
    write("/llms.txt", f"""# {BRAND}

> Valora is an independent platform that matches people with vetted, independent
> fiduciary financial advisors based on their situation. Valora does not itself
> provide investment advice; advisors on the platform are independent and are
> not employees of Valora.

## Pages

{lines}
""")

    # llms-full.txt inlines each page's plain-text content so a crawler can
    # read the whole site without following links. Built from the same
    # source the pages are built from, so it can't drift out of sync.
    sections = []
    for path, desc in PAGES:
        if path == "/" or path.endswith("/"):
            file_path = os.path.join(ROOT, path.strip("/"), "index.html")
        else:
            file_path = os.path.join(ROOT, path.strip("/"))
        try:
            with open(file_path, encoding="utf-8") as f:
                html = f.read()
        except FileNotFoundError:
            continue
        text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
        sections.append(f"# {SITE_URL}{path}\n{desc}\n\n{text}")
    write("/llms-full.txt", "\n\n---\n\n".join(sections) + "\n")


if __name__ == "__main__":
    build_for_advisors()
    build_directory_pages(write)
    build_cities_index(write)
    build_specialties_index(write)
    build_professions_index(write)
    build_asset_types_index(write)
    build_us_directory(write)
    build_insights_pages(write)
    build_calculator_pages(write)
    PAGES.extend(build_content_pages(write))
    build_intake_page(write)
    build_concierge_page(write)
    refresh_index()
    build_robots()
    build_sitemap()
    build_llms()
    print("content pages:", len(PAGES) - 2 - len(real_pages()) - len(ARTICLES) - len(CALCULATORS) - len(CATEGORIES))
    total_dir = len(SPECIALTIES) + len(CITIES) + len(NICHES) + len(ASSET_TYPES) + len(real_combos())
    print("built /for-advisors/ (+ /advisors.html redirect) + %d directory pages (%d specialty + %d city + %d niche + %d asset-type + %d combo, %d indexed / rest noindex) + %d insights articles + %d calculators + refreshed index.html regions + robots.txt + sitemap.xml + llms.txt + llms-full.txt"
          % (total_dir, len(SPECIALTIES), len(CITIES), len(NICHES), len(ASSET_TYPES), len(real_combos()), len(real_pages()), len(ARTICLES), len(CALCULATORS)))
