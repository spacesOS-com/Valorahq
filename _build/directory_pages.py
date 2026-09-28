# -*- coding: utf-8 -*-
"""/find-a-financial-advisor/[...] pages: specialty, city, niche, asset type,
and a small number of real city+specialty combos.

Every page lists real advisors from advisor_pages.ADVISORS when their tags
or city genuinely match — no invented people. Where nothing matches, the
page shows an honest empty state AND is marked noindex (see partials.head):
it stays live and useful for a visitor who lands on it, but isn't presented
to search engines as if it were a real, populated page. Only pages with a
real match are indexed and listed in the sitemap (see build.py's PAGES).

Combo pages (city + specialty together) are built only where a real advisor
actually matches both — not the full city x specialty cross-product, which
at this site's current size would mean dozens of near-identical empty
pages, exactly the kind of thin/duplicate content that hurts SEO instead of
helping it.
"""
from html import escape

from partials import (page, head, BRAND, contact_section,
                       DIRECTORY_SPECIALTIES as SPECIALTIES, DIRECTORY_CITIES as CITIES,
                       DIRECTORY_NICHES as NICHES, DIRECTORY_ASSET_TYPES as ASSET_TYPES)
from advisor_pages import ADVISORS


def _advisor_card(a):
    tags = "".join(f"<li>{escape(t)}</li>" for t in a["tags"])
    return f"""<a class="acard" href="/advisors/{a['slug']}/">
        <div class="acard__top">
          <img src="{escape(a['photo'])}" alt="" width="52" height="52" loading="lazy">
          <div><h3>{escape(a['name'])}</h3><p>{escape(a['firm'])}</p></div>
        </div>
        <p class="acard__quote">{escape(a['quote'])}</p>
        <ul class="acard__tags">{tags}</ul>
      </a>"""


# Specialties/niches that map to one of calculator_pages.CATEGORIES. Cities and
# asset types don't map to a specific category (location/net worth don't imply
# a topic), so those pages link out to all categories instead — see
# _calc_cross_link below.
SPECIALTY_TO_CALC = {
    "retirement-planning": "Retirement",
    "tax-planning": "Taxes",
    "concentrated-stock": "Equity Compensation",
    "managing-investments": "Investing",
    "cash-liquidity-management": "Banking",
}
NICHE_TO_CALC = {
    "retired": "Retirement",
}


def _calc_cross_link(categories):
    if not categories:
        return ""
    from calculator_pages import _category_slug
    links = "".join(
        f'<a class="btn btn--outline" href="/calculators/{_category_slug(cat)}/" style="margin:4px 8px 4px 0;">{escape(cat)} calculators</a>'
        for cat in categories
    )
    return f"""<div style="margin-top:40px; padding-top:28px; border-top:1px solid var(--line);">
      <p class="eyebrow reveal" style="margin-bottom:14px;">Related tools</p>
      {links}
    </div>"""


def _listing_body(eyebrow, title, intro, advisors, empty_note, calc_categories=None):
    if advisors:
        cards = "\n".join(_advisor_card(a) for a in advisors)
        grid = f'<div class="match__grid">{cards}</div>'
    else:
        grid = f"""<div class="dir-empty">
      <p>{escape(empty_note)}</p>
      <a class="btn btn--dark" href="/#advisors">Explore all advisors</a>
    </div>"""
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:900px;">
    <p class="eyebrow reveal">{escape(eyebrow)}</p>
    <h1 class="display display--lg reveal">{title}</h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:56ch;">{escape(intro)}</p>
    <div style="margin-top:40px;">
      {grid}
    </div>
    {_calc_cross_link(calc_categories)}
  </div>
</section>

