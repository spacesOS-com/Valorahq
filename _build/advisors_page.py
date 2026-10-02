"""For Advisors: landing page. Promise is reaching people who are seeking
the firm's services; AEO & GEO, outbound and YouTube are the means, not the pitch."""
from html import escape
from blog_feed import latest_posts, BLOG_URL
from root_inquiry import inquiry_form_section
from partials import _asset_ver
import re
FOR_ADVISORS_FAQ = [
    ('How does Valora help my firm reach new clients?', 'Valora works to put your firm in front of people who are already looking for the kind of advice you give. We do that in three ways: by making your firm easier to find when people ask AI tools and search engines about financial advice, by reaching out directly to people who fit the clients you serve, and by putting your firm\'s expertise on YouTube.'),
    ('What are AEO and GEO?', 'Answer engine optimization (AEO) and generative engine optimization (GEO) are the work of making a firm\'s expertise easy for AI assistants and AI-powered search to find, read and cite. They are tools we use, alongside outbound outreach and YouTube, to connect your firm with people seeking its services.'),
    ('Does Valora guarantee new clients?', 'No. Results depend on your firm, your market and your competition, and visibility builds over time. Valora does not guarantee clients, search rankings, AI citations or video views.'),
    ('Who approves what is published or sent for my firm?', 'Your firm does. Advisory firms are responsible for their own advertising and communications, so nothing should go out under your firm\'s name without your review.'),
    ('What does it cost?', 'Plans start at $900 per month. The price depends on the scope of work for your firm. Tell us about your firm and we will reply by email.'),
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

def _endpoint():
    """Same reviewed endpoint as the site-wide inquiry form."""
    return re.search(r'data-endpoint="([^"]+)"', inquiry_form_section()).group(1)

def _intro_form():
    return f"""<aside class="advx-form" aria-labelledby="advisorIntroTitle">
    <h2 id="advisorIntroTitle">Tell us about your firm</h2>
    <p class="advx-form__sub">See how Valora can put your firm in front of the right people.</p>
    <form id="advisorIntro" data-endpoint="{_endpoint()}" novalidate>
      <div class="advx-form__row">
        <label>First name<input name="first" autocomplete="given-name" required maxlength="60"></label>
        <label>Last name<input name="last" autocomplete="family-name" required maxlength="60"></label>
      </div>
      <label>Work email<input name="email" type="email" autocomplete="email" required maxlength="120" placeholder="name@yourfirm.com"></label>
      <label>Phone number<input name="phone" type="tel" inputmode="tel" autocomplete="tel" maxlength="20"></label>
      <label>Firm name<input name="firm" autocomplete="organization" required maxlength="120"></label>
      <label>Firm website<input name="website" inputmode="url" autocomplete="url" maxlength="160" placeholder="yourfirm.com"></label>
      <p class="advx-form__error" role="alert"></p>
      <button type="submit" class="btn btn--dark advx-btn">Get started</button>
      <p class="advx-form__fine">We review every inquiry and reply by email. Valora does not guarantee clients, revenue or asset growth.</p>
    </form>
    <div id="advisorIntroDone" class="advx-form__done" tabindex="-1" hidden><h3>Thank you.</h3><p>We have your details and will reply by email.</p></div>
  </aside>"""

def for_advisors_body():
    return f"""<section class="advx-hero" id="top"><div class="container advx-hero__grid">
  <div class="advx-hero__copy">
    <p class="advx-pill reveal">For financial advisory firms</p>
    <h1 class="advx-hero__title reveal">Connect with people <span>seeking your firm's services.</span></h1>
    <p class="advx-hero__sub reveal">Valora puts your firm in front of people who are already looking for the advice you give, and helps you start the conversation.</p>
    <ul class="advx-ticks reveal">
      <li>Be found when people ask AI tools and search for financial advice</li>
      <li>Reach the people your firm serves best, directly</li>
      <li>Be seen on YouTube, where people go to learn</li>
      <li>Built only for advisory firms</li>
    </ul>
    <p class="advx-price reveal">Starts at <strong>$900</strong> per month</p>
    <p class="advx-hero__note reveal">Results vary by firm, market and competition. Valora does not guarantee clients.</p>
  </div>
  {_intro_form()}
</div></section>
<section class="section section--paper advx-why" id="introductions"><div class="container advx-why__grid">
  <div class="advx-why__copy">
    <h2 class="advx-stack reveal">Grow your firm.<br>Be found first.<br>Start more conversations.</h2>
    <p class="reveal">People looking for a financial advisor now ask AI tools and search before they ask a friend. Valora works to make your firm the one they find, and reaches out to the people who fit you best.</p>
    <a class="btn btn--dark advx-btn reveal" href="#top">Get started</a>
  </div>
  <div class="advx-cards advx-cards--two">
    <div class="advx-card reveal"><h3>People already looking</h3><p>We focus on people who are actively seeking the kind of advice your firm gives.</p></div>
    <div class="advx-card reveal"><h3>The clients you want</h3><p>Tell us who you serve and where. The work is aimed at them.</p></div>
    <div class="advx-card reveal"><h3>Built for advisory firms</h3><p>Valora works only with advisory firms, so the work fits how advice is found and chosen.</p></div>
    <div class="advx-card reveal"><h3>Done for you</h3><p>We do the work. Your firm reviews what goes out under its name.</p></div>
  </div>
</div></section>
<section class="section section--cream advx-how" id="how-it-works"><div class="container">
  <h2 class="advx-h2 reveal">As easy as 1, 2, 3</h2>
  <ol class="advx-steps">
    <li class="reveal"><span class="advx-steps__n">01</span><div><h3>Tell us about your firm</h3><p>Who you serve, where you work and the clients you want more of.</p></div></li>
    <li class="reveal"><span class="advx-steps__n">02</span><div><h3>We get your firm in front of them</h3><p>We make your firm easier to find in AI answers, search and on YouTube, and reach out directly to people who fit.</p></div></li>
    <li class="reveal"><span class="advx-steps__n">03</span><div><h3>You have the conversations</h3><p>People who want to talk come to your firm. You take it from there.</p></div></li>
  </ol>
  <div class="advx-center reveal"><a class="btn btn--dark advx-btn" href="#top">Get started</a></div>
</div></section>
<section class="section section--paper advx-tools" id="how-we-do-it"><div class="container">
  <h2 class="advx-h2 reveal">How we get you there</h2>
  <p class="advx-lead reveal">These are the tools. The goal is the same: more conversations with people who need your firm.</p>
  <div class="advx-cards advx-cards--left">
    <div class="advx-card reveal"><p class="advx-card__tag">AEO &amp; GEO</p><h3>Be the answer AI gives</h3><p>People now ask AI assistants and AI-powered search who to trust with their money. Answer engine optimization and generative engine optimization make your firm's expertise easy for them to find, read and cite.</p></div>
    <div class="advx-card reveal"><p class="advx-card__tag">Outbound</p><h3>Direct outreach</h3><p>We reach out to people who fit the clients you serve, so you are not relying only on being found.</p></div>
    <div class="advx-card reveal"><p class="advx-card__tag">YouTube</p><h3>Be seen before the first call</h3><p>People watch before they choose an advisor. We put your firm's expertise on YouTube, where they go to learn.</p></div>
  </div></section>
<section class="section section--cream advx-proj" id="projection"><div class="container">
  <h2 class="advx-h2 reveal">Know what to expect before you start</h2>
  <p class="advx-lead reveal">Before any work begins, we build a projection for your firm, so you can see the numbers we are working toward.</p>
  <div class="advx-proj__flow reveal">
    <div><p class="advx-proj__step">Search demand</p><p>How often people search and ask AI about the topics your firm covers</p></div>
    <span class="advx-proj__arrow" aria-hidden="true">&rarr;</span>
    <div><p class="advx-proj__step">Projected visitors</p><p>Quarter-by-quarter website traffic we expect that demand to bring</p></div>
    <span class="advx-proj__arrow" aria-hidden="true">&rarr;</span>
    <div><p class="advx-proj__step">Projected leads</p><p>A minimum base of leads we expect from that traffic</p></div>
  </div>
  <p class="advx-fine reveal">A projection is an estimate built on stated assumptions, not a result. Every firm's projection is different, and Valora does not guarantee visitors, leads or clients.</p>
  <div class="advx-center reveal"><a class="btn btn--dark advx-btn" href="#top">Get your projection</a></div>
</div></section>
<section class="section section--paper advx-blog" id="insights-for-advisors"><div class="container">
  <h2 class="advx-h2 reveal">Timely articles for your firm</h2>
  <p class="advx-lead reveal">Practical articles on advisory-firm growth, operations and communication. These articles are educational, not a promise of clients, search rankings or business results.</p>
  {_blog_cards()}
  <div class="advx-center reveal"><a class="btn btn--outline advx-btn" href="{BLOG_URL}" target="_blank" rel="noopener">View more articles</a></div>
</div></section>
<section class="section section--cream advx-scope" id="portal"><div class="container">
  <h2 class="advx-h2 reveal">Clear expectations</h2>
  <p class="advx-lead reveal">We would rather tell you now than waste your time.</p>
  <div class="advx-fit">
    <div class="advx-fit__col advx-fit__col--yes reveal"><h3>What you can expect</h3><ul>
      <li>Work aimed at people already looking for the advice your firm gives</li>
      <li>Your firm made easier to find in AI answers and search</li>
      <li>Direct outreach to people who fit the clients you serve</li>
      <li>Your firm's expertise on YouTube</li>
    </ul></div>
    <div class="advx-fit__col advx-fit__col--no reveal" id="directory"><h3>What we do not promise</h3><ul>
      <li>Guaranteed clients, search rankings, AI citations or video views</li>
      <li>Overnight results. Visibility builds over time</li>
      <li>Investment advice. Valora is not a registered investment adviser</li>
    </ul></div>
  </div>
</div></section>
<section class="section section--green advx-band"><div class="container">
  <div><h2 class="reveal">Ready to get started?</h2><p class="reveal">Tell us about your firm. We review every inquiry and reply by email.</p></div>
  <div class="advx-band__cta"><a class="btn btn--cream advx-btn reveal" href="#top">Get started</a><p class="advx-band__price reveal">Starts at $900 per month</p></div>
</div></section>
<section class="section section--paper adv-faq advx-faq" id="faq"><div class="container"><h2 class="advx-h2 reveal">Frequently asked questions</h2><div class="faq">{_faq_accordion()}</div></div></section>
<section class="advx-cross"><div class="container"><div><h2>Looking for advice?</h2><p>Read Valora's educational guides on financial planning.</p></div><a class="btn btn--outline advx-btn" href="/guides/">Browse the guides</a></div></section>
<script defer src="/assets/advisor-intro-form.js?v={_asset_ver("advisor-intro-form.js")}"></script>"""
