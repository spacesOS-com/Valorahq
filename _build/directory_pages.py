# -*- coding: utf-8 -*-
"""/find-a-financial-advisor/[...] pages: specialty, city, niche, asset type,
and a small number of real city+specialty combos.

Every page lists real advisors from advisor_pages.ADVISORS — no invented
people, ever. Where a page's tag/city doesn't genuinely match any advisor,
it falls back to showing the full roster with an honest note: these are
general profiles, not a verified location or specialty match. That page
is still marked noindex (see partials.head): it stays live and useful for
a visitor who lands on it, but isn't presented to search engines as if it
were a genuine local/specialty match. Only pages with a real match are
indexed and listed in the sitemap (see build.py's PAGES / real_pages()).

Combo pages (city + specialty together) are built only where a real advisor
actually matches both — not the full city x specialty cross-product, which
at this site's current size would mean dozens of near-identical empty
pages, exactly the kind of thin/duplicate content that hurts SEO instead of
helping it.
"""
from html import escape

from partials import (page, head, BRAND, contact_section, floating_cta,
                       DIRECTORY_SPECIALTIES as SPECIALTIES, DIRECTORY_CITIES as CITIES,
                       DIRECTORY_NICHES as NICHES, DIRECTORY_ASSET_TYPES as ASSET_TYPES)
from advisor_pages import ADVISORS
from directory_faqs import DIRECTORY_FAQS
from directory_profession_guides import PROFESSION_GUIDES
from directory_specialty_guides import SPECIALTY_GUIDES
from directory_held_guides import HELD_GUIDES
from partials import faq_schema, faq_block


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
    "business-owner": "Investing",
    "executive-professional": "Equity Compensation",
    "entrepreneur-founder": "Equity Compensation",
    "recently-sold-a-business": "Investing",
    "recently-received-an-inheritance": "Investing",
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


def _listing_body(eyebrow, title, intro, advisors, empty_note, calc_categories=None, faq=None, guide=""):
    faq_section = ""
    if faq:
        faq_section = (
            '<section class="section section--paper" id="faq">\n'
            '  <div class="container" style="max-width:900px;">\n'
            + faq_block(faq) + '\n'
            '  </div>\n</section>'
        )
    if advisors:
        shown = advisors
        note = ""
    else:
        shown = ADVISORS
        note = f'<p class="dir-note">{escape(empty_note)}</p>'
    cards = "\n".join(_advisor_card(a) for a in shown)
    grid = f'{note}<div class="match__grid">{cards}</div>'
    if guide:
        guide_section = f'''
<section class="section section--paper dir-guide" id="guide" style="padding-top:64px">
  <div class="container" style="max-width:900px;">
    <div class="dir-guide__prose" style="font-size:1.06rem; line-height:1.75; max-width:74ch;">{guide}</div>
  </div>
</section>
<section class="section section--paper" id="advisor-profiles">
  <div class="container" style="max-width:900px;">
    <h2>Review advisor profiles</h2>
    <div style="margin-top:24px;">{grid}</div>
    {_calc_cross_link(calc_categories)}
  </div>
</section>
'''
        first_section = f'<p style="margin-top:24px;"><a class="btn btn--dark" href="#guide">Read the planning guide</a> <a class="btn btn--outline" href="#advisor-profiles">Review advisor profiles</a></p>'
    else:
        guide_section = ""
        first_section = f'<div style="margin-top:40px;">{grid}</div>{_calc_cross_link(calc_categories)}'
    return f'''
<section class="section section--paper" id="top">
  <div class="container" style="max-width:900px;">
    <p class="eyebrow reveal">{escape(eyebrow)}</p>
    <h1 class="display display--lg reveal">{title}</h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:56ch;">{escape(intro)}</p>
    {first_section}
  </div>
</section>
{guide_section}
{faq_section}
{contact_section()}
'''

def _specialty_matches(needles):
    return [a for a in ADVISORS if any(n in t.lower() for t in a["tags"] for n in needles)]


