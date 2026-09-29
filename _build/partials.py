# -*- coding: utf-8 -*-
"""Shared markup for every Valora page: <head>, header, footer, lead forms.

index.html keeps its own hand-written sections, but its header, footer,
client forms and modal live between <!-- @build:NAME --> markers and are
rewritten from here, so every page stays identical.
"""
import hashlib
import json
import os
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _asset_ver(filename):
    """Short content hash for cache-busting /styles.css and /script.js. Without
    this, a returning visitor's browser can keep serving a JS/CSS file cached
    from before the last deploy against the newly-deployed HTML — exactly the
    stale-script bug that made the two-step contact form look broken in dev."""
    try:
        with open(os.path.join(ROOT, filename), "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()[:8]
    except FileNotFoundError:
        return "0"


STYLES_VER = _asset_ver("styles.css")
SCRIPT_VER = _asset_ver("script.js")

BRAND = "Valora"
SITE_URL = "https://www.valorahq.com"
EMAIL = "barot@valorahq.com"
PHONE_DISPLAY = ""  # removed: unverified number (founder, Sep 28) - do not re-add without a confirmed line
PHONE_TEL = ""

# the original "What are you solving for?" options
GOAL_OPTIONS = ["Retirement income", "Equity compensation", "Selling a business",
                "Estate & legacy", "A second opinion"]

# qualifying questions on the full contact form (page_form)
HELP_OPTIONS = ["Managing investments", "Retirement planning", "Selling a business",
                "Business owner wealth planning", "Tax planning", "Estate planning",
                "Concentrated stock", "Inheritance / sudden wealth",
                "Cash / liquidity management", "Other"]

# Shared with directory_pages.py, which builds a real page for each of these,
# and with footer() below, which links to them. Defined here (not in
# directory_pages.py) so both that module and this one can import them
# without a circular import.
# (slug, label, substrings matched against an advisor's tags, case-insensitive)
DIRECTORY_SPECIALTIES = [
    ("managing-investments", "Managing investments", ["investment"]),
    ("retirement-planning", "Retirement planning", ["retirement"]),
    ("selling-a-business", "Selling a business", ["business sale", "exit"]),
    ("business-owner-wealth-planning", "Business owner wealth planning", ["business owner"]),
    ("tax-planning", "Tax planning", ["tax"]),
    ("estate-planning", "Estate planning", ["estate"]),
    ("concentrated-stock", "Concentrated stock", ["concentrated stock"]),
    ("inheritance-sudden-wealth", "Inheritance / sudden wealth", ["inheritance", "sudden wealth"]),
    ("cash-liquidity-management", "Cash / liquidity management", ["liquidity", "cash management"]),
]

# (slug, "City, ST") — the ~30 largest US metro areas. Real advisor matches
# (currently Austin, Los Angeles) get a populated page; the rest are honest
# empty-state previews, marked noindex until a real advisor is based there
# (see directory_pages.real_pages()) — same pattern as niches/asset types.
DIRECTORY_CITIES = [
    ("new-york", "New York, NY"),
    ("los-angeles", "Los Angeles, CA"),
    ("chicago", "Chicago, IL"),
    ("dallas", "Dallas, TX"),
    ("houston", "Houston, TX"),
    ("washington-dc", "Washington, DC"),
    ("miami", "Miami, FL"),
    ("philadelphia", "Philadelphia, PA"),
    ("atlanta", "Atlanta, GA"),
    ("phoenix", "Phoenix, AZ"),
    ("boston", "Boston, MA"),
    ("san-francisco", "San Francisco, CA"),
    ("detroit", "Detroit, MI"),
    ("seattle", "Seattle, WA"),
    ("minneapolis", "Minneapolis, MN"),
    ("san-diego", "San Diego, CA"),
    ("tampa", "Tampa, FL"),
    ("denver", "Denver, CO"),
    ("baltimore", "Baltimore, MD"),
    ("st-louis", "St. Louis, MO"),
    ("charlotte", "Charlotte, NC"),
    ("orlando", "Orlando, FL"),
    ("san-antonio", "San Antonio, TX"),
    ("portland", "Portland, OR"),
    ("sacramento", "Sacramento, CA"),
    ("pittsburgh", "Pittsburgh, PA"),
    ("austin", "Austin, TX"),
    ("las-vegas", "Las Vegas, NV"),
    ("cincinnati", "Cincinnati, OH"),
    ("columbus", "Columbus, OH"),
    ("kansas-city", "Kansas City, MO"),
]

ASSET_OPTIONS = ["Under $250K", "$250K to $500K", "$500K to $1M",
                  "$1M to $3M", "$3M to $10M", "$10M+"]

SITUATION_OPTIONS = ["Business owner", "Executive / professional", "Retired",
                      "Recently sold a business", "Recently received an inheritance",
                      "Entrepreneur / founder", "Other"]

# Directory pages for "who the client is" (niches) and "how much they have"
# (asset types) — reusing the exact same real option lists the qualifying
# form already asks ([[SITUATION_OPTIONS]]/[[ASSET_OPTIONS]] above), so these
# never drift into a separate, invented taxonomy. Not building a separate
# "life events" set: unlike niches/assets, there's no real option list behind
# it yet, and none of ADVISORS is tagged this way — adding it now would mean
# publishing pages with literally nothing real to say. (slug, label)
DIRECTORY_NICHES = [
    ("business-owner", "Business owner"),
    ("executive-professional", "Executive / professional"),
    ("retired", "Retired"),
    ("recently-sold-a-business", "Recently sold a business"),
    ("recently-received-an-inheritance", "Recently received an inheritance"),
    ("entrepreneur-founder", "Entrepreneur / founder"),
]

DIRECTORY_ASSET_TYPES = [
    ("under-250k", "Under $250K"),
    ("250k-to-500k", "$250K to $500K"),
    ("500k-to-1m", "$500K to $1M"),
    ("1m-to-3m", "$1M to $3M"),
    ("3m-to-10m", "$3M to $10M"),
    ("10m-plus", "$10M+"),
]

# Home-page FAQ. Every answer restates a fact already published elsewhere on
# this site (form microcopy, footer disclosure) — nothing here is a new claim,
# so the visible accordion and the FAQPage schema built from it can't drift
# out of sync with what the rest of the page actually says.
CLIENT_FAQ = [
    ("Is Valora free to use?",
     "Yes. Exploring advisors on Valora is free, with no obligation, and we never sell your information."),
    ("Does Valora provide investment advice?",
     "No. Valora is an independent platform that provides financial education and helps consumers discover "
     "financial advisors. Valora does not provide investment, tax, legal, or financial advice — financial "
     "advisory services are provided independently by the advisors you choose to contact."),
    ("How does Valora match me with an advisor?",
     "You answer a few questions about your situation — what you're solving for, your assets, and your "
     "circumstances. Valora surfaces advisors who may fit, and you review their profiles and decide who, "
     "if anyone, to contact."),
    ("Who are the advisors on Valora?",
     "Independent, fiduciary financial advisors — not Valora employees. Valora is an independent platform "
     "that helps you discover them; it isn't an advisory firm itself."),
    ("How soon will I hear back after I submit the form?",
     "After you submit, we review your request and email you about next steps. Timing may vary."),
]

LOGO_SVG = ('<svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="15" stroke="currentColor" '
            'stroke-width="1.4"/><path d="M6 20.5c4-9 6.5-9 10 0s6 9 10 0" stroke="currentColor" '
            'stroke-width="1.4" stroke-linecap="round"/></svg>')
TICK_SVG = ('<svg viewBox="0 0 32 32" fill="none"><path d="M8 17l5.5 5.5L24 11" stroke="currentColor" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')
FAVICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           "<rect width='100' height='100' rx='22' fill='%231e3b2a'/><text x='50' y='70' font-size='58' "
           "text-anchor='middle' fill='%23efebe0' font-family='Georgia'>V</text></svg>")


