# -*- coding: utf-8 -*-
"""Individual /advisors/[slug]/ profile pages.

No REAL advisor profiles are approved for publication (see Mira's directory
pre-flip HOLD alongside DIRECTORY_ENABLED in build.py). The two entries
below are explicitly-labeled sample/placeholder records (sample=True) added
at the founder's direction to show what a populated profile looks like —
each is unmistakably marked as a placeholder (banner, eyebrow, card quote)
and excluded from the sitemap/indexing via noindex. Never add a record that
could be mistaken for a real person; a sample record's name, firm and bio
must stay obviously synthetic.

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
  sample                                 -- True for a labeled placeholder record (see module docstring)
"""
from html import escape

from partials import page, head, BRAND, contact_section

PLACEHOLDER_AVATAR = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E"
    "%3Crect width='200' height='200' fill='%23e3e0d6'/%3E"
    "%3Ccircle cx='100' cy='78' r='34' fill='%23b9b4a3'/%3E"
    "%3Cpath d='M30 190c0-42 31-70 70-70s70 28 70 70' fill='%23b9b4a3'/%3E"
    "%3Ctext x='100' y='196' font-family='Arial' font-size='11' text-anchor='middle' fill='%23756f5c'%3ESAMPLE%3C/text%3E"
    "%3C/svg%3E"
)

ADVISORS = [
    {
        "slug": "sample-advisor-a",
        "name": "Sample Advisor A",
        "firm": "Sample Firm (Placeholder)",
        "photo": PLACEHOLDER_AVATAR,
        "quote": "Sample placeholder profile — not a real person or advisor.",
        "tags": ["Retirement planning", "Business owners"],
        "city": "Austin, TX",
        "status": "Placeholder — not a real advisor",
        "location": "Sample City, ST",
        "credentials": "Sample credential text",
        "bio": [
            "This is a placeholder profile used to preview the advisor-page layout. It does not describe a real person.",
            "Once real, compliance-approved advisor profiles are ready, records like this one will be replaced with genuine data.",
        ],
        "sample": True,
    },
    {
        "slug": "sample-advisor-b",
        "name": "Sample Advisor B",
        "firm": "Sample Firm (Placeholder)",
        "photo": PLACEHOLDER_AVATAR,
        "quote": "Sample placeholder profile — not a real person or advisor.",
        "tags": ["Tax planning"],
        "city": "Austin, TX",
        "status": "Placeholder — not a real advisor",
        "location": "Sample City, ST",
        "credentials": "Sample credential text",
        "bio": [
            "This is a placeholder profile used to preview the advisor-page layout. It does not describe a real person.",
        ],
        "sample": True,
    },
]

# Everything that matches/indexes advisors against specialties, cities and
# combos (directory_pages.py, us_directory_pages.py) must use this, not
# ADVISORS directly — a sample/placeholder record must never surface as a
# "real match" on an indexed directory page. Only the dedicated profile
# builder below and the homepage roster section use the full ADVISORS list,
# where the sample banner/eyebrow/card-quote make it unmistakable.
REAL_ADVISORS = [a for a in ADVISORS if not a.get("sample")]


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
    sample_banner = ("""<div class="advisor-profile__sample-banner" role="note">
  <div class="container"><strong>Sample placeholder profile.</strong> This page previews the advisor-page layout. """
  """It does not describe a real person, and Valora does not currently have an approved advisor directory.</div>
</div>""") if a.get("sample") else ""
    return f"""
{sample_banner}
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
                 social_image=a.get("photo"),
                 noindex=bool(a.get("sample"))),
            _advisor_body(a),
            active="advisors",
        )
        write_fn(f"/advisors/{a['slug']}/", html)