def _write_listing(write_fn, slug, meta_title, meta_desc, eyebrow, title, intro, matches, empty_note, calc_categories=None, faq=None):
    html = page(
        head(meta_title, meta_desc, path=f"/find-a-financial-advisor/{slug}/", noindex=(slug in {n[0] for n in NICHES} or not matches),
             schema=faq_schema(faq) if faq else ""),
        _listing_body(eyebrow, title, intro, matches, empty_note, calc_categories, faq=faq, guide=PROFESSION_GUIDES.get(slug, SPECIALTY_GUIDES.get(slug, HELD_GUIDES.get(slug, "")))) + floating_cta(slug),
        with_gate=True,
        body_class="page-sub has-cta-float",
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
            out.append((slug, f"Explore {label.lower()} questions and topic-tagged advisor profiles on Valora; tags do not verify expertise."))
    for slug, city in CITIES:
        if [a for a in ADVISORS if a["city"] == city]:
            out.append((slug, f"Financial advisors in {city} on Valora."))
    # Niches remain excluded from the sitemap even if a future fallback roster
    # is populated. A roster card alone does not establish niche-specific fit.
    # Asset types have no tagged matches today either.
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
                        f"{label} - questions to ask an advisor | {BRAND}",
                        (f"Explore {label.lower()} and compare advisor questions. "
                         f"No advisor is currently tagged for this topic." if not matches else
                         f"Explore {label.lower()} and questions to ask an advisor. "
                         f"A topic tag does not verify expertise or fiduciary status."),
                        "Specialty", f"{label}: questions for an advisor",
                        (f"Learn what to ask about {label.lower()} and review general advisor profiles. "
                         f"No advisor is currently tagged for this topic." if not matches else
                         f"Learn what to ask about {label.lower()} and review topic-tagged advisor profiles. "
                         f"Verify each advisor's experience, registration, fees and fit."),
                        matches,
                        f"We don't have a {label.lower()} specialist tagged here yet. The profiles below "
                        "are a general roster; ask each advisor whether they cover this topic.",
                        calc_categories=[SPECIALTY_TO_CALC[slug]] if slug in SPECIALTY_TO_CALC else None,
                        faq=DIRECTORY_FAQS.get(slug))

    for slug, city in CITIES:
        matches = [a for a in ADVISORS if a["city"] == city]
        _write_listing(write_fn, slug,
                        f"Financial Advisors in {city} | {BRAND}",
                        f"Find independent, fiduciary financial advisors in {city} on Valora.",
                        city, f"Financial advisors in {city}",
                        f"Independent, fiduciary financial advisors based in {city}.",
                        matches,
                        f"We don't have a {city.split(',')[0]}-based advisor listed yet, but the "
                        "profiles below are a general roster; ask each advisor about location and fit.",
                        calc_categories=CALC_CATEGORIES,
                        faq=DIRECTORY_FAQS.get(slug))  # location doesn't imply a topic — show all

    for slug, label in NICHES:
        # no advisor is tagged by client situation today — always the honest empty state, always noindex
        _write_listing(write_fn, slug,
                        f"Advisors for {label} | {BRAND}",
                        f"Explore planning for {label.lower()} clients and questions to ask a financial advisor. No advisor is currently tagged for this situation.",
                        "Niche", f"Advisors for {label.lower()} clients",
                        f"Explore what {label.lower()} clients should ask a financial advisor. The profiles below are a general roster, not verified specialists for this situation.",
                        [],
                        "We don't have an advisor specifically tagged for this yet. The profiles "
                        "below are a general roster; ask each advisor whether they cover your situation.",
                        calc_categories=[NICHE_TO_CALC[slug]] if slug in NICHE_TO_CALC else None,
                        faq=DIRECTORY_FAQS.get(slug))

    for slug, label in ASSET_TYPES:
        # same as niches: real option list, no real matches yet
        _write_listing(write_fn, slug,
                        f"Advisors for {label} in Assets | {BRAND}",
                        f"Independent, fiduciary financial advisors on Valora for households with {label.lower()} in investable assets.",
                        "Asset range", f"Advisors for {label} in investable assets",
                        f"Independent advisors on Valora who work with households in the {label.lower()} range.",
                        [],
                        "We don't have an advisor specifically tagged for this asset range yet, but the "
                        "profiles below are a general roster; ask each advisor about location and fit.")

    for city_slug, city, spec_slug, label in real_combos():
        matches = [a for a in ADVISORS if a["city"] == city]
        combo_slug = f"{city_slug}-{spec_slug}"
        html = page(
            head(f"{label} Advisors in {city} | {BRAND}",
                 f"Independent, fiduciary {label.lower()} advisors on Valora based in {city}.",
                 path=f"/find-a-financial-advisor/{combo_slug}/",
                 schema=faq_schema(DIRECTORY_FAQS[f"{city_slug}-{spec_slug}"]) if f"{city_slug}-{spec_slug}" in DIRECTORY_FAQS else ""),
            _listing_body(f"{city} · {label}", f"{label} advisors in {city}",
                          f"Independent advisors on Valora who specialize in {label.lower()} and are based in {city}.",
                          matches, "",
                          calc_categories=[SPECIALTY_TO_CALC[spec_slug]] if spec_slug in SPECIALTY_TO_CALC else None,
                          faq=DIRECTORY_FAQS.get(f"{city_slug}-{spec_slug}")) + floating_cta(combo_slug),
            with_gate=True,
            body_class="page-sub has-cta-float",
        )
        write_fn(f"/find-a-financial-advisor/{combo_slug}/", html)