# ------------------------------------------------------------------ head
def json_ld(data):
    """A <script type="application/ld+json"> block. `data` is a plain dict; keys
    with a falsy value (None, "", [], {}) are dropped so callers can build a dict
    with optional fields and not worry about emitting empty schema properties."""
    clean = {k: v for k, v in data.items() if v}
    return f'<script type="application/ld+json">{json.dumps(clean, ensure_ascii=False)}</script>'


def organization_schema():
    return json_ld({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": BRAND,
        "url": SITE_URL,
        "description": "Valora is an independent platform that matches people with vetted, "
                        "independent fiduciary financial advisors based on their situation.",
        "email": EMAIL,
        "areaServed": {
            "@type": "Country",
            "name": "United States",
            "identifier": "US",
        },
    })


def article_schema(headline, description, url, date_published, author_name, image=None):
    """Article schema for an /insights/ page — same headline/description/date
    already visible on the page, so this can't say something the page doesn't."""
    return json_ld({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "description": description,
        "url": url,
        "datePublished": date_published,
        "author": {"@type": "Person", "name": author_name},
        "publisher": {"@type": "Organization", "name": BRAND, "url": SITE_URL},
        "image": image or None,
    })


def advisor_schema(name, job_title, url, image=None, description=None, area_served=None):
    """Person schema for an /advisors/[slug]/ page. `name` containing a comma
    (e.g. "James Conole, CFP®") signals a real individual; a firm name without
    one (e.g. "Even Better Retirement") gets ProfessionalService instead, so
    this never mislabels a firm as a person."""
    is_person = "," in name
    return json_ld({
        "@context": "https://schema.org",
        "@type": "Person" if is_person else "ProfessionalService",
        "name": name,
        "jobTitle": job_title if is_person else None,
        "description": description,
        "url": url,
        "image": image,
        "areaServed": {"@type": "City", "name": area_served} if area_served else None,
    })


