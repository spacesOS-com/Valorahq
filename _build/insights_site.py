# -*- coding: utf-8 -*-
"""Static site for insights.spacesos.com: the advisor articles published from the CMS.

Reads _build/insights-articles/*.json (written by the CMS on publish) and writes a
self-contained site to /_insights-site/: an index, one page per article, an RSS feed at
/rss/ (the same address Ghost used, so existing subscribers and the for-advisors page keep
working), sitemap.xml and robots.txt. Point the insights.spacesos.com app at that folder.

No tracking scripts and no dependency on valorahq.com's stylesheet.
"""
import glob
import json
import os
from email.utils import format_datetime
from datetime import datetime, timezone
from html import escape
from xml.sax.saxutils import escape as xml_escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_build", "insights-articles")
OUT = os.path.join(ROOT, "_insights-site")
SITE = os.environ.get("INSIGHTS_SITE_URL", "https://insights.spacesos.com")
NAME = "Valora Insights"
TAGLINE = "Practical articles for independent financial advisors."

CSS = """:root{--green:#1e3b2a;--ink:#16190f;--soft:#3b4034;--muted:#767a6c;--line:rgba(22,25,15,.14);--paper:#f7f5f0;--tint:#dceceb}
*{box-sizing:border-box}body{margin:0;font:17px/1.7 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper)}
a{color:var(--green)}img{max-width:100%;height:auto;display:block}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}.wide{max-width:1120px}
header.site{background:#fff;border-bottom:1px solid var(--line)}header.site .wrap{display:flex;justify-content:space-between;align-items:center;padding-top:18px;padding-bottom:18px}
header.site a{font-weight:600;text-decoration:none;color:var(--ink);font-size:1.15rem}header.site nav a{font-size:.9rem;font-weight:500;color:var(--soft);margin-left:20px}
h1{font-size:clamp(1.9rem,4.4vw,2.8rem);line-height:1.15;letter-spacing:-.02em;margin:48px 0 14px}
h2{font-size:1.45rem;line-height:1.3;letter-spacing:-.01em;margin:40px 0 10px}h3{font-size:1.15rem;margin:28px 0 8px}
.meta{color:var(--muted);font-size:.9rem;margin-bottom:28px}.lede{font-size:1.15rem;color:var(--soft)}
figure{margin:0 0 32px}figure img{border-radius:14px;border:1px solid var(--line);width:100%}
article p,article ul,article ol,article table,article blockquote{margin:0 0 18px}article ul,article ol{padding-left:24px}
article table{border-collapse:collapse;width:100%;font-size:.95rem}article th,article td{border:1px solid var(--line);padding:8px 12px;text-align:left}
blockquote{border-left:3px solid var(--green);padding-left:16px;color:var(--soft)}
.takeaways{background:var(--tint);border-radius:14px;padding:20px 24px;margin:0 0 28px}.takeaways h2{margin:0 0 8px;font-size:1.05rem}.takeaways ul{margin:0;padding-left:20px}
.faq details{border-top:1px solid var(--line);padding:14px 0}.faq summary{font-weight:600;cursor:pointer}.faq p{margin:10px 0 0;color:var(--soft)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px;margin:32px 0 64px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;text-decoration:none;color:inherit}
.card img{aspect-ratio:16/9;object-fit:cover}.card div{padding:18px 20px 22px}.card h2{font-size:1.1rem;margin:6px 0 8px}.card p{margin:0;font-size:.92rem;color:var(--soft);line-height:1.55}
.card small{color:var(--muted);font-size:.78rem;letter-spacing:.06em;text-transform:uppercase}
footer.site{border-top:1px solid var(--line);margin-top:72px;padding:28px 0;color:var(--muted);font-size:.85rem}
"""


def load_articles():
    items = []
    for path in sorted(glob.glob(os.path.join(SRC, "*.json"))):
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        for key in ("slug", "meta_title", "meta_description", "h1", "body_html"):
            if key not in doc:
                raise SystemExit(f"insights article {path} is missing '{key}'")
        doc.setdefault("faqs", [])
        doc.setdefault("cms", {})
        items.append(doc)
    items.sort(key=lambda d: d["cms"].get("published_at", ""), reverse=True)
    return items


