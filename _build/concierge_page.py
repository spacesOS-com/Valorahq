# -*- coding: utf-8 -*-
"""/concierge/ — a UI concept preview for a single-entry-point "front door":
one free-text question instead of a page-by-page funnel, that assembles
everything relevant (advisor matches, a calculator, an insight article) on
one screen instead of sending the visitor off to browse separate pages.

This is a static prototype, not a working product: the "conversation" and
the assembled results below are a scripted example, not live AI or real
matching logic. It exists to demonstrate the interaction model before any
decision is made to build the real thing (an actual LLM integration, real
matching logic, and real product/compliance thinking about an AI making
advisor recommendations in a financial-services context). The advisors
shown are real ADVISORS entries and the calculator/insight links are real,
existing pages — only the client's message is a scripted example, framed
the same way the existing "Michael Chen" portal mockup already is.
"""
from html import escape

from partials import page, head, BRAND, contact_section
from advisor_pages import ADVISORS
from calculator_pages import CALCULATORS
from insights_pages import ARTICLES

_CALC_SLUG = "retirement-savings-growth"
_ARTICLE_SLUG = "realistic-withdrawal-rate-today"

# Illustrative match: the 3 of the 4 real advisors tagged for retirement income
_MATCH_SLUGS = ["james-conole", "kevin-lum", "even-better-retirement"]


def _match_card(a):
    tags = "".join(f"<li>{escape(t)}</li>" for t in a["tags"])
    return f"""<a class="acard reveal" href="/advisors/{a['slug']}/">
        <div class="acard__top">
          <img src="{escape(a['photo'])}" alt="" width="52" height="52" loading="lazy">
          <div><h3>{escape(a['name'])}</h3><p>{escape(a['firm'])}</p></div>
        </div>
        <p class="acard__quote">{escape(a['quote'])}</p>
        <ul class="acard__tags">{tags}</ul>
      </a>"""


def _concierge_body():
    matches = [a for a in ADVISORS if a["slug"] in _MATCH_SLUGS]
    cards = "\n".join(_match_card(a) for a in matches)
    calc = next(c for c in CALCULATORS if c["slug"] == _CALC_SLUG)
    article = next(a for a in ARTICLES if a["slug"] == _ARTICLE_SLUG)
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:760px;">
    <p class="eyebrow reveal">Concept preview &mdash; not a live feature</p>
    <h1 class="display display--lg reveal">One question in.<br><em>Everything relevant, at once.</em></h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:56ch;">
      Today, finding an advisor, a relevant calculator, and relevant reading means visiting three
      separate pages. This concept collapses that into one: describe the situation once, and the
      site assembles what's relevant &mdash; on this screen, not across a click-through funnel.
      Everything below is scripted for this preview, not live.
    </p>

    <div class="concierge-entry reveal" style="margin-top:40px;" aria-hidden="true">
      <label class="concierge-entry__label">What's going on?</label>
      <div class="concierge-entry__field">
        <span>I'm 58, planning to retire in about 7 years, and I want a clear income plan for when I stop working.</span>
        <span class="btn btn--dark concierge-entry__submit">Ask Valora</span>
      </div>
    </div>

    <div class="concierge-mock reveal" style="margin-top:24px;" aria-hidden="true">
      <div class="convert-mock__bar"><span></span><span></span><span></span><em>Valora Concierge &middot; Preview</em></div>
      <div class="concierge-mock__chat">
        <div class="convert-mock__bubble convert-mock__bubble--us">Got it &mdash; retirement income planning, roughly a 7-year runway. Here's what's relevant:</div>
      </div>
    </div>

    <p class="eyebrow reveal" style="margin-top:36px;">Advisors who focus on this</p>
    <div class="match__grid reveal" style="margin-top:16px;">
      {cards}
    </div>

    <p class="eyebrow reveal" style="margin-top:36px;">A calculator that fits</p>
    <a class="concierge-inline-card reveal" href="/calculators/{calc['slug']}/" style="margin-top:16px;">
      <h4>{escape(calc['title'])}</h4>
      <p>{escape(calc['summary'])}</p>
    </a>

    <p class="eyebrow reveal" style="margin-top:36px;">Worth reading</p>
    <a class="concierge-inline-card reveal" href="/insights/{article['slug']}/" style="margin-top:16px;">
      <h4>{escape(article['title'])}</h4>
      <p>{escape(article['summary'])}</p>
    </a>

    <div class="dir-note" style="margin-top:36px;">
      This is a design concept, not a working product. The entry field, the chat response, and the
      act of assembling these specific results are all scripted for this one example &mdash; a real
      version needs an actual conversational AI integration and real matching logic across
      advisors, calculators, and articles, not something this preview does today.
    </div>
  </div>
</section>

{contact_section()}
"""


def build_concierge_page(write_fn):
    html = page(
        head(f"AI Concierge Concept | {BRAND}",
             "A UI concept preview for an AI chat concierge that recommends advisors based on a natural conversation.",
             path="/concierge/",
             noindex=True),
        _concierge_body(),
    )
    write_fn("/concierge/", html)
