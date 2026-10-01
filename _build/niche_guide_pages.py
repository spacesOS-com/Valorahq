# -*- coding: utf-8 -*-
"""Educational guide pages generated from the niches research pack
(_build/content-packs/niches.json, sourced from the team's "Advisor AI
Prompt Tracking - Niches" research).

These are NOT advisor-directory pages. ADVISORS is still empty — unlike
directory_pages.py's listings, nothing here claims a browsable roster of
profiles. Each page answers the real researched search phrasings honestly:
who this is for, what tends to be different about their situation, and
what to ask an advisor about it — then the standard "send us a question"
CTA. Content is template-generated from the research columns already
gathered (who/pain-points/search phrasings), not invented per-row facts.
"""
import json
import os
import re
from collections import defaultdict
from html import escape

from partials import page, head, BRAND, contact_section, faq_schema, faq_block

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, "_build", "data", "niches.json"), encoding="utf-8") as f:
    NICHES_DATA = json.load(f)

TOP_LABELS = {
    "profession": "Profession",
    "life-situation": "Life situation",
    "immigration-status": "Immigration status",
    "union-trade": "Union trade",
    "asset-type": "Investment type",
    "employer": "Employer",
}

INDEXES = [
    ("life-situation", "/life-events/", "Find financial guidance by life event",
     "Browse educational guidance organized by the life event you're navigating."),
    ("immigration-status", "/immigration/", "Financial guidance by immigration status",
     "Browse educational guidance for visa holders, green card holders and returning expats."),
    ("union-trade", "/union-trades/", "Financial guidance for union trades",
     "Browse educational guidance organized by union and trade."),
    ("employer", "/employers/", "Financial guidance by employer",
     "Browse educational guidance organized by employer type."),
    ("asset-type", "/investment-types/", "Financial guidance by investment type",
     "Browse educational guidance organized by what you hold."),
]


def _question(phrase):
    low = phrase.lower().rstrip("?")
    if low.startswith(("is ", "are ", "can ", "should ", "does ", "do ", "what ", "how ", "when ", "where ", "why ")):
        return phrase[0].upper() + phrase[1:].rstrip("?") + "?"
    if re.match(r"(financial advisor|advisor|financial planner|planner)\b", low):
        return f"How do I find a {phrase}?"
    return f"What should I know about {phrase}?"


def _answer(row, phrase):
    points = row["pain_points"]
    lead = (points[0] if points else row["who"]).rstrip(".")
    extra = f" Other things worth raising: {', '.join(p.rstrip('.') for p in points[1:4])}." if len(points) > 1 else ""
    return (f"Look for someone with direct, specific experience with {row['name'].lower()} — "
            f"ask how they've actually handled {lead.lower()} for other clients, not just whether "
            f"they're generally familiar with it.{extra} Valora doesn't match you with an advisor "
            f"directly; send us your situation and we'll follow up by email with what to ask.")


def _faq_for(row):
    return [(_question(p), _answer(row, p)) for p in row["phrasings"][:4]]


def _body(row):
    points = "".join(f"<li>{escape(p)}</li>" for p in row["pain_points"])
    faq = _faq_for(row)
    faq_html = faq_block(faq, heading="Common questions") if faq else ""
    eyebrow = escape(TOP_LABELS[row["top"]])
    if row["group"]:
        eyebrow += f" &middot; {escape(row['group'])}"
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:860px;">
    <div class="niche-hero">
      <div class="niche-hero__copy">
        <p class="eyebrow reveal">{eyebrow}</p>
        <h1 class="display display--lg reveal">Financial guidance for {escape(row['name'].lower())}</h1>
        <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:62ch;">{escape(row['who'])}</p>
      </div>
      <div class="niche-hero__image reveal reveal--right" role="img" aria-label="Image placeholder for {escape(row['name'])}">
        <span>Image placeholder</span>
      </div>
    </div>

    {f'<div class="niche-points reveal" style="margin-top:48px;"><h2>What tends to be different</h2><ul>{points}</ul></div>' if points else ''}

    {f'<div style="margin-top:48px;">{faq_html}</div>' if faq_html else ''}
  </div>
</section>
{contact_section(title=f"Have a question about {row['name'].lower()}?" if row["top"] == "life-situation" else f"Have a question about your situation as {row['name'].lower()}?")}
"""


def niche_pages():
    """(path, description) for every generated guide — used by build.py for
    the sitemap/llms.txt, kept in sync automatically since it's the same
    NICHES_DATA the pages are built from."""
    return [(f"/find-a-financial-advisor/{r['slug']}/", f"{r['who']} Educational guidance for {r['name'].lower()}.")
            for r in NICHES_DATA]


def index_pages():
    return [(path, intro) for _, path, _, intro in INDEXES] + [
        ("/occupations/", "Browse financial guidance organized by occupation.")]


def build_niche_guide_pages(write_fn):
    for row in NICHES_DATA:
        meta_desc = f"{row['who']} Educational guidance for {row['name'].lower()} — not personalized advice."
        schema = faq_schema(_faq_for(row)) if row["phrasings"] else ""
        html = page(
            head(f"Financial Guidance for {row['name']} | {BRAND}",
                 meta_desc[:300],
                 path=f"/find-a-financial-advisor/{row['slug']}/",
                 schema=schema),
            _body(row),
        )
        write_fn(f"/find-a-financial-advisor/{row['slug']}/", html)


def _index_page(write_fn, path, title, intro, groups):
    sections = []
    for group_name, items in groups:
        lis = "".join(f'<li><a href="/find-a-financial-advisor/{slug}/">{escape(name)}</a></li>' for slug, name in items)
        heading = f'<h2>{escape(group_name)}</h2>' if group_name else ""
        sections.append(f'{heading}<ul class="niche-index__list">{lis}</ul>')
    body = f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:900px;">
    <p class="eyebrow reveal">Guides</p>
    <h1 class="display display--lg reveal">{escape(title)}</h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:62ch;">{escape(intro)}</p>
    <div style="margin-top:40px;">{''.join(sections)}</div>
  </div>
</section>
{contact_section()}
"""
    write_fn(path, page(head(f"{title} | {BRAND}", intro, path=path), body))


def build_niche_indexes(write_fn):
    by_top = defaultdict(list)
    for row in NICHES_DATA:
        by_top[row["top"]].append(row)

    groups = defaultdict(list)
    for row in by_top["profession"]:
        groups[row["group"]].append((row["slug"], row["name"]))
    _index_page(write_fn, "/occupations/", "Find financial guidance by profession",
                "Browse educational guidance organized by occupation.", sorted(groups.items()))

    for top, path, title, intro in INDEXES:
        items = [(r["slug"], r["name"]) for r in by_top[top]]
        _index_page(write_fn, path, title, intro, [("", items)])
