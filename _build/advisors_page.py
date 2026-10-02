"""For Advisors: educational content and inquiry route, no matching offering."""
from html import escape
from blog_feed import latest_posts, BLOG_URL
from root_inquiry import inquiry_host
FOR_ADVISORS_FAQ = [('Does Valora match advisors with prospective clients?', 'No. Valora publishes educational information and accepts questions. Valora is not arranging advisor matches or introductions at this time.'), ('Does Valora offer exclusive client introductions?', 'No. There is no current client-introduction offering or exclusivity promise. Asking a question does not reserve a prospective client or territory.'), ('Does Valora manage my client relationships or data?', 'This educational page does not establish an advisory agreement, data-ownership terms or a client-management service. Any future service would need its own stated terms. Valora does not provide investment advice.'), ('What can I ask Valora about?', "You can ask about the educational articles or Valora's current work. We review questions and respond by email. An inquiry is not a client introduction, an advisor recommendation or a request to send client records."), ('Does this page offer a paid advisor plan?', "No paid advisor plan, pricing tier or territory is offered on this page. You can ask about Valora's current work without assuming that a proposed service is available.")]

def _faq_accordion():
    return "\n".join(f'<details class="faq__item"><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in FOR_ADVISORS_FAQ)

def _thumb(url):
    """Ghost serves resized webp variants; ask for a card-sized one."""
    return url.replace("/content/images/", "/content/images/size/w600/format/webp/", 1)

def _blog_cards():
    cards = []
    for p in latest_posts(6):
        url, title = escape(p["url"]), escape(p["title"])
        img = (f'<a class="advx-post__media" href="{url}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">'
               f'<img src="{escape(_thumb(p["image"]))}" alt="" loading="lazy" decoding="async" width="600" height="338"></a>') if p.get("image") else ''
        date = f'<p class="advx-post__date">{escape(p["date"])}</p>' if p.get("date") else ''
        cards.append(f'<article class="advx-post reveal">{img}<div class="advx-post__body">{date}'
                     f'<h3><a href="{url}" target="_blank" rel="noopener">{title}</a></h3>'
                     f'<p>{escape(p["excerpt"])}</p>'
                     f'<a class="advx-post__link" href="{url}" target="_blank" rel="noopener">Read the article →</a></div></article>')
    return '<div class="advx-posts">' + "\n".join(cards) + '</div>'

_ICON = {
    "book": '<path d="M5 5.5A2.5 2.5 0 0 1 7.5 3H19v15H7.5A2.5 2.5 0 0 0 5 20.5v-15Z"/><path d="M5 20.5A2.5 2.5 0 0 0 7.5 23H19v-5"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m4 7.5 8 6 8-6"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.8 2.8L16 9.8"/>',
}

def _icon(name):
    return f'<span class="advx-icon" aria-hidden="true"><svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{_ICON[name]}</svg></span>'

def for_advisors_body():
    return f"""<section class="advx-hero" id="top"><div class="container advx-hero__grid">
  <div class="advx-hero__copy">
    <p class="eyebrow reveal">For advisory firms</p>
    <h1 class="advx-hero__title reveal">Educational resources. Clear expectations.</h1>
    <p class="advx-hero__sub reveal">Read educational articles for advisory firms and ask about Valora's current work.</p>
    <ul class="advx-ticks reveal">
      <li>Practical articles on advisory-firm operations and communication</li>
      <li>We review inquiries and respond by email</li>
      <li>No paid advisor plan, pricing tier or territory</li>
    </ul>
    <p class="advx-hero__note reveal">Valora is not arranging advisor matches or introductions at this time.</p>
  </div>
  <aside class="hcard hcard--inquiry advx-hero__form" aria-label="Ask Valora a question">{inquiry_host()}</aside>
</div></section>
<section class="section section--paper advx-why" id="introductions"><div class="container">
  <h2 class="advx-h2 reveal">Why Valora?</h2>
  <div class="advx-cards">
    <div class="advx-card reveal">{_icon("book")}<h3>Educational</h3><p>Valora publishes educational information about financial planning and advisory-firm work.</p></div>
    <div class="advx-card reveal">{_icon("mail")}<h3>Direct</h3><p>You can send a question; we review inquiries and respond by email.</p></div>
    <div class="advx-card reveal">{_icon("check")}<h3>Clear</h3><p>No paid advisor plan, pricing tier or territory is offered on this page.</p></div>
  </div>
</div></section>
<section class="section section--cream advx-how" id="how-it-works"><div class="container">
  <h2 class="advx-h2 reveal">How it works</h2>
  <ol class="advx-steps">
    <li class="reveal"><span class="advx-steps__n">01</span><div><h3>Read the articles</h3><p>Read practical discussions of advisory-firm operations and communication.</p></div></li>
    <li class="reveal"><span class="advx-steps__n">02</span><div><h3>Ask a question</h3><p>Ask about the educational content or Valora's current work.</p></div></li>
    <li class="reveal"><span class="advx-steps__n">03</span><div><h3>Get a reply by email</h3><p>We review inquiries and respond by email. A question does not create a partnership, reserve a territory or establish an advisory relationship.</p></div></li>
  </ol>
  <div class="advx-center reveal"><a class="btn btn--dark advx-btn" href="/#contact" data-gate-open>Ask a question</a></div>
</div></section>
<section class="section section--paper advx-blog" id="insights-for-advisors"><div class="container">
  <h2 class="advx-h2 reveal">Educational articles for advisory firms</h2>
  <p class="advx-lead reveal">Read practical discussions of advisory-firm operations and communication. These articles are educational, not a promise of clients, search rankings or business results.</p>
  {_blog_cards()}
  <div class="advx-center reveal"><a class="btn btn--outline advx-btn" href="{BLOG_URL}" target="_blank" rel="noopener">View more articles</a></div>
</div></section>
<section class="section section--cream advx-scope" id="portal"><div class="container">
  <h2 class="advx-h2 reveal">Clear expectations</h2>
  <p class="advx-lead reveal">Education and inquiries, not a client-acquisition service.</p>
  <div class="advx-fit">
    <div class="advx-fit__col advx-fit__col--yes reveal"><h3>What you can do here</h3><ul>
      <li>Read educational information about financial planning and advisory-firm work</li>
      <li>Ask about the educational articles or Valora's current work</li>
      <li>Get a reply by email after we review your inquiry</li>
    </ul></div>
    <div class="advx-fit__col advx-fit__col--no reveal" id="directory"><h3>What is not offered here</h3><ul>
      <li>Exclusive leads, prospect qualification, investor-advisor matching or booked introductions</li>
      <li>Prospect messaging, follow-up reminders, client notes, calendar integrations or digital onboarding</li>
      <li>An approved-advisor directory listing, verification badge, search placement or consultation booking</li>
    </ul></div>
  </div>
  <p class="advx-fine reveal">Any future capabilities would need their own description, availability and terms before you could rely on them. Educational content is not evidence that a professional has been vetted or is available.</p>
</div></section>
<section class="section section--green advx-band"><div class="container">
  <div><h2 class="reveal">Have a question?</h2><p class="reveal">Ask about the educational content or Valora's current work. We review inquiries and respond by email. Valora is not arranging advisor matches or introductions at this time.</p></div>
  <a class="btn btn--cream advx-btn reveal" href="/#contact" data-gate-open>Ask a question</a>
</div></section>
<section class="section section--paper adv-faq advx-faq" id="faq"><div class="container"><h2 class="advx-h2 reveal">Frequently asked questions</h2><div class="faq">{_faq_accordion()}</div></div></section>
<section class="advx-cross"><div class="container"><div><h2>Not an advisory firm?</h2><p>Read Valora's educational guides on financial planning.</p></div><a class="btn btn--outline advx-btn" href="/guides/">Browse the guides</a></div></section>"""