def _city_mark(city):
    """A small illustrative skyline mark, not a photo of the real place — we
    don't have a verified, licensed photo for each of 31 cities on hand, and
    a wrong or mismatched stock photo is worse than a simple, honest graphic
    in the site's own brand colors."""
    import hashlib
    seed = int(hashlib.sha1(city.encode()).hexdigest(), 16)
    heights = [24 + (seed >> (i * 4) & 0xF) * 3 for i in range(7)]
    bars = "".join(
        f'<rect x="{i * 16}" y="{64 - h}" width="10" height="{h}" rx="1"/>'
        for i, h in enumerate(heights)
    )
    return f'<svg class="city-card__mark" viewBox="0 0 112 64" aria-hidden="true">{bars}</svg>'


def build_cities_index(write_fn):
    """/cities/ — every city page, each with a small illustrative mark (see
    _city_mark) so the footer can link a handful of cities plus "More
    cities" here instead of listing all ~30 in every page footer."""
    cards = "".join(
        f'<a class="city-card" href="/find-a-financial-advisor/{slug}/">'
        f'{_city_mark(city)}<span>{escape(city)}</span></a>'
        for slug, city in CITIES
    )
    body = f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:1000px;">
    <p class="eyebrow reveal">Directory</p>
    <h1 class="display display--lg reveal">Find a financial advisor by city</h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:60ch;">Browse independent, fiduciary financial advisors on Valora by metro area.</p>
    <div class="city-grid" style="margin-top:40px;">
      {cards}
    </div>
  </div>
</section>

{contact_section()}
"""
    html = page(
        head(f"Financial Advisors by City | {BRAND}",
             "Browse independent, fiduciary financial advisors on Valora by metro area.",
             path="/cities/"),
        body,
    )
    write_fn("/cities/", html)


def _item_placeholder(label):
    """A placeholder mark for a directory item — an abstract category (a
    specialty or profession, not a place), so an initial-letter mark is
    honest here in a way a stock photo wouldn't be (see _city_mark)."""
    initial = label.strip()[:1].upper() or "?"
    return f'<span class="item-card__mark" aria-hidden="true">{escape(initial)}</span>'


def _single_column_index(write_fn, slug, eyebrow_title, items):
    cards = "".join(
        f'<a class="item-card" href="/find-a-financial-advisor/{s}/">{_item_placeholder(l)}<span>{escape(l)}</span></a>'
        for s, l in items
    )
    body = f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:900px;">
    <p class="eyebrow reveal">Directory</p>
    <h1 class="display display--lg reveal">Find a financial advisor by {eyebrow_title.lower()}</h1>
    <div class="item-grid" style="margin-top:40px;">
      {cards}
    </div>
  </div>
</section>

{contact_section()}
"""
    html = page(
        head(f"Financial Advisors by {eyebrow_title} | {BRAND}",
             f"Browse independent, fiduciary financial advisors on Valora by {eyebrow_title.lower()}.",
             path=f"/{slug}/"),
        body,
    )
    write_fn(f"/{slug}/", html)


def build_specialties_index(write_fn):
    """/specialties/ — specialty pages only."""
    _single_column_index(write_fn, "specialties", "Specialty", [(s, l) for s, l, _ in SPECIALTIES])


def build_professions_index(write_fn):
    """/professions/ — profession (niche) pages only."""
    _single_column_index(write_fn, "professions", "Profession", NICHES)


def build_asset_types_index(write_fn):
    """/asset-types/ — asset-range pages only."""
    _single_column_index(write_fn, "asset-types", "Asset Range", ASSET_TYPES)