def _date(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def _json_ld(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def _shell(title, description, canonical, body, extra_head="", noindex=False):
    robots = '<meta name="robots" content="noindex,follow">\n' if noindex else ""
    return f"""<!DOCTYPE html>
<html lang="en-US"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
{robots}<link rel="canonical" href="{escape(canonical)}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="{SITE}/rss/">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
{extra_head}
</head><body>
<header class="site"><div class="wrap wide"><a href="/">{NAME}</a><nav><a href="/rss/">RSS</a><a href="https://www.valorahq.com/for-advisors/">For advisors</a></nav></div></header>
{body}
<footer class="site"><div class="wrap wide">{NAME}. {TAGLINE} Educational content only; not investment, tax or legal advice.</div></footer>
</body></html>"""


def render_article(doc):
    cms = doc.get("cms", {})
    url = cms.get("canonical") or f"{SITE}/{doc['slug']}/"
    published = _date(cms.get("published_at", ""))
    author = cms.get("author_persona") or NAME
    img = doc.get("feature_image") or {}
    og_image = cms.get("og_image") or img.get("src", "")
    hero = f'<figure><img src="{escape(img["src"])}" alt="{escape(img.get("alt", ""))}"></figure>' if img.get("src") else ""
    takeaways = ""
    if doc.get("key_takeaways"):
        takeaways = '<aside class="takeaways"><h2>Key takeaways</h2><ul>' + "".join(f"<li>{escape(t)}</li>" for t in doc["key_takeaways"]) + "</ul></aside>"
    faq = ""
    if doc["faqs"]:
        faq = '<section class="faq"><h2>Frequently asked questions</h2>' + "".join(
            f'<details><summary>{escape(f["q"])}</summary><p>{escape(f["a"])}</p></details>' for f in doc["faqs"]) + "</section>"
    schema = [{"@context": "https://schema.org", "@type": "Article", "headline": doc["h1"], "description": doc["meta_description"],
               "datePublished": published.isoformat(), "dateModified": cms.get("updated_at") or published.isoformat(),
               "author": {"@type": "Person", "name": author}, "publisher": {"@type": "Organization", "name": "Valora"},
               "mainEntityOfPage": url, **({"image": og_image} if og_image else {})}]
    if doc["faqs"]:
        schema.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in doc["faqs"]]})
    if isinstance(cms.get("structured_data"), dict) and cms["structured_data"].get("@type"):
        schema.append(cms["structured_data"])
    head = "\n".join(_json_ld(s) for s in schema)
    head += f'\n<meta property="og:type" content="article"><meta property="og:title" content="{escape(doc["meta_title"])}">'
    head += f'<meta property="og:description" content="{escape(doc["meta_description"])}"><meta property="og:url" content="{escape(url)}">'
    if og_image:
        head += f'<meta property="og:image" content="{escape(og_image)}"><meta name="twitter:card" content="summary_large_image">'
    body = f"""<main class="wrap"><article>
<h1>{escape(doc['h1'])}</h1>
<p class="meta">By {escape(author)} · {published.strftime('%b %-d, %Y')}</p>
{hero}
{takeaways}
{doc['body_html']}
{faq}
</article></main>"""
    return _shell(doc["meta_title"], doc["meta_description"], url, body, head, noindex=doc.get("status") == "draft")


def render_index(articles):
    cards = []
    for doc in articles:
        img = (doc.get("feature_image") or {}).get("src")
        pic = f'<img src="{escape(img)}" alt="" loading="lazy">' if img else ""
        date = _date(doc["cms"].get("published_at", "")).strftime("%b %-d, %Y")
        cards.append(f'<a class="card" href="/{escape(doc["slug"])}/">{pic}<div><small>{date}</small><h2>{escape(doc["h1"])}</h2><p>{escape(doc["meta_description"])}</p></div></a>')
    empty = "" if cards else '<p class="lede">New articles are on their way.</p>'
    body = f'<main class="wrap wide"><h1>{NAME}</h1><p class="lede">{TAGLINE}</p>{empty}<div class="grid">{"".join(cards)}</div></main>'
    return _shell(NAME, TAGLINE, SITE + "/", body)


def render_rss(articles):
    items = []
    for doc in articles[:30]:
        url = f"{SITE}/{doc['slug']}/"
        img = (doc.get("feature_image") or {}).get("src")
        media = f'<media:content url="{xml_escape(img)}" medium="image"/>' if img else ""
        items.append(f"""<item><title><![CDATA[{doc['h1']}]]></title><description><![CDATA[{doc['meta_description']}]]></description>
<link>{xml_escape(url)}</link><guid isPermaLink="true">{xml_escape(url)}</guid>
<dc:creator><![CDATA[{doc['cms'].get('author_persona') or NAME}]]></dc:creator>
<pubDate>{format_datetime(_date(doc['cms'].get('published_at', '')))}</pubDate>{media}</item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/" version="2.0">
<channel><title><![CDATA[{NAME}]]></title><description><![CDATA[{TAGLINE}]]></description><link>{SITE}/</link>
<atom:link href="{SITE}/rss/" rel="self" type="application/rss+xml"/>
{''.join(items)}
</channel></rss>
"""


def build_insights_site():
    articles = load_articles()
    public = [a for a in articles if a.get("status") != "draft"]

    def write(rel, text):
        out = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    write("styles.css", CSS)
    write("index.html", render_index(public))
    for doc in articles:
        write(os.path.join(doc["slug"], "index.html"), render_article(doc))
    write(os.path.join("rss", "index.xml"), render_rss(public))
    write("rss.xml", render_rss(public))
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    urls = "".join(f"<url><loc>{xml_escape(SITE)}/{xml_escape(a['slug'])}/</loc><lastmod>{_date(a['cms'].get('updated_at') or a['cms'].get('published_at', '')).date().isoformat()}</lastmod></url>" for a in public)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE}/</loc></url>{urls}</urlset>\n')
    return len(public)


if __name__ == "__main__":
    print("insights articles:", build_insights_site())
