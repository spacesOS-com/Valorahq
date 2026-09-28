# -*- coding: utf-8 -*-
"""/traction-concept/ — a UI concept preview for a curated public "traction"
section (a handful of chosen stats, not a live/raw traffic-and-outreach
dashboard).

Static prototype only: every number below is a clearly-labeled placeholder,
not real data — this site has no real traffic/outreach figures to publish
yet, and won't invent any. Exists to make the design concrete enough to
evaluate: once there are real numbers worth sharing, swap the placeholders
for real ones and un-noindex it.
"""
from partials import page, head, BRAND, contact_section

STATS = [
    ("[XX]", "Advisors vetted"),
    ("[XX]", "Client requests reviewed"),
    ("[X]", "Cities with an active advisor"),
    ("[XX]%", "Requests matched to an advisor"),
]


def _stat_tile(num, label):
    return (f'<div class="stat traction-stat"><span class="stat__num">{num}</span>'
            f'<span class="stat__label">{label}</span></div>')


def _traction_body():
    tiles = "\n".join(_stat_tile(n, l) for n, l in STATS)
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:760px;">
    <p class="eyebrow reveal">Concept preview &mdash; not live data</p>
    <h1 class="display display--lg reveal">A curated traction section,<br><em>not a raw dashboard.</em></h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:56ch;">
      Rather than an always-on, unfiltered traffic/outreach dashboard, this is a concept for a
      small, chosen set of numbers &mdash; updated deliberately, not streamed live. Every figure
      below is a placeholder; nothing here is real data.
    </p>

    <div class="traction-grid reveal" style="margin-top:40px;">
      {tiles}
    </div>

    <div class="dir-note" style="margin-top:32px;">
      Why curated instead of live: raw traffic and outreach numbers are easy for a competitor to
      read, easy to misread out of context this early, and outreach specifics in particular can
      edge into privacy territory. A chosen handful of numbers, updated on purpose, gets the trust
      benefit without those risks &mdash; but only once there are real, good numbers to put here.
    </div>
  </div>
</section>

{contact_section()}
"""


def build_traction_page(write_fn):
    html = page(
        head(f"Traction Section Concept | {BRAND}",
             "A UI concept preview for a curated public traction section — placeholder numbers only, not live data.",
             path="/traction-concept/",
             noindex=True),
        _traction_body(),
    )
    write_fn("/traction-concept/", html)
