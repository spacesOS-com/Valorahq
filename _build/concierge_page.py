# -*- coding: utf-8 -*-
"""Public, noindex concierge entry page. Answers and resource IDs come from the
server after its catalog and safety gates; the browser never makes matches."""
from partials import page, head, BRAND


def build_concierge_page(write_fn):
    body = """
<section class="section section--paper" id="top">
  <div class="container concierge-home">
    <p class="eyebrow">Valora concierge preview</p>
    <h1 class="display display--lg">Ask Valora is not available yet.</h1>
    <p>We are preparing an AI guide for general financial education and to help visitors find relevant Valora pages. It is not live here. It will not give personal financial, tax, or legal advice or book appointments.</p>
    <p>For help finding an advisor now, <a href="/find-your-advisor/">send us a request</a>. A person reviews each request before any introduction.</p>
    <div id="concierge-results" class="concierge-results" aria-live="polite"></div>
  </div>
</section>
"""
    write_fn('/concierge/', page(
        head(f"Ask Valora | {BRAND}",
             "Ask a question and explore financial advisors, calculators and articles on Valora.",
             path='/concierge/', noindex=True),
        body,
    ))
