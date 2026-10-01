"""Educational business-owner navigation page, separate from the held roster."""
import json
from pathlib import Path
from content_pages import _body
from partials import head, page, faq_schema

# Owner-only indexing decision. Set False to roll back both renderer and sitemap.
# Bound reviews/owner approval are recorded in business-owner-indexing-eligibility.json.
BUSINESS_OWNER_INDEXABLE = True
BUSINESS_OWNER_PATH = '/find-a-financial-advisor/business-owner/'


def build_business_owner_page(write_fn):
    pack=json.loads((Path(__file__).parent/'content-packs/business-owner-advisor-fit.pagepack').read_text(encoding='utf-8'))
    pairs=[(f['q'],f['a']) for f in pack['faqs']]
    markup=page(head(pack['meta_title'],pack['meta_description'],path='/find-a-financial-advisor/business-owner/',noindex=not BUSINESS_OWNER_INDEXABLE,schema=faq_schema(pairs),social_image='/assets/owner-fit/hero.jpg',social_image_alt='Illustration of a business owner reviewing business and household financial planning documents.',social_type='article'),_body(pack),with_gate=False)
    markup=markup.replace('</head>', '<style>.owner-fit-figure{margin:40px 0}.owner-fit-figure figcaption{font-size:14px;line-height:1.6;margin-top:12px}.insights-article ol{list-style:decimal;padding-left:24px}.insights-article ol li{margin:10px 0}.owner-worksheet{padding:24px;border:1px solid #d5d6cc;border-radius:12px;margin:30px 0}.owner-worksheet h3{margin-top:0}</style></head>')
    write_fn('/find-a-financial-advisor/business-owner/',markup)
