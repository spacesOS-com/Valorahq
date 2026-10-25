"""Educational business-owner navigation page, separate from the held roster.

The historical emission is indexable. That is not manifest eligibility.
business-owner-indexing-eligibility.json is an older note and is not consulted.
An empty indexing manifest leaves this emission unchanged. Exact-path rollback
in the manifest restores noindex and removes the sitemap entry. A full
dual-gate row indexes the page only when its artifact hash matches.
"""
import json
from pathlib import Path
from content_pages import _body
from indexing_eligibility import get_manifest, rendered_artifact_sha256, resolved_noindex
from partials import head, page, faq_schema

# Historical renderer request. Not an approval and not manifest eligibility.
BUSINESS_OWNER_INDEXABLE = True
BUSINESS_OWNER_PATH = '/find-a-financial-advisor/business-owner/'
_STYLE = '<style>.owner-fit-figure{margin:40px 0}.owner-fit-figure figcaption{font-size:14px;line-height:1.6;margin-top:12px}.insights-article ol{list-style:decimal;padding-left:24px}.insights-article ol li{margin:10px 0}.owner-worksheet{padding:24px;border:1px solid #d5d6cc;border-radius:12px;margin:30px 0}.owner-worksheet h3{margin-top:0}</style>'


def _pack():
    pack = json.loads((Path(__file__).parent / 'content-packs/business-owner-advisor-fit.pagepack').read_text(encoding='utf-8'))
    pairs = [(item['q'], item['a']) for item in pack['faqs']]
    return pack, pairs


def _render(noindex, eligibility):
    pack, pairs = _pack()
    markup = page(head(pack['meta_title'], pack['meta_description'], path=BUSINESS_OWNER_PATH, noindex=noindex, eligibility=eligibility, schema=faq_schema(pairs), social_image='/assets/owner-fit/hero.jpg', social_image_alt='Illustration of a business owner reviewing business and household financial planning documents.', social_type='article'), _body(pack), with_gate=False)
    return markup.replace('</head>', _STYLE + '</head>')


def _eligibility(manifest=None):
    manifest = manifest if manifest is not None else get_manifest()
    ctx = {
        "cohort": "educational",
        "presentation": "educational-guide",
        "implies_verified_specialists": False,
        "implies_matching": False,
    }
    if manifest.entry_for(BUSINESS_OWNER_PATH) is not None:
        # Hash the historical render with the manifest skipped. Robots markup
        # is removed by the hash, so a later noindex decision cannot stale itself.
        ctx["artifact_sha256"] = rendered_artifact_sha256(_render(not BUSINESS_OWNER_INDEXABLE, False))
    return ctx


def business_owner_decision(manifest=None):
    """Shared by the renderer and the sitemap."""
    manifest = manifest if manifest is not None else get_manifest()
    return resolved_noindex(BUSINESS_OWNER_PATH, not BUSINESS_OWNER_INDEXABLE, _eligibility(manifest), manifest)


def build_business_owner_page(write_fn):
    write_fn(BUSINESS_OWNER_PATH, _render(business_owner_decision(), False))
