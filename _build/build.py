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
                       faq_schema, client_faq_section, CLIENT_FAQ, SCRIPT_VER, lead_script_includes)
from advisors_page import for_advisors_body, FOR_ADVISORS_FAQ
from advisor_pages import ADVISORS
from directory_pages import build_directory_pages, build_cities_index, build_specialties_index, build_professions_index, build_asset_types_index, SPECIALTIES, CITIES, NICHES, ASSET_TYPES, real_pages, real_combos
from niche_guide_pages import build_niche_guide_pages, build_niche_indexes, niche_pages, index_pages as niche_index_pages
from us_directory_pages import build_us_directory, real_pages as us_real_pages, all_states as us_all_states
from insights_pages import build_insights_pages, ARTICLES
from calculator_pages import build_calculator_pages, CALCULATORS, CATEGORIES
from content_pages import build_content_pages
from intake_page import build_intake_page
from concierge_page import build_concierge_page
from conversation_assets import prepare_conversation_surfaces
from developers_page import build_developers_page
from navigation_placeholders import build_navigation_placeholders
from business_owner_page import build_business_owner_page, BUSINESS_OWNER_INDEXABLE, BUSINESS_OWNER_PATH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = "https://www.valorahq.com"

# Mira pre-flip ruling (2026-09-30, via Sam): the 56 directory roster URLs
# (/top-financial-advisors/*, /find-a-financial-advisor/*, /cities/,
# /specialties/, /professions/, /asset-types/) were HELD pending the founder's
# directory decision + counsel. Founder confirmed counsel sign-off (2026-10-02)
# and directed the flip. DIRECTORY_ENABLED=True restores them to the build,
# sitemap.xml, llms.txt and llms-full.txt.
DIRECTORY_ENABLED = True

# Every live page, one line each. Add a page here when it goes live and the
# sitemap, llms.txt and llms-full.txt all pick it up on the next build.
PAGES = [
    # (path, one-line description for llms.txt)
    ("/", "Educational financial-planning content and an inquiry route; no advisor matches or introductions currently."),
    ("/for-advisors/", "For advisors — information for independent advisors interested in Valora; no live advisor directory or matching at this time."),
    ("/find-your-advisor/", "Tell us what you need: four-question intake; each request is reviewed by hand."),
    ("/guides/", "Financial advice guides for tech employees, physicians and business owners."),
    ("/calculators/", "Browse financial calculators by topic."),
] + ([
    ("/cities/", "Browse financial advisors by city."),
    ("/specialties/", "Browse financial advisors by specialty."),
    ("/professions/", "Browse financial advisors by profession."),
    ("/asset-types/", "Browse financial advisors by investable-asset range."),
    ("/top-financial-advisors/", "Top financial advisors in the U.S., by state and city."),
] + [(f"/top-financial-advisors/{slug}/", f"Top financial advisors in {name}.") for slug, name in us_all_states()
] + [
    (f"/find-a-financial-advisor/{slug}/", desc) for slug, desc in real_pages()
] + [
    (path, desc) for path, desc in us_real_pages()
] + niche_pages() + niche_index_pages() if DIRECTORY_ENABLED else []) + [(f"/insights/{a['slug']}/", a["summary"]) for a in ARTICLES
] + [(f"/calculators/{c['slug']}/", c["summary"]) for c in CALCULATORS if not c.get("noindex")
] + [(f"/calculators/{cat.lower().replace(' ', '-')}/", f"{cat} calculators on Valora.") for cat in CATEGORIES]


