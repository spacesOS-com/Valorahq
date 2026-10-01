"""Scoped exact-pack render. Does not rebuild unrelated pages or index draft."""
import copy,hashlib,json,os,re
from content_pages import render
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK=os.path.join(ROOT,'_build/content-packs/selling-a-business.pagepack')
EXPECTED='9050a33759d1e4018c138204425be6b01e68e53af8300adf0d991a4b57f755fa'
def build():
    raw=open(PACK,'rb').read()
    if hashlib.sha256(raw).hexdigest()!=EXPECTED:raise ValueError('Unreviewed content revision')
    source=json.loads(raw);pack=copy.deepcopy(source);pack['_draft']=True
    # Source body already contains the same four takeaways. Render once only.
    if 'class="worksheet key-takeaways"' in pack['body_html']:pack['key_takeaways']=[]
    html=render(pack)
    image=source['feature_image']
    needle='<img src="'+image['src']+'" alt="'+image['alt']+'" loading="lazy">'
    if html.count(needle)!=1:raise ValueError('Ambiguous hero')
    html=html.replace(needle,'<picture><source media="(max-width:600px)" srcset="'+image['mobile_src']+'">'+needle+'</picture>')
    # Privacy scope: no inherited visitor-identification/analytics loaders.
    html=re.sub(r'<script\b[^>]*>.*?</script>',lambda m:'' if any(marker in m[0] for marker in ('posthog.init(', 'window.reb2b', 'ddwl4m2hdecbv.cloudfront.net')) else m[0],html,flags=re.S|re.I)
    if any(marker in html.lower() for marker in ('posthog.init(', 'window.reb2b', 'ddwl4m2hdecbv.cloudfront.net')):raise ValueError('Vendor loader remains')
    # Keep sibling holds in inherited navigation/footer on this exact page only.
    html=re.sub(r'<li><a href="/find-a-financial-advisor/business-owner-wealth-planning/">.*?</a></li>','',html,flags=re.S)
    # Add tracking metadata without changing href/visible passed copy.
    needle='<a class="btn btn--light" href="/find-your-advisor/">'
    if html.count(needle)!=1:raise ValueError('Ambiguous end CTA')
    html=html.replace(needle,needle[:-1]+' data-content-event="content_cta_click" data-content-page="selling-a-business" data-content-placement="end" data-content-destination="inquiry">')
    html=html.replace('</head>','</head>')
    html=html.replace('</body>','<script src="/assets/content-click-dispatch.js"></script></body>')
    path=os.path.join(ROOT,source['slug'],'index.html');os.makedirs(os.path.dirname(path),exist_ok=True)
    open(path,'w',encoding='utf-8').write(html)
if __name__=='__main__':build()
