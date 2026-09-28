# -*- coding: utf-8 -*-
"""Programmatic content pages rendered from Lena's JSON content packs.

One pack = one page at /<slug>/. Pack schema (keys):
  slug, page_type, meta_title (<=60), meta_description (<=155), keywords[],
  h1, body_html (unique grounded copy), faqs[{q,a}], faq_jsonld (reference
  only - the build regenerates JSON-LD from the visible faqs so they match
  by construction), internal_links[], source_notes[], optional cta
  {heading, body, button_label, href} (href placeholder until the consumer
  routing decision lands - default CTA is the site contact form).
"""
import glob
import json
import os

from partials import page, head, faq_schema, faq_block, contact_section, escape, BRAND

PACK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content-packs")

PAGE_TYPE_LABELS = {
    "niche-profession": "Profession",
    "city": "City",
    "life-event": "Life event",
    "asset-type": "Asset type",
    "employer": "Employer",
}


def load_packs():
    packs = []
    for path in sorted(glob.glob(os.path.join(PACK_DIR, "*.json"))):
        with open(path, encoding="utf-8") as f:
            pack = json.load(f)
        for key in ("slug", "meta_title", "meta_description", "h1", "body_html", "faqs"):
            if key not in pack:
                raise SystemExit(f"content pack {path} is missing '{key}'")
        pack["_draft"] = pack.get("status", "approved") == "draft"
        # PREVIEW BRANCH ONLY: drafts render with noindex so the founder can review them.
        packs.append(pack)
    return packs


def _related(links):
    real = [l for l in (links or []) if isinstance(l, str) and l.startswith("http")]
    if not real:
        return ""
    items = "\n".join(f'      <li><a href="{escape(l)}">{escape(l)}</a></li>' for l in real)
    return f"""
  <div class="content-page__related" style="margin-top:40px;">
    <h5 style="font-size:.7rem; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); margin-bottom:14px;">Related</h5>
    <ul style="list-style:none; padding:0;">{items}
    </ul>
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


def _body(pack):
    label = PAGE_TYPE_LABELS.get(pack.get("page_type", ""), "Guide")
    faq_pairs = [(f["q"], f["a"]) for f in pack["faqs"]]
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:700px;">
    <p class="eyebrow reveal">{escape(label)}</p>
    <h1 class="display display--lg reveal">{escape(pack['h1'])}</h1>
    <div class="insights-article" style="margin-top:32px;">
{pack['body_html']}
    </div>
{_related(pack.get('internal_links'))}
  </div>
</section>

<section class="section section--paper" id="faq">
  <div class="container" style="max-width:700px;">
{faq_block(faq_pairs)}
  </div>
</section>

{_cta(pack)}
"""


def render(pack):
    faq_pairs = [(f["q"], f["a"]) for f in pack["faqs"]]
    return page(
        head(pack["meta_title"], pack["meta_description"],
             path=f"/{pack['slug']}/", schema=faq_schema(faq_pairs),
             keywords=pack.get("keywords"), noindex=pack.get("_draft", False)),
        _body(pack),
    )


def build_content_pages(write_fn):
    """Renders every pack. Returns [(path, description)] for sitemap/llms registration."""
    built = []
    for pack in load_packs():
        write_fn(f"/{pack['slug']}/", render(pack))
        if not pack.get("_draft", False):
            built.append((f"/{pack['slug']}/", pack["meta_description"]))
    return built
