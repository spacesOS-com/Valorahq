# -*- coding: utf-8 -*-
"""Per-advisor profile pages at /advisors/[slug]/.

ADVISORS holds only facts already published on the homepage advisor cards
(name, firm, quote, specialty tags, photo) — nothing new is invented here,
this just gives each of the 4 confirmed advisor-partners their own URL.
"""
from html import escape

from partials import page, head, BRAND, SITE_URL, contact_section, advisor_schema

ADVISORS = [
    {
        "slug": "james-conole",
        "name": "James Conole, CFP®",
        "firm": "Founder · Root Financial",
        "city": "Austin, TX",
        "photo": "/images/advisors/advisor-1.jpg",
        "quote": "Works with people who are within about ten years of retirement and want a clear plan for getting there.",
        "tags": ["Pre-retirement", "Retirement planning"],
    },
    {
        "slug": "kevin-lum",
        "name": "Kevin Lum, CFP®",
        "firm": "Foundry Financial",
        "city": "Los Angeles, CA",
        "photo": "/images/advisors/advisor-2.jpg",
        "quote": "Host of Retirement Made Simple, focused on making retirement decisions clear and straightforward.",
        "tags": ["Retirement planning", "Retirement income"],
    },
    {
        "slug": "eric-peakfp",
        "name": "Eric, CFP®",
        "firm": "The PeakFP",
        "city": "Woodland Hills, CA",
        "photo": "/images/advisors/advisor-3.jpg",
        "quote": "A CERTIFIED FINANCIAL PLANNER™ professional specializing in retirement income planning.",
        "tags": ["Retirement income", "Withdrawal strategy"],
    },
    {
        "slug": "even-better-retirement",
        "name": "Even Better Retirement",
        "firm": "Retirement planning",
        "city": "Bismarck, ND",
        "photo": "/images/advisors/advisor-4.jpg",
        "quote": "“You saved money for a lifetime, now it’s time to have fun.”",
        "tags": ["Retirement lifestyle", "Spending plans"],
    },
]


def _advisor_body(a):
    tags = "".join(f"<li>{escape(t)}</li>" for t in a["tags"])
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:760px;">
    <a href="/#advisors" class="btn btn--outline" style="margin-bottom:32px;">&larr; All advisors</a>
    <div style="display:flex; gap:24px; align-items:center; flex-wrap:wrap;">
      <img src="{escape(a['photo'])}" alt="{escape(a['name'])}" width="96" height="96" style="border-radius:50%; object-fit:cover; width:96px; height:96px;">
      <div>
        <h1 class="display display--lg">{escape(a['name'])}</h1>
        <p style="color:var(--muted); margin-top:6px;">{escape(a['firm'])} &middot; {escape(a['city'])}</p>
      </div>
    </div>
    <blockquote style="font-family:var(--serif); font-size:1.3rem; line-height:1.5; margin:32px 0; max-width:56ch;">&ldquo;{a['quote'].strip('“”')}&rdquo;</blockquote>
    <p class="eyebrow" style="margin-bottom:10px;">Specialties</p>
    <ul class="acard__tags">{tags}</ul>
    <p style="margin-top:28px; color:var(--ink-soft); max-width:56ch;">Interested in speaking with {escape(a['name'].split(',')[0])}? Answer a few questions below and Valora will pass along your details — the advisor decides whether to follow up.</p>
  </div>
</section>

{contact_section(title=f"Explore working with<br><em>{escape(a['name'].split(',')[0])}</em>.")}
"""


def build_advisor_pages(write_fn):
    """write_fn: build.py's write() helper, so paths land at /advisors/<slug>/index.html."""
    for a in ADVISORS:
        schema = advisor_schema(
            name=a["name"],
            job_title=a["firm"],
            url=f"{SITE_URL}/advisors/{a['slug']}/",
            image=f"{SITE_URL}{a['photo']}",
            description=a["quote"],
            area_served=a["city"],
        )
        html = page(
            head(f"{a['name']} | {BRAND}",
                 f"{a['name']}, {a['firm']} in {a['city']}. Specialties: {', '.join(a['tags'])}.",
                 path=f"/advisors/{a['slug']}/",
                 schema=schema),
            _advisor_body(a),
            with_gate=True,
        )
        write_fn(f"/advisors/{a['slug']}/", html)