{contact_section()}
"""


def _specialty_matches(needles):
    return [a for a in ADVISORS if any(n in t.lower() for t in a["tags"] for n in needles)]


def _write_listing(write_fn, slug, meta_title, meta_desc, eyebrow, title, intro, matches, empty_note, calc_categories=None):
    html = page(
        head(meta_title, meta_desc, path=f"/find-a-financial-advisor/{slug}/", noindex=not matches),
        _listing_body(eyebrow, title, intro, matches, empty_note, calc_categories),
    )
    write_fn(f"/find-a-financial-advisor/{slug}/", html)
    return bool(matches)


def real_pages():
    """Slugs (and one-line descriptions) for pages that actually have a real
    advisor match — the only directory pages build.py should list in the
    sitemap/llms.txt. Computed the same way build_directory_pages() decides
    what to render, so the two can never drift apart."""
    out = []
    for slug, label, needles in SPECIALTIES:
        if _specialty_matches(needles):
            out.append((slug, f"{label} advisors on Valora."))
    for slug, city in CITIES:
        if [a for a in ADVISORS if a["city"] == city]:
            out.append((slug, f"Financial advisors in {city} on Valora."))
    # niches and asset types: no advisor is tagged this way yet, so none are real pages today
    for city_slug, city, spec_slug, label in real_combos():
        out.append((f"{city_slug}-{spec_slug}", f"{label} advisors in {city} on Valora."))
    return out


def real_combos():
    """(city_slug, city, specialty_slug, specialty_label) triples where a real
    advisor matches both — the only city+specialty combos worth a page."""
    combos = []
    for city_slug, city in CITIES:
        in_city = [a for a in ADVISORS if a["city"] == city]
        if not in_city:
            continue
        for spec_slug, label, needles in SPECIALTIES:
            matches = [a for a in in_city if any(n in t.lower() for t in a["tags"] for n in needles)]
            if matches:
                combos.append((city_slug, city, spec_slug, label))
    return combos


def build_directory_pages(write_fn):
    from calculator_pages import CATEGORIES as CALC_CATEGORIES

    for slug, label, needles in SPECIALTIES:
        matches = _specialty_matches(needles)
        _write_listing(write_fn, slug,
                        f"{label} Advisors | {BRAND}",
                        f"Independent, fiduciary financial advisors on Valora who specialize in {label.lower()}.",
                        "Specialty", f"{label} advisors",
                        f"Independent advisors on Valora who specialize in {label.lower()}.",
                        matches,
                        f"We don't have a {label.lower()} specialist listed yet — this page is a "
                        "preview of how specialty pages will look as our advisor network grows.",
                        calc_categories=[SPECIALTY_TO_CALC[slug]] if slug in SPECIALTY_TO_CALC else None)

    for slug, city in CITIES:
        matches = [a for a in ADVISORS if a["city"] == city]
        _write_listing(write_fn, slug,
                        f"Financial Advisors in {city} | {BRAND}",
                        f"Find independent, fiduciary financial advisors in {city} on Valora.",
                        city, f"Financial advisors in {city}",
                        f"Independent, fiduciary financial advisors based in {city}.",
                        matches,
                        f"We don't have a {city.split(',')[0]}-based advisor listed yet — this "
                        "page is a preview of how city pages will look as our advisor network grows.",
                        calc_categories=CALC_CATEGORIES)  # location doesn't imply a topic — show all

    for slug, label in NICHES:
        # no advisor is tagged by client situation today — always the honest empty state, always noindex
        _write_listing(write_fn, slug,
                        f"Advisors for {label} | {BRAND}",
                        f"Independent, fiduciary financial advisors on Valora who work with {label.lower()} clients.",
                        "Niche", f"Advisors for {label.lower()} clients",
                        f"Independent advisors on Valora who work with {label.lower()} clients.",
                        [],
                        "We don't have an advisor tagged for this yet — this page is a preview of how "
                        "niche pages will look as our advisor network grows.",
                        calc_categories=[NICHE_TO_CALC[slug]] if slug in NICHE_TO_CALC else None)

    for slug, label in ASSET_TYPES:
        # same as niches: real option list, no real matches yet
        _write_listing(write_fn, slug,
                        f"Advisors for {label} in Assets | {BRAND}",
                        f"Independent, fiduciary financial advisors on Valora for households with {label.lower()} in investable assets.",
                        "Asset range", f"Advisors for {label} in investable assets",
                        f"Independent advisors on Valora who work with households in the {label.lower()} range.",
                        [],
                        "We don't have an advisor tagged for this asset range yet — this page is a "
                        "preview of how these pages will look as our advisor network grows.")

    for city_slug, city, spec_slug, label in real_combos():
        matches = [a for a in ADVISORS if a["city"] == city]
        combo_slug = f"{city_slug}-{spec_slug}"
        html = page(
            head(f"{label} Advisors in {city} | {BRAND}",
                 f"Independent, fiduciary {label.lower()} advisors on Valora based in {city}.",
                 path=f"/find-a-financial-advisor/{combo_slug}/"),
            _listing_body(f"{city} · {label}", f"{label} advisors in {city}",
                          f"Independent advisors on Valora who specialize in {label.lower()} and are based in {city}.",
                          matches, "",
                          calc_categories=[SPECIALTY_TO_CALC[spec_slug]] if spec_slug in SPECIALTY_TO_CALC else None),
        )
        write_fn(f"/find-a-financial-advisor/{combo_slug}/", html)
