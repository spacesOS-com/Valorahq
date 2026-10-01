"""Explicit noindex placeholders for linked pages, without advisor directory content."""
from pathlib import Path
from partials import head, page, escape

PLACEHOLDERS = [('/find-a-financial-advisor/new-york/', 'New York, NY'), ('/find-a-financial-advisor/los-angeles/', 'Los Angeles, CA'), ('/find-a-financial-advisor/chicago/', 'Chicago, IL'), ('/find-a-financial-advisor/dallas/', 'Dallas, TX'), ('/find-a-financial-advisor/houston/', 'Houston, TX'), ('/find-a-financial-advisor/managing-investments/', 'Managing investments'), ('/find-a-financial-advisor/retirement-planning/', 'Retirement planning'), ('/find-a-financial-advisor/selling-a-business/', 'Selling a business'), ('/find-a-financial-advisor/business-owner-wealth-planning/', 'Business owner wealth planning'), ('/find-a-financial-advisor/tax-planning/', 'Tax planning'), ('/find-a-financial-advisor/business-owner/', 'Business owner'), ('/find-a-financial-advisor/executive-professional/', 'Executive / professional'), ('/find-a-financial-advisor/retired/', 'Retired'), ('/find-a-financial-advisor/recently-sold-a-business/', 'Recently sold a business'), ('/find-a-financial-advisor/recently-received-an-inheritance/', 'Recently received an inheritance'), ('/find-a-financial-advisor/under-250k/', 'Under $250K'), ('/find-a-financial-advisor/250k-to-500k/', '$250K to $500K'), ('/find-a-financial-advisor/500k-to-1m/', '$500K to $1M'), ('/find-a-financial-advisor/1m-to-3m/', '$1M to $3M'), ('/find-a-financial-advisor/3m-to-10m/', '$3M to $10M'), ('/find-a-financial-advisor/10m-plus/', '$10M+'), ('/top-financial-advisors/arizona/', 'Arizona'), ('/top-financial-advisors/california/', 'California'), ('/top-financial-advisors/colorado/', 'Colorado'), ('/top-financial-advisors/district-of-columbia/', 'District of Columbia'), ('/top-financial-advisors/florida/', 'Florida'), ('/top-financial-advisors/', 'Advisors by state')]

def build_navigation_placeholders(write_fn, site_root):
    """Never overwrite a real page. Excluded from search catalogs by returning nothing."""
    for path, label in PLACEHOLDERS:
        target = Path(site_root) / path.strip("/") / "index.html"
        if target.exists() and "<!-- valora-navigation-placeholder -->" not in target.read_text(encoding="utf-8"):
            continue
        body = f'<!-- valora-navigation-placeholder --><section class="section section--paper"><div class="container" style="max-width:700px"><h1>{escape(label)}</h1><p>This page is being prepared.</p></div></section>'
        write_fn(path, page(head(f"{label} | Valora", "This page is being prepared.", path=path, noindex=True), body))