def write(path, html):
    out = os.path.join(ROOT, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(ROOT, path.strip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)


def build_for_advisors():
    html = page(head("For Advisors | Valora - Educational Resources",
                     "Read educational articles for advisory firms and ask about Valora's current work. Valora is not arranging advisor introductions at this time.",
                     path="/for-advisors/", schema=faq_schema(FOR_ADVISORS_FAQ),
                     social_image="/assets/for-advisors-education-social.png",
                     social_image_alt="Valora educational resources for advisory firms. No advisor matches or introductions at this time."),
                     for_advisors_body(), active="advisors")
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
                     "Valora publishes educational information about financial planning and accepts questions. "
                     "We aren't arranging advisor matches or introductions at this time.",
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
    # Remove generated dependency tags before reinserting the shared ordered block.
    html = re.sub(r'<script src="/assets/(?:vendor/(?:libphonenumber-max-[^"/]+|disposable-email-domains-[^"/]+)\.js|contact-validation\.js)(?:\?v=[a-f0-9]+)?"></script>\s*', '', html)
    html = re.sub(r'<script src="/(?:assets/)?script\.js(?:\?v=[a-f0-9]+)?"></script>',
                  lambda _m: lead_script_includes(), html)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)


def build_directory_placeholders():
    """Visible section markers only; no advisor records or directory generators."""
    for slug, title in [("cities", "Cities"), ("specialties", "Specialties"),
                        ("professions", "Professions"), ("asset-types", "Asset Types")]:
        body = f'<section class="container" style="padding-block:96px 64px;min-height:45vh"><p class="eyebrow">Being prepared</p><h1>{title}</h1><p>This section is being prepared. Advisor listings are not available here yet.</p><p><a href="/guides/">Read financial planning guides</a> or <a href="/calculators/">explore calculators</a>.</p></section>'
        write(f"/{slug}/", page(head(f"{title} - Being prepared | Valora",
              "This section is being prepared. Advisor listings are not available here yet.",
              path=f"/{slug}/", noindex=True), body))


def refresh_guides_footer():
    """The static guides index uses the same current footer as built pages."""
    p = os.path.join(ROOT, "guides", "index.html")
    with open(p, encoding="utf-8") as f:
        html = f.read()
    html, header_count = re.subn(r"<header\b[^>]*>.*?</header>", lambda _m: header("guides").split("</header>", 1)[0] + "</header>", html, count=1, flags=re.S)
    if header_count != 1:
        raise SystemExit("guides/index.html is missing its header")
    html, count = re.subn(r"<footer\b[^>]*>.*?</footer>", lambda _m: footer().split("</footer>", 1)[0] + "</footer>", html,
                         count=1, flags=re.S)
    if count != 1:
        raise SystemExit("guides/index.html is missing its footer")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)


