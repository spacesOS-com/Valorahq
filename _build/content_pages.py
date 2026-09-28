# -*- coding: utf-8 -*-
"""Programmatic content pages rendered from Lena's JSON content packs.

One pack = one page at /<slug>/. Pack schema (keys):
  slug, page_type, meta_title (<=60), meta_description (<=155), keywords[],
  h1, body_html (unique grounded copy), faqs[{q,a}] (plain text - no HTML),
  faq_jsonld (reference only - the build regenerates JSON-LD from the
  visible faqs so they match by construction), internal_links[],
  source_notes[], optional cta {heading, body, button_label, href}
  (href placeholder until the consumer routing decision lands - default
  CTA is the site contact form).
  Foundation-upgrade optional slots:
  key_takeaways[]   styled box after the intro paragraph
  feature_image     {src, alt, caption} hero under the H1
  inline_ctas[]     {after_h2, heading, body, button_label, href} banner
                    rendered at the end of the named h2 section
  tags[]            pill row under the H1 + merged into meta keywords
  toc               auto-generated anchor-linked TOC from body <h2>s;
                    set "toc": false to opt out
"""
import glob
import json
import os
import re

from partials import page, head, faq_schema, faq_block, contact_section, escape, BRAND
from calculator_pages import CALCULATORS

PACK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content-packs")

PAGE_TYPE_LABELS = {
    "niche-profession": "Profession",
    "city": "City",
    "niche-city": "City",
    "life-event": "Life event",
    "asset-type": "Asset type",
    "employer": "Employer",
    "legal": "Legal",
    "team": "Company",
}


def _slugify(text):
    s = re.sub(r"<[^>]+>", "", text).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _linkify(text):
    """Plain-text URL -> clickable link (used for escaped FAQ answers)."""
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', text)


def _tags(tags):
    if not tags:
        return ""
    pills = "\n".join(f'      <li>{escape(t)}</li>' for t in tags)
    return f"""  <ul class="content-page__tags">{pills}
  </ul>"""


def _hero(img):
    if not img or not img.get("src"):
        return ""
    cap = f'<figcaption>{escape(img["caption"])}</figcaption>' if img.get("caption") else ""
    return f"""
  <figure class="content-page__hero">
    <img src="{escape(img['src'])}" alt="{escape(img.get('alt', ''))}" loading="lazy">
{cap}
  </figure>"""


def _takeaways(items):
    if not items:
        return ""
    lis = "\n".join(f'      <li>{escape(t)}</li>' for t in items)
    return f"""
  <div class="content-page__takeaways">
    <h2>Key takeaways</h2>
    <ul>{lis}
    </ul>
  </div>"""


def _toc(items):
    if len(items) < 3:
        return ""
    lis = "\n".join(f'      <li><a href="#{a}">{escape(t)}</a></li>' for a, t in items)
    return f"""
  <nav class="content-page__toc" aria-label="On this page">
    <h2>On this page</h2>
    <ul>{lis}
    </ul>
  </nav>"""


def _inline_cta(cta):
    return f"""
    <div class="content-page__cta">
      <h3>{escape(cta['heading'])}</h3>
      <p>{escape(cta.get('body', ''))}</p>
      <a class="btn btn--dark" href="{escape(cta['href'])}" data-gate-open>{escape(cta.get('button_label', 'Get started'))}</a>
    </div>"""


_CALC_TITLES = {c["slug"]: c["title"] for c in CALCULATORS}


def _calc_link_label(url):
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    return _CALC_TITLES.get(slug, slug.replace("-", " ").capitalize())


