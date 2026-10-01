# -*- coding: utf-8 -*-
"""/top-financial-advisors/ — a three-tier geographic directory:

  /top-financial-advisors/                     (US hub — every state with a city page)
  /top-financial-advisors/[state]/             (every city in that state)
  /top-financial-advisors/[state]/[city]/      ("Top Financial Advisors in [City], [ST]")

Reuses the same 31 metros already in partials.DIRECTORY_CITIES — this is a
second URL/page format over the same real data, not a new, bigger list of
cities. Same honesty rules as the rest of the directory: a city gets a real
advisor grid when one actually matches (today: Austin, Los Angeles); every
other city falls back to the real 4-advisor roster with an honest "not
based here, but available nationwide" note (see directory_pages._listing_body
for the identical pattern) and is marked noindex. Only genuine matches are
indexed/listed in the sitemap.
"""
from html import escape

from partials import page, head, BRAND, contact_section, DIRECTORY_CITIES
from advisor_pages import REAL_ADVISORS
from directory_pages import _advisor_card

STATE_NAMES = {
    "NY": "New York", "CA": "California", "IL": "Illinois", "TX": "Texas",
    "DC": "District of Columbia", "FL": "Florida", "PA": "Pennsylvania",
    "GA": "Georgia", "AZ": "Arizona", "MA": "Massachusetts", "MI": "Michigan",
    "WA": "Washington", "MN": "Minnesota", "CO": "Colorado", "MD": "Maryland",
    "MO": "Missouri", "NC": "North Carolina", "OR": "Oregon", "NV": "Nevada",
    "OH": "Ohio",
}


def _state_slug(abbr):
    return STATE_NAMES[abbr].lower().replace(" ", "-")


def _by_state():
    """(state_abbr, state_name, state_slug) -> [(city_slug, city_label), ...],
    grouped from DIRECTORY_CITIES and sorted by state name."""
    groups = {}
    for slug, label in DIRECTORY_CITIES:
        abbr = label.rsplit(", ", 1)[1]
        groups.setdefault(abbr, []).append((slug, label))
    return sorted(
        ((abbr, STATE_NAMES[abbr], _state_slug(abbr), cities) for abbr, cities in groups.items()),
        key=lambda t: t[1],
    )


def build_us_directory(write_fn):
    states = _by_state()

    # tier 1: US hub
    state_links = "".join(
        f'<li><a href="/top-financial-advisors/{state_slug}/">{escape(state_name)}</a></li>'
        for _, state_name, state_slug, _ in states
    )
    body = f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:800px;">
    <p class="eyebrow reveal">Directory</p>
    <h1 class="display display--lg reveal">Top Financial Advisors in the U.S.</h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:60ch;">Browse independent, fiduciary financial advisors on Valora by state, then by city.</p>
    <div class="dir-index" style="margin-top:40px;">
      <div class="dir-index__col"><ul>{state_links}</ul></div>
    </div>
  </div>
</section>

{contact_section()}
"""
    write_fn("/top-financial-advisors/",
              page(head(f"Top Financial Advisors in the U.S. | {BRAND}",
                        "Browse independent, fiduciary financial advisors on Valora by state and city.",
                        path="/top-financial-advisors/"),
                   body))

    for abbr, state_name, state_slug, cities in states:
        # tier 2: per-state
        city_links = "".join(
            f'<li><a href="/top-financial-advisors/{state_slug}/{city_slug}/">{escape(label)}</a></li>'
            for city_slug, label in cities
        )
        state_body = f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:800px;">
    <p class="eyebrow reveal">Directory</p>
    <h1 class="display display--lg reveal">Top Financial Advisors in {escape(state_name)}</h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:60ch;">Independent, fiduciary financial advisors on Valora, by city in {escape(state_name)}.</p>
    <div class="dir-index" style="margin-top:40px;">
      <div class="dir-index__col"><ul>{city_links}</ul></div>
    </div>
  </div>
</section>

{contact_section()}
"""
        write_fn(f"/top-financial-advisors/{state_slug}/",
                  page(head(f"Top Financial Advisors in {state_name} | {BRAND}",
                            f"Browse independent, fiduciary financial advisors on Valora in {state_name}, by city.",
                            path=f"/top-financial-advisors/{state_slug}/"),
                       state_body))

        # tier 3: per-city
        for city_slug, label in cities:
            city_name = label.rsplit(", ", 1)[0]
            matches = [a for a in REAL_ADVISORS if a["city"] == label]
            note = ""
            shown = matches
            if not matches:
                shown = REAL_ADVISORS
                note = (f'<p class="dir-note">We don&rsquo;t have a {escape(city_name)}-based advisor listed yet, '
                        "but the advisors below work with clients remotely, wherever they're based.</p>")
            cards = "\n".join(_advisor_card(a) for a in shown)
            city_body = f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:900px;">
    <p class="eyebrow reveal">{escape(state_name)}</p>
    <h1 class="display display--lg reveal">Top Financial Advisors in {escape(label)}</h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:56ch;">Independent, fiduciary financial advisors based in {escape(label)}.</p>
    <div style="margin-top:40px;">
      {note}
      <div class="match__grid">{cards}</div>
    </div>
  </div>
</section>

{contact_section()}
"""
            write_fn(f"/top-financial-advisors/{state_slug}/{city_slug}/",
                      page(head(f"Top Financial Advisors in {label} | {BRAND}",
                                f"Independent, fiduciary financial advisors in {label} on Valora.",
                                path=f"/top-financial-advisors/{state_slug}/{city_slug}/",
                                noindex=not matches),
                           city_body))


def all_states():
    """(state_slug, state_name) for every state that has at least one city page."""
    return [(state_slug, state_name) for _, state_name, state_slug, _ in _by_state()]


def real_pages():
    """(path, description) for city pages with a genuine advisor match — the
    only tier-3 pages build.py should list in the sitemap/llms.txt."""
    out = []
    for abbr, state_name, state_slug, cities in _by_state():
        for city_slug, label in cities:
            if [a for a in REAL_ADVISORS if a["city"] == label]:
                out.append((f"/top-financial-advisors/{state_slug}/{city_slug}/",
                             f"Top financial advisors in {label} on Valora."))
    return out