def faq_schema(faq):
    """faq: list of (question, answer) tuples — pass the exact same pairs the
    visible <details> accordion on the page renders, so the schema can never
    say something the page doesn't."""
    return json_ld({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            } for q, a in faq
        ],
    })



RB2B_SNIPPET = '<script>!function(key) {if (window.reb2b) return;window.reb2b = {loaded: true};var s = document.createElement("script");s.async = true;s.src = "https://ddwl4m2hdecbv.cloudfront.net/b/" + key + "/" + key + ".js.gz";document.getElementsByTagName("script")[0].parentNode.insertBefore(s, document.getElementsByTagName("script")[0]);}("7N850HK1EMN1");</script>'

POSTHOG_SNIPPET = r"""<script>
    !function(t,e){var o,n,p,r;e.__SV||(window.posthog && window.posthog.__loaded)||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}p||((p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",p.onerror=function(){p=null},(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r));var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],Object.defineProperty(u,"toString",{configurable:!0,enumerable:!0,writable:!0,value:function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e}}),Object.defineProperty(u.people,"toString",{configurable:!0,enumerable:!0,writable:!0,value:function(){return u.toString(1)+".people (stub)"}}),o="mu yu bu Su init Vu Gu zu Uu Ku il Wu Yu ju rh oh ah uh hh dh capture getExtension Zu pu gh calculateEventProperties ph register register_once register_for_session unregister unregister_for_session Hu mh getFeatureFlag getFeatureFlagPayload getFeatureFlagResult getAllFeatureFlags isFeatureEnabled reloadFeatureFlags updateFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSurveysLoaded onSessionId getSurveys getActiveMatchingSurveys renderSurvey displaySurvey cancelPendingSurvey canRenderSurvey canRenderSurveyAsync wh identify setPersonProperties unsetPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset kh shutdown setIdentity clearIdentity get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException addExceptionStep captureLog startExceptionAutocapture stopExceptionAutocapture loadToolbar get_property getSessionProperty yh ih createPersonProfile setInternalOrTestUser bh xu Cu opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing get_explicit_consent_status is_capturing clear_opt_in_out_capturing th debug nl Os getPageViewId captureTraceFeedback captureTraceMetric Du".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
    posthog.init('phc_swhDRhpyNrJXeLkkTpYuH9au4XstiKXqY88XAEmX2Cjk', {
        api_host: 'https://us.i.posthog.com',
        defaults: '2026-05-30',
        person_profiles: 'identified_only', // or 'always' to create profiles for anonymous users as well
    })
</script>"""


def head(title, description, path="/", schema="", noindex=False, keywords=None):
    canonical = SITE_URL + ("" if path == "/" else path)
    robots = '<meta name="robots" content="noindex,follow">\n' if noindex else ""
    return f"""<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
{f'<meta name="keywords" content="' + escape(", ".join(keywords)) + '">' if keywords else ""}
{robots}<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en-us" href="{canonical}">
<link rel="alternate" hreflang="x-default" href="{canonical}">
<meta property="og:locale" content="en_US">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css?v={STYLES_VER}">
<link rel="icon" href="{FAVICON}">
{organization_schema()}
{schema}
""" + POSTHOG_SNIPPET + RB2B_SNIPPET + f"""</head>"""