def _calculators(pack):
    """Standing founder rule: every profession/specialty page ships its related
    calculator. Existing calculators embed via iframe (?embed=1); new_build
    primaries render their related links until the build ships. The block
    always carries the book-a-call CTA (opens the gate popup)."""
    calc = pack.get("calculators")
    if not calc:
        return ""
    prim = calc.get("primary") or {}
    embed_url = ""
    if prim.get("type") == "existing":
        embed_url = prim.get("url") or ("/calculators/%s/" % prim["slug"] if prim.get("slug") else "")
        if embed_url.startswith("/"):
            embed_url = "https://www.valorahq.com" + embed_url
    name = prim.get("name") or (_calc_link_label(embed_url) if embed_url else "Calculator")
    iframe = ""
    if embed_url:
        iframe = (f'<iframe src="{escape(embed_url)}?embed=1" loading="lazy" '
                  f'title="{escape(name)}" data-calc-embed></iframe>')
    links = "".join(
        f'<li><a href="{escape(u)}">{escape(_calc_link_label(u))}</a></li>'
        for u in (calc.get("related_links") or [])
    )
    links_html = (f'<div class="calc-block__links">Related calculators:<ul>{links}</ul></div>'
                  if links else "")
    return f"""
<aside class="calc-block" id="calculator">
  <p class="calc-block__eyebrow">Calculator</p>
  <h3 class="calc-block__title">Try it: {escape(name)}</h3>
  <p class="calc-block__sub">Illustrative estimates only - your real numbers depend on your full picture.</p>
  {iframe}
  {links_html}
  <p class="calc-block__cta"><a class="btn btn--dark" href="/#contact" data-gate-open>Book a call with an advisor</a></p>
</aside>"""


def _team_extended(pack, body_html):
    """Grouped extended-team roster (extended_team array: name, title, grouping,
    order, avatar). Replaces the flat roster blocks after h2 'The team' with the
    grouped presentation; each member renders like the core-10 member blocks."""
    et = pack.get("extended_team")
    if not et:
        return None
    # Founder direction Sep 28: hide the Founder block for now. The entry and
    # avatar stay in the pack/assets; delete this filter to restore.
    et = [e for e in et if e.get("grouping") != "Founder"]
    groups = []
    for e in et:
        if e["grouping"] not in groups:
            groups.append(e["grouping"])
    out = []
    for g in groups:
        out.append(f'<h3 class="team-group">{escape(g)}</h3>')
        members = sorted((e for e in et if e["grouping"] == g), key=lambda e: e.get("order", 999))
        for e in members:
            avatar_file = e.get("avatar")
            if avatar_file:
                stem = avatar_file.rsplit(".", 1)[0]
                img = (f'<img class="team-member__avatar" src="/assets/{escape(stem)}.jpg" '
                       f'alt="Illustrated avatar of {escape(e["name"])}" loading="lazy" width="72" height="72">')
            else:
                # role-card style (founder direction Sep 28): no headshot, initials tile
                initials = "".join(w[0] for w in e["name"].split()[:2]).upper()
                img = (f'<div class="team-member__avatar team-member__avatar--initials" aria-hidden="true" '
                       f'style="width:72px;height:72px;border-radius:50%;background:var(--green,#1d4d3a);color:#fff;'
                       f'display:flex;align-items:center;justify-content:center;font-weight:600;font-size:24px;">'
                       f'{escape(initials)}</div>')
            paras = e.get("bio_paragraphs") or ([e["bio"]] if e.get("bio") else [])
            bio = "".join(f'<p>{escape(p)}</p>' for p in paras)
            out.append(
                f'<div class="team-member">{img}'
                f'<div class="team-member__text"><h3>{escape(e["name"])}</h3>'
                f'<p class="team-member__role">{escape(e["title"])}</p>{bio}</div></div>')
    # keep everything through the closing </h2> of "The team", drop the old roster
    m = re.search(r"<h2[^>]*>\s*The team\s*</h2>", body_html, flags=re.I)
    if not m:
        return None
    return body_html[:m.end()] + "\n" + "\n".join(out)


