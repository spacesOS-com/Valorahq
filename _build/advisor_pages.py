# -*- coding: utf-8 -*-
"""Individual /advisors/[slug]/ profile pages.

No advisor profiles are approved for publication (see Mira's directory
pre-flip HOLD alongside DIRECTORY_ENABLED in build.py). ADVISORS stays
empty — this module is ready-built infrastructure, not a decision to
publish anyone. Never add a placeholder/sample person to this list; add
only real, reviewed profiles once compliance approves them.

Expected record shape (all keys except slug/name/firm/photo/quote/tags
are optional):
  slug, name, firm, photo, quote, tags   -- also used by directory cards
  city                                   -- used by directory matching
  status                                 -- e.g. "Taking new clients"
  location                               -- e.g. "Austin, TX"
  credentials                            -- e.g. "CERTIFIED FINANCIAL PLANNER (CFP)"
  bio                                    -- list[str], one paragraph per item
  articles                               -- list[{title, url, excerpt}], this advisor's own writing
  videos                                 -- list[{title, url, thumbnail}], this advisor's own videos
"""
from html import escape

from partials import page, head, BRAND, contact_section

ADVISORS = []


def _fact(label, value):
    if not value:
        return ""
    return (f'<div class="advisor-profile__fact"><p class="advisor-profile__fact-label">{escape(label)}</p>'
            f'<p class="advisor-profile__fact-value">{escape(value)}</p></div>')


def _bio(paragraphs):
    return "\n".join(f"<p>{escape(p)}</p>" for p in paragraphs or [])


def _tags(tags):
    return "".join(f"<li>{escape(t)}</li>" for t in tags or [])


def _article_cards(articles):
    cards = "\n".join(
        f'<article class="blogcard reveal"><h3><a href="{escape(p["url"])}">{escape(p["title"])}</a></h3>'
        f'<p>{escape(p["excerpt"])}</p><a class="blogcard__link" href="{escape(p["url"])}">Read &rarr;</a></article>'
        for p in articles
    )
    return f"""<section class="section section--cream advisor-profile__articles"><div class="container">
  <p class="eyebrow reveal">From {{name}}</p><h2 class="display display--lg reveal">Articles</h2>
  <div class="adv-blog__grid">{cards}</div>
</div></section>"""


def _video_cards(videos):
    cards = "\n".join(
        f'<article class="blogcard advisor-profile__video reveal"><a href="{escape(v["url"])}">'
        f'<img src="{escape(v["thumbnail"])}" alt="" loading="lazy"><h3>{escape(v["title"])}</h3></a></article>'
        for v in videos
    )
    return f"""<section class="section section--paper advisor-profile__videos"><div class="container">
  <p class="eyebrow reveal">Watch</p><h2 class="display display--lg reveal">Videos</h2>
  <div class="adv-blog__grid">{cards}</div>
</div></section>"""


def _advisor_body(a):
    status = a.get("status")
    facts = "".join([
        _fact("Location", a.get("location")),
        _fact("Credentials", a.get("credentials")),
        _fact("Firm", a.get("firm")),
    ])
    articles = a.get("articles")
    videos = a.get("videos")
    return f"""
<section class="section section--paper advisor-profile" id="top">
  <div class="container advisor-profile__hero">
    <div class="advisor-profile__intro">
      {f'<p class="eyebrow advisor-profile__status reveal">{escape(status)}</p>' if status else ''}
      <h1 class="display display--lg reveal">Hi. I&rsquo;m {escape(a['name'])}.</h1>
      <p class="advisor-profile__firm reveal">{escape(a['firm'])}</p>
    </div>
    <img class="advisor-profile__photo reveal reveal--right" src="{escape(a['photo'])}" alt="{escape(a['name'])}" width="360" height="360" loading="lazy">
  </div>

  {f'<div class="container advisor-profile__facts reveal">{facts}</div>' if facts else ''}

  <div class="container advisor-profile__bio reveal">
    {_bio(a.get('bio'))}
  </div>

  {f'<div class="container advisor-profile__tags reveal"><ul class="acard__tags">{_tags(a.get("tags"))}</ul></div>' if a.get('tags') else ''}
</section>

{_article_cards(articles).replace('{name}', escape(a['name'])) if articles else ''}
{_video_cards(videos) if videos else ''}

{contact_section(title=f"Have a question for {a['name']}?")}
"""


def build_advisor_pages(write_fn):
    for a in ADVISORS:
        html = page(
            head(f"{a['name']} | {BRAND}",
                 a.get("quote") or f"{a['name']} at {a['firm']}.",
                 path=f"/advisors/{a['slug']}/",
                 social_image=a.get("photo")),
            _advisor_body(a),
            active="advisors",
        )
        write_fn(f"/advisors/{a['slug']}/", html)