# ------------------------------------------------------------------ header / footer
# Five categories are staged. Only the first has a complete live guide cohort.
NAV_MENUS = [
    {
        "name": "Financial Advice", "live": True,
        "guides": [
            ("Financial advisors for tech employees", "/financial-advisor-for-tech-employees/"),
            ("Financial advisors for physicians", "/financial-advisor-for-physicians/"),
            ("Financial advisors for business owners", "/financial-advisor-for-business-owners/"),
        ],
        "index": ("All financial advice guides", "/guides/"),
        "resources": [
            ("Financial advisors in New York", "/find-a-financial-advisor/new-york/"),
            ("Financial advisors in Chicago", "/find-a-financial-advisor/chicago/"),
        ],
        "cta": ("Find an advisor", "/find-your-advisor/"),
    },
    {"name": "Retirement", "live": False, "guides": [], "resources": [], "cta": ("Find an advisor", "/find-your-advisor/")},
    {"name": "Investing", "live": False, "guides": [], "resources": [], "cta": ("Find an advisor", "/find-your-advisor/")},
    {"name": "Banking", "live": False, "guides": [], "resources": [], "cta": ("Find an advisor", "/find-your-advisor/")},
    {"name": "Taxes", "live": False, "guides": [], "resources": [], "cta": ("Find an advisor", "/find-your-advisor/")},
]


def _nav_dropdown(menu, index):
    ident = f"nav-menu-{index}"
    def links(items):
        return "\n".join(f'<li><a href="{escape(url)}">{escape(label)}</a></li>' for label, url in items)
    guide_links = links(menu["guides"])
    if menu.get("index"):
        label, url = menu["index"]
        guide_links += f'<li class="nav-menu__all"><a href="{escape(url)}">{escape(label)}</a></li>'
    return f'''<li class="nav-menu">
      <button type="button" class="nav-menu__toggle" aria-expanded="false" aria-controls="{ident}">{escape(menu["name"])} <span aria-hidden="true" class="nav-menu__chevron"></span></button>
      <div class="nav-menu__panel" id="{ident}" hidden>
        <div class="nav-menu__col"><p class="nav-menu__caption">Get help with</p><ul>{guide_links}</ul></div>
        <div class="nav-menu__col nav-menu__col--resources"><p class="nav-menu__caption">More resources</p><a class="nav-menu__action" href="{escape(menu["cta"][1])}">{escape(menu["cta"][0])}</a><ul>{links(menu["resources"])}</ul></div>
      </div>
    </li>'''


def header(active=None, cta=("Find an advisor", "/#contact"), banner=False):
    items = "\n".join(_nav_dropdown(menu, i) for i, menu in enumerate(NAV_MENUS) if menu["live"])
    banner_html = ""
    if banner:
        banner_html = ('<div class="site-banner">Are you a financial advisor? '
                        '<a href="/for-advisors/">Join Valora &rarr;</a></div>')
    return f"""{banner_html}<header class="site-header" id="siteHeader">
  <div class="container header__inner">
    <a class="logo" href="/" aria-label="{BRAND} home">
      <span class="logo__mark" aria-hidden="true">
        {LOGO_SVG}
      </span>
      <span class="logo__word">{BRAND}</span>
    </a>

    <nav class="nav" id="primaryNav" aria-label="Primary">
      <ul class="nav__list">
{items}
      </ul>
      <div class="nav__cta">
        <a class="btn btn--dark" href="{cta[1]}" data-gate-open>{cta[0]}</a>
      </div>
    </nav>

    <button class="nav-toggle" id="navToggle" aria-expanded="false" aria-controls="primaryNav" aria-label="Open menu">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>"""


