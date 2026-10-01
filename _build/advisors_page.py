"""For Advisors: educational content and inquiry route, no matching offering."""
from html import escape
from blog_feed import latest_posts
FOR_ADVISORS_FAQ = [('Does Valora match advisors with prospective clients?', 'No. Valora publishes educational information and accepts questions. Valora is not arranging advisor matches or introductions at this time.'), ('Does Valora offer exclusive client introductions?', 'No. There is no current client-introduction offering or exclusivity promise. Asking a question does not reserve a prospective client or territory.'), ('Does Valora manage my client relationships or data?', 'This educational page does not establish an advisory agreement, data-ownership terms or a client-management service. Any future service would need its own stated terms. Valora does not provide investment advice.'), ('What can I ask Valora about?', "You can ask about the educational articles or Valora's current work. We review questions and respond by email. An inquiry is not a client introduction, an advisor recommendation or a request to send client records."), ('Does this page offer a paid advisor plan?', "No paid advisor plan, pricing tier or territory is offered on this page. You can ask about Valora's current work without assuming that a proposed service is available.")]

def _faq_accordion():
    return "\n".join(f'<details class="faq__item"><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in FOR_ADVISORS_FAQ)

def _blog_cards():
    return '<div class="adv-blog__grid">'+"\n".join(f'<article class="blogcard reveal"><h3><a href="{escape(p["url"])}" target="_blank" rel="noopener">{escape(p["title"])}</a></h3><p>{escape(p["excerpt"])}</p><a class="blogcard__link" href="{escape(p["url"])}" target="_blank" rel="noopener">Read on the blog →</a></article>' for p in latest_posts(3))+'</div>'

def for_advisors_body():
    return f"""<section class="hero hero--sub" id="top">
  <div class="hero__grid" aria-hidden="true"><span class="hero__cell hero__cell--gold"></span><span class="hero__cell hero__cell--wide"></span><span class="hero__cell hero__cell--ring"></span><span class="hero__cell hero__cell--green"></span></div>
  <div class="container hero__inner"><div class="hero__copy">
    <p class="eyebrow reveal">For advisory firms</p>
    <h1 class="hero__title reveal">Educational resources.<br><em>Clear expectations.</em></h1>
    <p class="adv-hero__sub reveal">Read educational articles for advisory firms and ask about Valora's current work. Valora is not arranging advisor matches or introductions at this time.</p>
    <div class="hero__actions reveal"><a class="btn btn--dark" href="/#contact" data-gate-open>Ask a question</a><a class="btn btn--outline" href="#insights-for-advisors">Read articles</a></div>
  </div></div>
</section>
<section class="section section--paper adv-value" id="introductions"><div class="container">
  <p class="eyebrow reveal">Current scope</p><h2 class="display display--lg reveal">Education and inquiries,<br><em>not a client-acquisition service.</em></h2>
  <p class="reveal">Valora publishes educational information about financial planning and advisory-firm work. You can send a question; we review inquiries and respond by email. We do not offer exclusive leads, qualify prospective clients, match investors with advisors or book introductions.</p>
  <p class="reveal">A question does not create a partnership, reserve a territory or establish an advisory relationship.</p>
</div></section>
<section class="section section--cream" id="portal"><div class="container">
  <p class="eyebrow reveal">Product expectations</p><h2 class="display display--lg reveal">No portal service<br><em>is offered on this page.</em></h2>
  <p class="reveal">This page is not an offer of prospect messaging, follow-up reminders, client notes, calendar integrations or digital onboarding. Any future capabilities would need their own description, availability and terms before you could rely on them.</p>
</div></section>
<section class="section section--paper" id="directory"><div class="container">
  <p class="eyebrow reveal">Directory expectations</p><h2 class="display display--lg reveal">No verified listing<br><em>or visibility promise.</em></h2>
  <p class="reveal">Valora is not offering an approved-advisor directory listing, verification badge, search placement or consultation-booking service here. Educational content is not evidence that a professional has been vetted or is available.</p>
</div></section>
<section class="section section--cream adv-blog" id="insights-for-advisors"><div class="container">
  <div class="adv-blog__head"><p class="eyebrow reveal">From the Valora blog</p><h2 class="display display--lg reveal">Educational articles<br><em>for advisory firms.</em></h2><p class="reveal">Read practical discussions of advisory-firm operations and communication. These articles are educational, not a promise of clients, search rankings or business results.</p></div>
  {_blog_cards()}
  <a class="btn btn--outline adv-blog__more" href="https://blog.valorahq.com/" target="_blank" rel="noopener">View more articles</a>
</div></section>
<section class="section section--paper" id="professional-guidance"><div class="container">
  <p class="eyebrow reveal">Assessing professional help</p><h2 class="display display--lg reveal">Ask about scope,<br><em>fees and conflicts.</em></h2>
  <p class="reveal">When assessing an advisory service, ask what work is included, who is responsible, how fees are charged and what conflicts may exist. Check a professional's registration and disclosures with the relevant regulator. A designation or a registration alone is not a guarantee of fit or results.</p>
  <p class="reveal">This is general educational guidance, not a claim that Valora has screened a network or endorsed an advisor.</p>
</div></section>
<section class="section section--cream adv-faq" id="faq"><div class="container"><h2 class="display display--lg reveal">Frequently asked questions</h2><div class="faq">{_faq_accordion()}</div></div></section>
<section class="section section--green adv-ready"><div class="container"><h2 class="display display--lg reveal">Have a question?</h2><p class="reveal">Ask about the educational content or Valora's current work. We review inquiries and respond by email. Valora is not arranging advisor matches or introductions at this time.</p><a class="btn btn--cream" href="/#contact" data-gate-open>Ask a question</a></div></section>"""
