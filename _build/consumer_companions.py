"""Reviewed companion content only. Calculator tool and eligibility note untouched."""
import os,json,re
from html import escape

def apply_consumer_companions(root):
    source=os.path.join(root,'_build','consumer-companions','roth-ira-growth')
    with open(os.path.join(source,'roth-ira-growth.pagepack'),encoding='utf-8') as f: pack=json.load(f)
    with open(os.path.join(source,'faq-schema.json'),encoding='utf-8') as f: schema=json.load(f)
    with open(os.path.join(source,'faq-visible.html'),encoding='utf-8') as f: faq=f.read()
    body=pack['body_html'].replace('href="/find-your-advisor/"','href="/#contact"')
    c=pack['cta']
    end='<aside class="worksheet content-cta"><h2>'+escape(c['heading'])+'</h2><p>'+escape(c['body'])+'</p><a href="/#contact" data-content-event="content_cta_click" data-content-page="roth-ira-growth" data-content-placement="end" data-content-destination="inquiry">'+escape(c['button_label'])+'</a></aside>'
    replacement='<div class="insights-article consumer-companion" style="margin-top:clamp(40px,6vw,72px);max-width:68ch;">\n'+body+'\n<div class="faq">'+faq+'</div>\n'+end+'</div>'
    path=os.path.join(root,'calculators','roth-ira-growth','index.html')
    with open(path,encoding='utf-8') as f: html=f.read()
    start=html.index('<div class="insights-article')
    stop=html.index('\n  </div>\n</section>\n\n<script>',start)
    html=html[:start]+replacement+html[stop:]
    count=0
    def schema_replace(m):
        nonlocal count
        obj=json.loads(m.group(1))
        if obj.get('@type')=='FAQPage':count+=1;return '<script type="application/ld+json">'+json.dumps(schema,separators=(',',':')).replace('<','\\u003c')+'</script>'
        return m.group(0)
    html=re.sub(r'<script type="application/ld\+json">(.*?)</script>',schema_replace,html,flags=re.S)
    if count!=1:raise ValueError('Expected exactly one FAQPage schema')
    html=html.replace('</head>','<meta name="robots" content="noindex,follow"><link rel="stylesheet" href="/assets/roth-companion-layout.css"></head>')
    html=html.replace('</body>','<script src="/assets/consumer-companion-events.js"></script></body>')
    with open(path,'w',encoding='utf-8') as f:f.write(html)