def footer():
    from calculator_pages import CATEGORIES, _category_slug  # lazy import: avoids a circular import (that module imports this one)
    calc_links = "".join(
        f'<li><a href="/calculators/{_category_slug(cat)}/">{escape(cat)}</a></li>'
        for cat in CATEGORIES
    )
    from us_directory_pages import all_states  # lazy import: avoids a circular import (that module imports this one)
    state_links = "".join(
        f'<li><a href="/top-financial-advisors/{slug}/">{escape(name)}</a></li>'
        for slug, name in all_states()[:5]
    )
    return f"""<footer class="footer">
  <div class="container">
    <h2 class="display display--md footer__statement reveal">Independent advice.<br><em>Personal fit.</em></h2>

    <div class="footer__grid">
      <nav class="footer__col" aria-label="Cities"><h5>Cities</h5><ul>{"".join(f'<li><a href="/find-a-financial-advisor/{slug}/">{escape(city)}</a></li>' for slug, city in DIRECTORY_CITIES[:5])}<li><a href="/cities/">More &rarr;</a></li></ul></nav>
      <nav class="footer__col" aria-label="Specialties"><h5>Specialties</h5><ul>{"".join(f'<li><a href="/find-a-financial-advisor/{slug}/">{escape(label)}</a></li>' for slug, label, _ in DIRECTORY_SPECIALTIES[:5])}<li><a href="/specialties/">More &rarr;</a></li></ul></nav>
      <nav class="footer__col" aria-label="Professions"><h5>Professions</h5><ul>{"".join(f'<li><a href="/find-a-financial-advisor/{slug}/">{escape(label)}</a></li>' for slug, label in DIRECTORY_NICHES[:5])}<li><a href="/professions/">More &rarr;</a></li></ul></nav>
      <nav class="footer__col" aria-label="Asset types"><h5>Asset Types</h5><ul>{"".join(f'<li><a href="/find-a-financial-advisor/{slug}/">{escape(label)}</a></li>' for slug, label in DIRECTORY_ASSET_TYPES)}</ul></nav>
      <nav class="footer__col" aria-label="Top financial advisors"><h5>Top Advisors</h5><ul>{state_links}<li><a href="/top-financial-advisors/">More &rarr;</a></li></ul></nav>
      <nav class="footer__col" aria-label="Calculators"><h5>Calculators</h5><ul>{calc_links}</ul></nav>
    </div>

    <div class="footer__nav-bottom">
      <div class="footer__brand">
        <a class="logo logo--light" href="/">
          <span class="logo__mark" aria-hidden="true">{LOGO_SVG}</span>
          <span class="logo__word">{BRAND}</span>
        </a>
        <p>An independent platform helping people discover financial advisors.</p>
        <ul class="footer__contact">
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
        </ul>
      </div>

      <nav class="footer__col" aria-label="Company"><h5>Company</h5><ul><li><a href="/#approach">Our approach</a></li><li><a href="/#advisors">Find an advisor</a></li><li><a href="/for-advisors/">For advisors</a></li><li><a href="/team/">Team</a></li><li><a href="/#insights">Insights</a></li></ul></nav>
      <nav class="footer__col" aria-label="For advisors tools"><h5>For Advisors &middot; Tools</h5><ul><li><a href="/for-advisors/">For advisers</a></li><li><a href="/for-advisors/#compare">How Valora compares</a></li><li><a href="/#insights">Insights</a></li><li><a href="/for-advisors/#apply">Book a demo</a></li></ul></nav>
      <nav class="footer__col" aria-label="Legal"><h5>Legal</h5><ul><li><a href="/terms/">Terms</a></li><li><a href="/privacy/">Privacy</a></li><li><a href="/cookies/">Cookies</a></li></ul></nav>
    </div>

    <div class="footer__base">
      <p>© <span id="year">2026</span> SpacesOS Inc. Valora is a SpacesOS Inc. product. {BRAND} is an independent platform that provides financial education and helps consumers discover financial advisors. {BRAND} does not provide investment, tax, legal, or financial advice. Financial advisory services are provided independently by the advisors you choose to contact. Advisors may pay {BRAND} for access to the platform or for introductions to prospective clients.</p>
    </div>
  </div>
</footer>

<button class="to-top" id="toTop" aria-label="Back to top"><span aria-hidden="true">↑</span></button>"""


# ------------------------------------------------------------------ client lead forms (original fields)
def _goal_select(uid):
    opts = '<option value="">Select one</option>' + "".join(f"<option>{escape(o)}</option>" for o in GOAL_OPTIONS)
    return f'<select id="{uid}goal" name="goal" required>{opts}</select>'


def client_fields(kind, uid, with_note=False, with_goal=True):
    """kind: 'hero' | 'gate' | 'page' — name, email, phone, what are you solving for (+ note on page form).
    with_goal=False drops the "solving for" select — used on page_form, which asks its own
    qualifying questions instead (see qualify_fields)."""
    wrap = {"hero": "hfield", "gate": "gate__field", "page": "field"}[kind]
    out = f"""
        <div class="{wrap}" data-field>
          <label for="{uid}name">Full name</label>
          <input id="{uid}name" name="name" type="text" required placeholder="Jordan Reyes" autocomplete="name">
          <small class="err" data-err="name"></small>
        </div>
        <div class="{wrap}" data-field>
          <label for="{uid}email">Email</label>
          <input id="{uid}email" name="email" type="email" required placeholder="jordan@email.com" autocomplete="email">
          <small class="err" data-err="email"></small>
        </div>
        <div class="{wrap}" data-field>
          <label for="{uid}phone">Phone number</label>
          <input id="{uid}phone" name="phone" type="tel" required placeholder="(415) 555-0100" autocomplete="tel" inputmode="tel">
          <small class="err" data-err="phone"></small>
        </div>"""
    if with_goal:
        out += f"""
        <div class="{wrap}" data-field>
          <label for="{uid}goal">What are you solving for?</label>
          {_goal_select(uid)}
          <small class="err" data-err="goal"></small>
        </div>"""
    if with_note:
        out += f"""
        <div class="{wrap} field--full" data-field>
          <label for="{uid}note">Anything we should know?</label>
          <textarea id="{uid}note" name="note" rows="3" placeholder="A sentence is plenty."></textarea>
        </div>"""
    return out


