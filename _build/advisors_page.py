"""For Advisors: landing page. Promise is reaching people who are seeking
the firm's services; AEO, GEO and outbound are the means, not the pitch."""
from html import escape
from blog_feed import latest_posts, BLOG_URL
from root_inquiry import inquiry_host
FOR_ADVISORS_FAQ = [
    ('How does Valora help my firm reach new clients?', 'Valora works to put your firm in front of people who are already looking for the kind of advice you give. We do that in two ways: by making your firm easier to find when people ask AI tools and search engines about financial advice, and by reaching out directly to people who fit the clients you serve.'),
    ('What are AEO and GEO?', 'Answer engine optimization (AEO) and generative engine optimization (GEO) are the work of making a firm\'s expertise easy for AI assistants and AI-powered search to find, read and cite. They are tools we use, alongside outbound outreach, to connect your firm with people seeking its services.'),
    ('Does Valora guarantee new clients?', 'No. Results depend on your firm, your market and your competition, and visibility builds over time. Valora does not guarantee clients, search rankings or AI citations.'),
    ('Who approves what is published or sent for my firm?', 'Your firm does. Advisory firms are responsible for their own advertising and communications, so nothing should go out under your firm\'s name without your review.'),
    ('What does it cost?', 'It depends on the scope of work for your firm. Tell us about your firm and we will reply by email.'),
    ('Is Valora an investment adviser?', 'No. Valora is not a registered investment adviser and does not provide investment advice. Valora provides marketing services to advisory firms.'),
]

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
    <h1 class="advx-hero__title reveal">Connect with people seeking your firm's services.</h1>
    <p class="advx-hero__sub reveal">Valora puts your firm in front of people who are already looking for the advice you give.</p>
    <ul class="advx-ticks reveal">
      <li>Be found when people ask AI tools and search for financial advice</li>
      <li>Reach the people your firm serves best, directly</li>
      <li>Built only for advisory firms</li>
    </ul>
    <p class="advx-hero__note reveal">Results vary by firm, market and competition. Valora does not guarantee clients.</p>
  </div>
  <aside class="hcard hcard--inquiry advx-hero__form" aria-label="Tell Valora about your firm">{inquiry_host()}</aside>
</div></section>
<section class="section section--paper advx-why" id="introductions"><div class="container">
  <h2 class="advx-h2 reveal">Why Valora?</h2>
  <div class="advx-cards">
    <div class="advx-card reveal">{_icon("check")}<h3>Right people</h3><p>We focus on people who are already looking for the kind of advice your firm gives.</p></div>
    <div class="advx-card reveal">{_icon("book")}<h3>Built for advisors</h3><p>Valora works only with advisory firms, so the work fits how advice is found and chosen.</p></div>
    <div class="advx-card reveal">{_icon("mail")}<h3>Done for you</h3><p>We do the work. Your firm reviews what goes out under its name.</p></div>
  </div>
</div></section>
<section class="section section--cream advx-how" id="how-it-works"><div class="container">
  <h2 class="advx-h2 reveal">How it works</h2>
  <ol class="advx-steps">
    <li class="reveal"><span class="advx-steps__n">01</span><div><h3>Tell us about your firm</h3><p>Who you serve, where you work and the clients you want more of.</p></div></li>
    <li class="reveal"><span class="advx-steps__n">02</span><div><h3>We get your firm in front of them</h3><p>We make your firm easier to find in AI answers and search, and reach out directly to people who fit.</p></div></li>
    <li class="reveal"><span class="advx-steps__n">03</span><div><h3>You have the conversations</h3><p>People who want to talk come to your firm. You take it from there.</p></div></li>
  </ol>
  <div class="advx-center reveal"><a class="btn btn--dark advx-btn" href="/#contact" data-gate-open>Get started</a></div>
</div></section>
<section class="section section--paper advx-tools" id="how-we-do-it"><div class="container">
  <h2 class="advx-h2 reveal">How we get you there</h2>
  <p class="advx-lead reveal">These are the tools. The goal is the same: more conversations with people who need your firm.</p>
  <div class="advx-cards advx-cards--left">
    <div class="advx-card reveal"><p class="advx-card__tag">AEO</p><h3>Answer engine optimization</h3><p>People now ask AI assistants who to trust with their money. We work to make your firm an answer they can give.</p></div>
    <div class="advx-card reveal"><p class="advx-card__tag">GEO</p><h3>Generative engine optimization</h3><p>We publish your firm's expertise in a form AI-powered search can find, read and cite.</p></div>
    <div class="advx-card reveal"><p class="advx-card__tag">Outbound</p><h3>Direct outreach</h3><p>We reach out to people who fit the clients you serve, so you are not relying only on being found.</p></div>
  </div>
</div></section>
<section class="section section--cream advx-blog" id="insights-for-advisors"><div class="container">
  <h2 class="advx-h2 reveal">Insights for advisory firms</h2>
  <p class="advx-lead reveal">Practical articles on advisory-firm growth, operations and communication. These articles are educational, not a promise of clients, search rankings or business results.</p>
  {_blog_cards()}
  <div class="advx-center reveal"><a class="btn btn--outline advx-btn" href="{BLOG_URL}" target="_blank" rel="noopener">View more articles</a></div>
</div></section>
<section class="section section--paper advx-scope" id="portal"><div class="container">
  <h2 class="advx-h2 reveal">Clear expectations</h2>
  <p class="advx-lead reveal">We would rather tell you now than waste your time.</p>
  <div class="advx-fit">
    <div class="advx-fit__col advx-fit__col--yes reveal"><h3>What you can expect</h3><ul>
      <li>Work aimed at people already looking for the advice your firm gives</li>
      <li>Your firm made easier to find in AI answers and search</li>
      <li>Direct outreach to people who fit the clients you serve</li>
    </ul></div>
    <div class="advx-fit__col advx-fit__col--no reveal" id="directory"><h3>What we do not promise</h3><ul>
      <li>Guaranteed clients, search rankings or AI citations</li>
      <li>Overnight results. Visibility builds over time</li>
      <li>Investment advice. Valora is not a registered investment adviser</li>
    </ul></div>
  </div>
</div></section>
<section class="section section--green advx-band"><div class="container">
  <div><h2 class="reveal">Ready to reach more of the right people?</h2><p class="reveal">Tell us about your firm. We review every inquiry and reply by email.</p></div>
  <a class="btn btn--cream advx-btn reveal" href="/#contact" data-gate-open>Get started</a>
</div></section>
<section class="section section--paper adv-faq advx-faq" id="faq"><div class="container"><h2 class="advx-h2 reveal">Frequently asked questions</h2><div class="faq">{_faq_accordion()}</div></div></section>
<section class="advx-cross"><div class="container"><div><h2>Not an advisory firm?</h2><p>Read Valora's educational guides on financial planning.</p></div><a class="btn btn--outline advx-btn" href="/guides/">Browse the guides</a></div></section>"""
