# -*- coding: utf-8 -*-
"""Renders one unpublished CMS document with the real page templates, for the CMS preview.
stdin: {"type": "consumer-page" | "advisor-article", "doc": {...}}   stdout: the page HTML."""
import json
import sys

payload = json.load(sys.stdin)
doc = payload["doc"]
doc.setdefault("faqs", [])
if payload["type"] == "advisor-article":
    from insights_site import render_article
    html = render_article(doc).replace('href="/styles.css"', 'href="/api/cms/v1/preview-assets/insights.css"')
else:
    from content_pages import render
    doc["_draft"] = True
    html = render(doc)
banner = ('<div style="position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#9a6a00;color:#fff;'
          'font:600 13px/1 Inter,sans-serif;padding:10px 16px;text-align:center">Preview. Not published.</div>')
sys.stdout.write(html.replace("</body>", banner + "</body>", 1))