def hero_card():
    return f"""<aside class="hcard reveal reveal--right">
      <span class="hcard__edge" aria-hidden="true"></span>
      <p class="hcard__eyebrow">Free · No obligation</p>
      <h2 class="hcard__title">Explore financial advisors<br><em>who may fit your needs.</em></h2>

      <form class="hcard__form form--steps" id="heroForm" data-lead="Client" data-done="#heroDone" novalidate>
        <div class="form__step" data-step>
          <p class="form__stepnum">Step 1 of 4</p>
          {help_fields(wrap="hfield")}
          <button class="btn btn--cream hcard__submit" type="button" data-step-next>Continue</button>
        </div>
        <div class="form__step" data-step hidden>
          <p class="form__stepnum">Step 2 of 4</p>
          {details_fields("h", wrap="hfield", wrap_full="hfield")}
          {situation_field("h", wrap="hfield")}
          <div class="hcard__stepnav">
            <button class="hcard__back" type="button" data-step-back>Back</button>
            <button class="btn btn--cream hcard__submit" type="button" data-step-next>Continue</button>
          </div>
        </div>
        <div class="form__step" data-step hidden>
          <p class="form__stepnum">Step 3 of 4</p>
          {client_fields("hero", "h", with_goal=False)}
          <div class="hcard__stepnav">
            <button class="hcard__back" type="button" data-step-back>Back</button>
            <button class="btn btn--cream hcard__submit" type="button" data-step-next>Continue</button>
          </div>
        </div>
        <div class="form__step" data-step hidden>
          <p class="form__stepnum">Step 4 of 4</p>
          {optional_field("h", wrap="hfield")}
          <div class="hcard__stepnav">
            <button class="hcard__back" type="button" data-step-back>Back</button>
            <button class="btn btn--cream hcard__submit" type="submit">Explore advisors</button>
          </div>
        </div>
        <p class="hcard__fine"></p>
      </form>

      <div class="hcard__done" id="heroDone" hidden>
        <span class="hcard__tick" aria-hidden="true">
          {TICK_SVG}
        </span>
        <h3 data-done-title>Thank you.</h3>
        <p>After you submit, we review your request and email you about next steps. Timing may vary.</p>
      </div>
    </aside>"""


def _check_group(name, options, legend, wrap="field field--full"):
    items = "\n".join(
        f'          <label class="check"><input type="checkbox" name="{name}" value="{escape(o)}"><span>{escape(o)}</span></label>'
        for o in options
    )
    return f"""<div class="{wrap}" data-field>
          <label>{escape(legend)}</label>
          <span class="opt">Select all that apply</span>
          <div class="check-group" role="group" aria-label="{escape(legend)}">
{items}
          </div>
        </div>"""


def _select_field(uid, name, label, options, placeholder="Select one", wrap="field"):
    opts = f'<option value="">{escape(placeholder)}</option>' + "".join(f"<option>{escape(o)}</option>" for o in options)
    return f"""<div class="{wrap}" data-field>
          <label for="{uid}{name}">{escape(label)}</label>
          <select id="{uid}{name}" name="{name}" required>{opts}</select>
          <small class="err" data-err="{name}"></small>
        </div>"""


def help_fields(wrap="field field--full"):
    """Step 1: the single "what do you need help with" question — lowest
    commitment, so it's the least effort a visitor has to give to get started."""
    return _check_group("help", HELP_OPTIONS, "What are you looking for help with?", wrap=wrap)


def situation_field(uid, wrap="field"):
    """Step 3: "what best describes your situation" — asked alongside contact
    info rather than in step 2's asset/location details."""
    return _select_field(uid, "situation", "What best describes your situation?", SITUATION_OPTIONS, wrap=wrap)