def _team_avatars(pack, body_html):
    """Circular headshots beside each member block (avatars map: name -> filename)."""
    avatars = pack.get("avatars")
    if not avatars:
        return body_html
    def repl(m):
        name, rest = m.group(1), m.group(2)
        fname = avatars.get(name)
        if not fname:
            return m.group(0)
        src = "/assets/" + fname.rsplit(".", 1)[0] + ".jpg"
        return (f'<div class="team-member"><img class="team-member__avatar" src="{src}" '
                f'alt="Illustrated avatar of {escape(name)}" loading="lazy" width="72" height="72">'
                f'<div class="team-member__text"><h3>{escape(name)}{rest}</h3>')
    out = re.sub(r"<h3>(\w+)((?:\s|&ndash;|-)[^<]*)</h3>", repl, body_html)
    # close the wrapper div after each member's paragraph(s): the transform above
    # opened <div class="team-member__text"> in place of each h3; close before the
    # next team-member or at the end of the roster (last </p> of each block).
    parts = out.split('<div class="team-member">')
    if len(parts) > 1:
        rebuilt = parts[0]
        for i, chunk in enumerate(parts[1:]):
            if i < len(parts) - 2:
                nxt = chunk  # ends right before the next member's wrapper
                cut = nxt.rfind("</p>")
                chunk = nxt[:cut + 4] + "</div></div>" + nxt[cut + 4:]
            else:
                cut = chunk.rfind("</p>")
                chunk = chunk[:cut + 4] + "</div></div>" + chunk[cut + 4:]
            rebuilt += '<div class="team-member">' + chunk
        out = rebuilt
    return out


