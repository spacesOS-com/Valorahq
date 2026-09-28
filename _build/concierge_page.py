# -*- coding: utf-8 -*-
"""/concierge/ — a UI concept preview for an AI chat concierge that would
understand someone's situation conversationally and recommend 1-3 advisors,
instead of the current multi-step form.

This is a static prototype, not a working chatbot: the "conversation" below
is a scripted example, not live AI. It exists to demonstrate the interaction
model before any decision is made to build a real conversational backend
(which would need an actual LLM integration, real matching logic, and real
product/compliance thinking about an AI making advisor recommendations in a
financial-services context). The advisors shown are real ADVISORS entries,
not invented people — only the client message is a scripted example, framed
the same way the existing "Michael Chen" portal mockup already is.
"""
from html import escape

from partials import page, head, BRAND, contact_section
from advisor_pages import ADVISORS

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
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:760px;">
    <p class="eyebrow reveal">Concept preview &mdash; not a live feature</p>
    <h1 class="display display--lg reveal">What an AI concierge<br><em>could look like.</em></h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:56ch;">
      Instead of a multi-step form, a chat concierge could ask a few natural questions, understand
      the situation, and recommend a short list of advisors directly. This page is a static
      prototype of that interaction &mdash; the conversation below is scripted, not a working AI.
    </p>

    <div class="concierge-mock reveal" style="margin-top:40px;" aria-hidden="true">
      <div class="convert-mock__bar"><span></span><span></span><span></span><em>Valora Concierge &middot; Preview</em></div>
      <div class="concierge-mock__chat">
        <div class="convert-mock__bubble convert-mock__bubble--us">Hi &mdash; tell me a bit about what you're looking for, and I'll match you with a few advisors.</div>
        <div class="convert-mock__bubble convert-mock__bubble--them">I'm 58, planning to retire in about 7 years, and I want a clear income plan for when I stop working.</div>
        <div class="convert-mock__bubble convert-mock__bubble--us">Got it &mdash; retirement income planning, roughly a 7-year runway. Based on that, here are advisors who focus on exactly this:</div>
      </div>
    </div>

    <div class="match__grid" style="margin-top:32px;">
      {cards}
    </div>

    <div class="dir-note" style="margin-top:32px;">
      This is a design concept, not a working chatbot. Building the real version would mean an
      actual conversational AI integration and real matching logic &mdash; a separate build, not
      something this preview does today.
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