def optional_field(uid, wrap="field field--full"):
    """Step 4: the one optional question, kept on its own last step so it
    never reads as a requirement blocking the rest of the form."""
    return f"""<div class="{wrap}" data-field>
          <label for="{uid}message">What would you like help with?</label>
          <span class="opt">Optional</span>
          <textarea id="{uid}message" name="message" rows="3" placeholder="A sentence is plenty."></textarea>
        </div>"""


def details_fields(uid, wrap="field", wrap_full="field field--full"):
    """Step 2: the qualifying details — currently just the asset range.
    Location was here (with an IP-based prefill in script.js's
    prefillLocation) but is removed for now at the user's request on
    2026-09-28; prefillLocation is left in script.js, harmless as a no-op
    with no `location` field on the page, in case it comes back."""
    return _select_field(uid, "assets", "Approximately how much do you have in investable assets?", ASSET_OPTIONS, wrap=wrap)


def page_form(goal=None):
    """Four steps, lowest-commitment first: what you need help with, then the
    qualifying details, then situation + contact info, then the one optional
    question last. All four live in the same form — JS (stepForm in
    script.js) just shows/hides them; with JS off, .form__step[hidden] still
    holds via CSS but the browser's own hidden attribute keeps it usable as
    a single long form (nothing here depends on JS to submit)."""
    return f"""<form class="form form--steps reveal" id="matchForm" data-lead="Client" data-success="Thank you, {{name}} — we review each request by hand and will email you about next steps. Timing may vary." novalidate>
      <div class="form__step" data-step>
        <p class="field field--full form__stepnum">Step 1 of 4</p>{help_fields()}
        <div class="field field--full form__nav">
          <button class="btn btn--cream" type="button" data-step-next>Continue</button>
        </div>
      </div>
      <div class="form__step" data-step hidden>
        <p class="field field--full form__stepnum">Step 2 of 4</p>{details_fields("f")}{situation_field("f")}
        <div class="field field--full form__nav">
          <button class="btn btn--outline" type="button" data-step-back>Back</button>
          <button class="btn btn--cream" type="button" data-step-next>Continue</button>
        </div>
      </div>
      <div class="form__step" data-step hidden>
        <p class="field field--full form__stepnum">Step 3 of 4 — where should advisors reach you?</p>{client_fields("page", "f", with_goal=False)}
        <div class="field field--full form__nav">
          <button class="btn btn--outline" type="button" data-step-back>Back</button>
          <button class="btn btn--cream" type="button" data-step-next>Continue</button>
        </div>
      </div>
      <div class="form__step" data-step hidden>
        <p class="field field--full form__stepnum">Step 4 of 4</p>{optional_field("f")}
        <div class="field field--full form__foot">
          <button class="btn btn--outline" type="button" data-step-back>Back</button>
          <button class="btn btn--cream" type="submit">Explore advisors</button>
          <p class="form__fine"></p>
        </div>
      </div>
      <p class="form__success" role="status" hidden></p>
    </form>"""


def contact_section(goal=None, title='Let\'s build a<br>financial life<br><em>that feels like yours.</em>'):
    form = page_form()
    if goal:  # preselect the matching "solving for" option on specialty pages
        form = form.replace(f"<option>{escape(goal)}</option>", f"<option selected>{escape(goal)}</option>", 1)
    return f"""<section class="section section--green cta" id="contact">
  <div class="container cta__grid">
    <div class="cta__copy">
      <h2 class="display display--lg reveal">{title}</h2>
      <p class="reveal">Answer a few questions to find advisors who match your needs.</p>
    </div>

    {form}
  </div>
</section>"""


def client_faq_section():
    return f"""<section class="section section--paper" id="faq">
  <div class="container">
{faq_block(CLIENT_FAQ)}
  </div>
</section>"""