def refresh_guides_gate():
    """Refresh the static guides inquiry dialog and its validation dependencies."""
    p = os.path.join(ROOT, "guides", "index.html")
    with open(p, encoding="utf-8") as f:
        html = f.read()
    current_gate = gate().replace("Tell us what you need", "Ask Valora a question").replace(
        "Tell us a little about your situation. We’ll review your request and email next steps. We aren’t arranging advisor matches or introductions at this time.",
        "Tell us what you're trying to figure out. We'll review your request and email next steps. We are not arranging advisor matches or introductions at this time.")
    # Put the reviewed disclosure before navigation on every collecting step.
    fine = re.search(r'<p class="gate__fine">.*?</p>', current_gate, flags=re.S)
    if not fine:
        raise SystemExit("shared gate is missing the reviewed disclosure")
    current_gate = current_gate.replace(fine.group(0), "")
    current_gate = current_gate.replace('<div class="gate__foot">', fine.group(0) + '\n          <div class="gate__foot">')
    html, count = re.subn(r'<div class="gate" id="gate" hidden>.*?(?=<script src="/assets/)',
                         lambda _m: current_gate + "\n", html, count=1, flags=re.S)
    if count != 1:
        raise SystemExit("guides/index.html is missing its inquiry gate")
    html = re.sub(r'<script src="/assets/(?:vendor/(?:libphonenumber-max-[^"/]+|disposable-email-domains-[^"/]+)\.js|contact-validation\.js)(?:\?v=[a-f0-9]+)?"></script>\s*', '', html)
    html, count = re.subn(r'<script src="/assets/script\.js(?:\?v=[a-f0-9]+)?"></script>',
                         lambda _m: lead_script_includes(), html, count=1)
    if count != 1:
        raise SystemExit("guides/index.html is missing its shared script include")
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
    sitemap_pages = list(PAGES)
    if BUSINESS_OWNER_INDEXABLE:
        sitemap_pages.append((BUSINESS_OWNER_PATH, "Educational guide to choosing financial help for business owners."))
    urls = "\n".join(
        f"""  <url>
    <loc>{xml_escape(SITE_URL + path)}</loc>
    <lastmod>{today}</lastmod>
  </url>""" for path, _ in sitemap_pages
    )
    write("/sitemap.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
""")


def build_llms():
    lines = "\n".join(f"- [{SITE_URL}{path}]({SITE_URL}{path}): {desc}" for path, desc in PAGES)
    write("/llms.txt", f"""# {BRAND}

> Valora publishes educational information about financial planning and accepts
> questions. We are not arranging advisor matches or introductions at this time.
> Valora does not provide investment advice.

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
    if DIRECTORY_ENABLED:
        build_directory_pages(write)
        build_cities_index(write)
        build_specialties_index(write)
        build_professions_index(write)
        build_asset_types_index(write)
        build_us_directory(write)
        build_niche_guide_pages(write)
        build_niche_indexes(write)
    else:
        build_directory_placeholders()
        PAGES[:] = [p for p in PAGES if p[0] not in {"/cities/", "/specialties/", "/professions/", "/asset-types/"}]
    build_insights_pages(write)
    build_calculator_pages(write)
    _content_pages = build_content_pages(write)
    PAGES.extend(_content_pages)
    build_intake_page(write)
    build_concierge_page(write)
    build_developers_page(write)
    build_business_owner_page(write)
    build_navigation_placeholders(write, ROOT)
    refresh_guides_footer()
    refresh_guides_gate()
    refresh_index()
    build_robots()
    build_sitemap()
    build_llms()
    prepare_conversation_surfaces(ROOT)
    print("content pages:", len(_content_pages))
    total_dir = len(SPECIALTIES) + len(CITIES) + len(NICHES) + len(ASSET_TYPES) + len(real_combos())
    if not DIRECTORY_ENABLED:
        print("directory roster pages EXCLUDED from build (Mira pre-flip HOLD, DIRECTORY_ENABLED=False); skipped %d configured directory pages" % total_dir)
    # Honest robots accounting: count generated directory pages that LACK a
    # noindex meta (previously mislabeled "%d indexed / rest noindex" while
    # 25 roster pages shipped indexable). Directory generators live under
    # these roots only.
    dir_roots = ["top-financial-advisors", "find-a-financial-advisor", "cities",
                 "specialties", "professions", "asset-types"]
    noindex_missing = 0
    dir_html = 0
    for dr in dir_roots:
        for _r, _d, files in os.walk(os.path.join(ROOT, dr)):
            for fn in files:
                if fn.endswith(".html"):
                    dir_html += 1
                    with open(os.path.join(_r, fn), encoding="utf-8") as fh:
                        if "noindex" not in fh.read():
                            noindex_missing += 1
    if DIRECTORY_ENABLED:
        print("built /for-advisors/ (+ /advisors.html redirect) + %d directory pages (%d specialty + %d city + %d niche + %d asset-type + %d combo, %d without noindex of %d html) + %d insights articles + %d calculators + refreshed index.html regions + robots.txt + sitemap.xml + llms.txt + llms-full.txt"
              % (total_dir, len(SPECIALTIES), len(CITIES), len(NICHES), len(ASSET_TYPES), len(real_combos()), noindex_missing, dir_html, len(ARTICLES), len(CALCULATORS)))
    else:
        print("built /for-advisors/ (+ /advisors.html redirect) + %d insights articles + %d calculators + refreshed index.html regions + robots.txt + sitemap.xml + llms.txt + llms-full.txt"
              % (len(ARTICLES), len(CALCULATORS)))