def _process_body(pack):
    """Add h2 anchor ids, inject inline CTAs at the end of their named sections.
    Returns (processed_html, toc_items)."""
    html = pack["body_html"]
    ctas = {}
    for c in (pack.get("inline_ctas") or []):
        ctas[c["after_h2"].strip().lower()] = c
    parts = re.split(r"(<h2[^>]*>.*?</h2>)", html, flags=re.S | re.I)
    out = [parts[0]]
    toc = []
    matched = set()
    it = parts[1:]
    for i in range(0, len(it), 2):
        h2tag = it[i]
        section = it[i + 1] if i + 1 < len(it) else ""
        text = re.sub(r"<[^>]+>", "", h2tag).strip()
        anchor = _slugify(text)
        toc.append((anchor, text))
        out.append(re.sub(r"<h2", f'<h2 id="{anchor}"', h2tag, count=1))
        out.append(section)
        cta = ctas.get(text.lower())
        if cta:
            out.append(_inline_cta(cta))
            matched.add(text.lower())
    for key in ctas:
        if key not in matched:
            print(f"WARNING: inline_cta target '{key}' not found in {pack['slug']} body h2s - dropped")
    body = "".join(out)
    calc_block = _calculators(pack)
    if calc_block:
        # mid-content: insert before the h2 that starts the second half
        h2_pos = [m.start() for m in re.finditer(r"<h2[ >]", body)]
        if len(h2_pos) >= 3:
            at = h2_pos[len(h2_pos) // 2]
            body = body[:at] + calc_block + body[at:]
        else:
            body += calc_block
    return body, toc


def load_packs():
    packs = []
    for path in sorted(glob.glob(os.path.join(PACK_DIR, "*.json"))):
        with open(path, encoding="utf-8") as f:
            pack = json.load(f)
        if "h1" not in pack and "title" in pack:
            pack["h1"] = pack["title"]  # legal packs use 'title'
        pack.setdefault("faqs", [])     # legal packs carry no FAQs by design
        for key in ("slug", "meta_title", "meta_description", "h1", "body_html"):
            if key not in pack:
                raise SystemExit(f"content pack {path} is missing '{key}'")
        pack["_path"] = path
        pack["_draft"] = pack.get("status", "approved") == "draft"
        # Drafts render with noindex and stay out of sitemap/llms registration.
        packs.append(pack)
    return packs


def _link_label(url):
    """Readable label from a URL slug: 'financial-advisor-for-tech-employees' -> 'Financial advisor for tech employees'."""
    slug = url.rstrip("/").rsplit("/", 1)[-1] or url
    words = slug.replace("-", " ").replace("_", " ")
    return words[:1].upper() + words[1:] if words else url


def _related(links):
    # Founder direction Sep 28: only cross-link client (niche) pages here -
    # never advisor-facing content (blog, for-advisors pages).
    real = [l for l in (links or [])
            if isinstance(l, str) and l.startswith("https://www.valorahq.com/financial-advisor-for-")]
    if not real:
        return ""
    cards = "\n".join(
        f'      <a class="content-page__related-card" href="{escape(l)}">'
        f'<span>{escape(_link_label(l))}</span>'
        f'<span class="content-page__related-arrow" aria-hidden="true">&rarr;</span></a>'
        for l in real)
    return f"""
  <div class="content-page__related">
    <h5>Related guides</h5>
    <div class="content-page__related-grid">
{cards}
    </div>
  </div>"""


def _cta(pack):
    cta = pack.get("cta")
    if not cta or not cta.get("href"):
        return contact_section()
    return f"""
<section class="section section--green cta">
  <div class="container" style="max-width:680px; text-align:center;">
    <h2 class="display display--md">{escape(cta.get('heading', 'Ready to take the next step?'))}</h2>
    <p style="margin:16px 0 28px;">{escape(cta.get('body', ''))}</p>
    <a class="btn btn--light" href="{escape(cta['href'])}">{escape(cta.get('button_label', 'Get started'))}</a>
  </div>
</section>
"""


def _closing(pack, faq_pairs, is_legal):
    """FAQ section (content pages) + closing CTA (skipped on legal pages)."""
    out = ""
    if faq_pairs:
        out += f"""
<section class="section section--paper" id="faq">
  <div class="container" style="max-width:700px;">
{faq_block(faq_pairs)}
  </div>
</section>
"""
    if not is_legal:
        out += _cta(pack)
    return out


def _body(pack):
    label = PAGE_TYPE_LABELS.get(pack.get("page_type", ""), "Guide")
    faq_pairs = [(f["q"], f["a"]) for f in pack["faqs"]]
    is_legal = pack.get("page_type") in ("legal", "team")  # plain render, no closing CTA
    body_html, toc_items = _process_body(pack)
    extended = _team_extended(pack, body_html)
    body_html = extended if extended is not None else _team_avatars(pack, body_html)
    middle = _takeaways(pack.get("key_takeaways"))
    if pack.get("toc", True):
        middle += _toc(toc_items)
    # takeaways + TOC land after the intro paragraph (first </p>) when there is one
    first_close = body_html.find("</p>")
    if first_close != -1 and middle:
        cut = first_close + len("</p>")
        body_html = body_html[:cut] + middle + body_html[cut:]
    else:
        body_html = middle + body_html
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:700px;">
    <p class="eyebrow reveal">{escape(label)}</p>
    <h1 class="display display--lg reveal">{escape(pack['h1'])}</h1>
{_tags(pack.get('tags'))}
{_hero(pack.get('feature_image'))}
    <div class="insights-article" style="margin-top:32px;">
{body_html}
    </div>
{_related(pack.get('internal_links'))}
  </div>
</section>

{_closing(pack, faq_pairs, is_legal)}
"""


def render(pack):
    faq_pairs = [(f["q"], f["a"]) for f in pack["faqs"]]
    return page(
        head(pack["meta_title"], pack["meta_description"],
             path=f"/{pack['slug']}/", schema=faq_schema(faq_pairs) if faq_pairs else "",
             keywords=list(dict.fromkeys((pack.get("keywords") or []) + (pack.get("tags") or []))),
             noindex=pack.get("_draft", False)),
        _body(pack),
        with_gate=True,
    )


def build_content_pages(write_fn):
    """Renders every pack. Returns [(path, description)] for sitemap/llms registration."""
    from city_validate import validate_pack  # fail-closed contract, Lena city-template v2
    packs = load_packs()
    city_packs = [p for p in packs if p.get("page_type") == "niche-city"]
    for pack in city_packs:
        # Render-time gate: a bad pack can never reach the site. offline=True -
        # URL liveness ran pre-handoff (city_validate CLI); warns never fail.
        fails, _ = validate_pack(pack["_path"], pack, other_packs=city_packs, offline=True)
        if fails:
            raise SystemExit(
                f"city pack FAILS validation, refusing to render: {pack['_path']}\n"
                + "\n".join(f"  - {f}" for f in fails))
    built = []
    for pack in packs:
        write_fn(f"/{pack['slug']}/", render(pack))
        if not pack.get("_draft", False):
            built.append((f"/{pack['slug']}/", pack["meta_description"]))
    return built