def gate():
    return f"""<div class="gate" id="gate" hidden>
  <div class="gate__scrim" data-gate-close></div>

  <div class="gate__panel" role="dialog" aria-modal="true" aria-labelledby="gateTitle" aria-describedby="gateSub">
    <span class="gate__glow" aria-hidden="true"></span>

    <button class="gate__x" type="button" aria-label="Close" data-gate-close>
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
    </button>

    <div class="gate__inner">
      <p class="gate__eyebrow gate__i" style="--i:1">Free · No obligation</p>
      <h2 class="gate__title display gate__i" id="gateTitle" style="--i:2">
        Explore advisors<br><em>who may fit your needs.</em>
      </h2>
      <p class="gate__sub gate__i" id="gateSub" style="--i:3">
        Answer a few questions to find advisors who match your needs.
      </p>

      <form class="gate__form gate__i form--steps" id="gateForm" data-lead="Client" data-done="#gateDone" style="--i:4" novalidate>
        <div class="form__step" data-step>
          <p class="form__stepnum">Step 1 of 4</p>
          {help_fields(wrap="gate__field")}
          <div class="gate__foot">
            <button class="btn btn--cream gate__submit" type="button" data-step-next>Continue</button>
            <button class="gate__skip" type="button" data-gate-close>I'm just looking</button>
          </div>
        </div>
        <div class="form__step" data-step hidden>
          <p class="form__stepnum">Step 2 of 4</p>
          {details_fields("g", wrap="gate__field", wrap_full="gate__field")}
          {situation_field("g", wrap="gate__field")}
          <div class="gate__foot">
            <button class="gate__skip" type="button" data-step-back>Back</button>
            <button class="btn btn--cream gate__submit" type="button" data-step-next>Continue</button>
          </div>
        </div>
        <div class="form__step" data-step hidden>
          <p class="form__stepnum">Step 3 of 4</p>
          {client_fields("gate", "g", with_goal=False)}
          <div class="gate__foot">
            <button class="gate__skip" type="button" data-step-back>Back</button>
            <button class="btn btn--cream gate__submit" type="button" data-step-next>Continue</button>
          </div>
        </div>
        <div class="form__step" data-step hidden>
          <p class="form__stepnum">Step 4 of 4</p>
          {optional_field("g", wrap="gate__field")}
          <div class="gate__foot">
            <button class="gate__skip" type="button" data-step-back>Back</button>
            <button class="btn btn--cream gate__submit" type="submit">Explore advisors</button>
          </div>
        </div>
        <p class="gate__fine"></p>
      </form>

      <div class="gate__done" id="gateDone" hidden>
        <span class="gate__tick" aria-hidden="true">
          {TICK_SVG}
        </span>
        <h3 class="display" data-done-title style="font-size:1.5rem">Thank you.</h3>
        <p>After you submit, we review your request and email you about next steps. Timing may vary.</p>
        <button class="btn btn--cream" type="button" data-gate-close>Explore the site</button>
      </div>
    </div>
  </div>
</div>"""


# ------------------------------------------------------------------ floating CTA
# Founder directive (Sep 28): a floating "Find your advisor" button on every
# niche/city page that follows scroll. Destination = the page's existing CTA
# target for now; the founder's routing decision is still pending, so the
# target lives in ONE constant - change FLOATING_CTA_HREF and every page
# picks it up on the next build.
# Routing decision (Sep 28): consumer CTAs point to the /find-your-advisor/
# intake, not #contact. One constant still owns the destination - if the
# founder re-routes again, this line is the only change.
FLOATING_CTA_HREF = "/find-your-advisor/"
FLOATING_CTA_UTM = "utm_source=site&utm_medium=cta&utm_campaign=floating-cta"
FLOATING_CTA_LABEL = "Find your advisor"

def floating_cta(utm_content=None):
    href = FLOATING_CTA_HREF
    if utm_content:
        href = f"{href}?{FLOATING_CTA_UTM}&utm_content={utm_content}"
    return (f'<a class="cta-float" id="ctaFloat" href="{href}" '
            f'data-cta="floating-find-advisor" aria-label="{escape(FLOATING_CTA_LABEL)} - answer a few questions">'
            f'{escape(FLOATING_CTA_LABEL)}<span aria-hidden="true" style="margin-left:8px;">&rarr;</span></a>')


def faq_block(faq, heading="Common questions"):
    items = "\n".join(
        f'      <details class="faq__item"><summary>{escape(q)}</summary><p>{escape(a)}</p></details>'
        for q, a in faq
    )
    return f"""<div class="faq">
      <h2 class="faq__title">{heading}</h2>
{items}
    </div>"""


def page(head_html, body_html, active=None, with_gate=False, body_class="page-sub"):
    return f"""<!DOCTYPE html>
<html lang="en-US">
{head_html}
<body class="{body_class}">

<a class="skip-link" href="#main">Skip to content</a>

{header(active)}

<main id="main">
{body_html}
</main>

{footer()}
{gate() if with_gate else ''}
<script src="/script.js?v={SCRIPT_VER}"></script>
</body>
</html>
"""
