# -*- coding: utf-8 -*-
"""Gated public AI-guide entry. No scripted advice or advisor profiles."""
from partials import page, head, BRAND


def build_concierge_page(write_fn):
    body = """
<section class="section section--paper" id="top">
  <div class="container concierge-home">
    <p class="eyebrow">Valora AI guide</p>
    <h1 class="display display--lg">Valora is not available to chat yet.</h1>
    <p>We are preparing an AI guide for general topics and guides on this site. It will not give personal financial, tax or legal advice or book appointments.</p>
    <p>For a person to review a question, <a href="/find-your-advisor/">send us a request</a>. We are not arranging advisor matches or introductions at this time.</p>
    <div id="concierge-results" class="concierge-results" aria-live="polite"></div>
  </div>
</section>
"""
    write_fn('/concierge/', page(
        head(f"Ask Valora | {BRAND}", "Valora's AI guide is not available to chat yet. You can send a question for a person to review.", path='/concierge/', noindex=True),
        body,
    ))
