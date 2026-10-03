"""For Advisors: landing page. Promise is reaching people who are seeking
the firm's services; AEO & GEO, outbound and YouTube are the means, not the pitch.

All copy lives in _build/data/for-advisors.json so it can be edited from the
CMS; this module only lays it out."""
import json
import os
import re
from html import escape
from blog_feed import latest_posts, BLOG_URL
from root_inquiry import inquiry_form_section
from partials import _asset_ver

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "for-advisors.json"), encoding="utf-8") as _f:
    FOR_ADVISORS = json.load(_f)
FOR_ADVISORS_FAQ = [(f["q"], f["a"]) for f in FOR_ADVISORS["faqs"]]

def _faq_accordion():
    return "\n".join(f'<details class="faq__item"><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in FOR_ADVISORS_FAQ)

def _thumb(url):
    """Ghost serves resized webp variants; ask for a card-sized one."""
    return url.replace("/content/images/", "/content/images/size/w600/format/webp/", 1)

def _blog_cards():
    cards = []
    for p in latest_posts(int(FOR_ADVISORS["articles"].get("count", 6))):
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
    f = FOR_ADVISORS["form"]
    return f"""<aside class="advx-form" aria-labelledby="advisorIntroTitle">
    <h2 id="advisorIntroTitle">{escape(f["heading"])}</h2>
    <p class="advx-form__sub">{escape(f["subheading"])}</p>
    <form id="advisorIntro" data-endpoint="{_endpoint()}" data-button-label="{escape(f["button_label"])}" novalidate>
      <div class="advx-form__row">
        <label>First name<input name="first" autocomplete="given-name" required maxlength="60"></label>
        <label>Last name<input name="last" autocomplete="family-name" required maxlength="60"></label>
      </div>
      <label>Work email<input name="email" type="email" autocomplete="email" required maxlength="120" placeholder="name@yourfirm.com"></label>
      <label>Phone number<input name="phone" type="tel" inputmode="tel" autocomplete="tel" maxlength="20"></label>
      <label>Firm name<input name="firm" autocomplete="organization" required maxlength="120"></label>
      <label>Firm website<input name="website" inputmode="url" autocomplete="url" maxlength="160" placeholder="yourfirm.com"></label>
      <p class="advx-form__error" role="alert"></p>
      <button type="submit" class="btn btn--dark advx-btn">{escape(f["button_label"])}</button>
      <p class="advx-form__fine">{escape(f["fine_print"])}</p>
    </form>
    <div id="advisorIntroDone" class="advx-form__done" tabindex="-1" hidden><h3>{escape(f["thanks_heading"])}</h3><p>{escape(f["thanks_body"])}</p></div>
  </aside>"""

def _li(items):
    return "\n".join(f"      <li>{escape(i)}</li>" for i in items)

def _cards(cards):
    out = []
    for c in cards:
        tag = f'<p class="advx-card__tag">{escape(c["tag"])}</p>' if c.get("tag") else ''
        out.append(f'    <div class="advx-card reveal">{tag}<h3>{escape(c["heading"])}</h3><p>{escape(c["body"])}</p></div>')
    return "\n".join(out)

def for_advisors_body():
    d = FOR_ADVISORS
    hero, why, steps, tools, proj, art, exp, close, cross = (d[k] for k in ("hero", "why", "steps", "tools", "projection", "articles", "expectations", "closing", "cross_link"))
    step_items = "\n".join(
        f'    <li class="reveal"><span class="advx-steps__n">{i:02d}</span><div><h3>{escape(s["heading"])}</h3><p>{escape(s["body"])}</p></div></li>'
        for i, s in enumerate(steps["items"], 1))
    stages = '\n    <span class="advx-proj__arrow" aria-hidden="true">&rarr;</span>\n'.join(
        f'    <div><p class="advx-proj__step">{escape(s["heading"])}</p><p>{escape(s["body"])}</p></div>' for s in proj["stages"])
    price = (f'    <p class="advx-price reveal">{escape(hero["price_prefix"])} <strong>{escape(hero["price"])}</strong> {escape(hero["price_suffix"])}'
             f'<span>{escape(hero["price_note"])}</span></p>\n') if hero.get("price") else ''
    return f"""<section class="advx-hero" id="top"><div class="container advx-hero__grid">
  <div class="advx-hero__copy">
    <p class="advx-pill reveal">{escape(hero["label"])}</p>
    <h1 class="advx-hero__title reveal">{escape(hero["headline"])} <span>{escape(hero["headline_accent"])}</span></h1>
    <p class="advx-hero__sub reveal">{escape(hero["subheadline"])}</p>
    <ul class="advx-ticks reveal">
{_li(hero["bullets"])}
    </ul>
{price}    <p class="advx-hero__note reveal">{escape(hero["disclaimer"])}</p>
  </div>
  {_intro_form()}
</div></section>
<section class="section section--paper advx-why" id="introductions"><div class="container advx-why__grid">
  <div class="advx-why__copy">
    <h2 class="advx-stack reveal">{"<br>".join(escape(l) for l in why["statement_lines"])}</h2>
    <p class="reveal">{escape(why["body"])}</p>
    <a class="btn btn--dark advx-btn reveal" href="#top">{escape(why["button_label"])}</a>
  </div>
  <div class="advx-cards advx-cards--two">
{_cards(why["cards"])}
  </div>
</div></section>
<section class="section section--cream advx-how" id="how-it-works"><div class="container">
  <h2 class="advx-h2 reveal">{escape(steps["heading"])}</h2>
  <ol class="advx-steps">
{step_items}
  </ol>
  <div class="advx-center reveal"><a class="btn btn--dark advx-btn" href="#top">{escape(steps["button_label"])}</a></div>
</div></section>
<section class="section section--paper advx-tools" id="how-we-do-it"><div class="container">
  <h2 class="advx-h2 reveal">{escape(tools["heading"])}</h2>
  <p class="advx-lead reveal">{escape(tools["intro"])}</p>
  <div class="advx-cards advx-cards--left">
{_cards(tools["cards"])}
  </div>
</div></section>
<section class="section section--cream advx-proj" id="projection"><div class="container">
  <h2 class="advx-h2 reveal">{escape(proj["heading"])}</h2>
  <p class="advx-lead reveal">{escape(proj["intro"])}</p>
  <div class="advx-proj__flow reveal">
{stages}
  </div>
  <p class="advx-fine reveal">{escape(proj["fine_print"])}</p>
  <div class="advx-center reveal"><a class="btn btn--dark advx-btn" href="#top">{escape(proj["button_label"])}</a></div>
</div></section>
<section class="section section--paper advx-blog" id="insights-for-advisors"><div class="container">
  <h2 class="advx-h2 reveal">{escape(art["heading"])}</h2>
  <p class="advx-lead reveal">{escape(art["intro"])}</p>
  {_blog_cards()}
  <div class="advx-center reveal"><a class="btn btn--outline advx-btn" href="{BLOG_URL}" target="_blank" rel="noopener">{escape(art["button_label"])}</a></div>
</div></section>
<section class="section section--cream advx-scope" id="portal"><div class="container">
  <h2 class="advx-h2 reveal">{escape(exp["heading"])}</h2>
  <p class="advx-lead reveal">{escape(exp["intro"])}</p>
  <div class="advx-fit">
    <div class="advx-fit__col advx-fit__col--yes reveal"><h3>{escape(exp["yes_heading"])}</h3><ul>
{_li(exp["yes_items"])}
    </ul></div>
    <div class="advx-fit__col advx-fit__col--no reveal" id="directory"><h3>{escape(exp["no_heading"])}</h3><ul>
{_li(exp["no_items"])}
    </ul></div>
  </div>
</div></section>
<section class="section section--green advx-band"><div class="container">
  <div><h2 class="reveal">{escape(close["heading"])}</h2><p class="reveal">{escape(close["body"])}</p></div>
  <div class="advx-band__cta"><a class="btn btn--cream advx-btn reveal" href="#top">{escape(close["button_label"])}</a><p class="advx-band__price reveal">{"<br>".join(escape(l) for l in close["price_lines"])}</p></div>
</div></section>
<section class="section section--paper adv-faq advx-faq" id="faq"><div class="container"><h2 class="advx-h2 reveal">{escape(d["faq_heading"])}</h2><div class="faq">{_faq_accordion()}</div></div></section>
<section class="advx-cross"><div class="container"><div><h2>{escape(cross["heading"])}</h2><p>{escape(cross["body"])}</p></div><a class="btn btn--outline advx-btn" href="{escape(cross["href"])}">{escape(cross["button_label"])}</a></div></section>
<script defer src="/assets/advisor-intro-form.js?v={_asset_ver("advisor-intro-form.js")}"></script>"""
