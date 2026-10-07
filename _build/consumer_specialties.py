"""Render exact passed specialty packs with scoped release wiring and noindex."""
import os,json,glob,re
from html import escape
from content_pages import render

def apply_consumer_specialties(root):
    for source in glob.glob(os.path.join(root,'_build','consumer-specialties','*','*.pagepack')):
        with open(source,encoding='utf-8') as f:pack=json.load(f)
        slug=pack['slug'].split('/')[-1]
        pack['_draft']=True
        pack['body_html']=pack['body_html'].replace('href="/find-your-advisor/"','href="/#contact"')
        pack['cta']['href']='/#contact'
        html=render(pack)
        # Give the final CTA same exact metadata as reviewed inline CTA.
        pat=r'(<a class="btn btn--light" href="/#contact")>'
        html,count=re.subn(pat,lambda m:m.group(1)+' data-content-event="content_cta_click" data-content-page="'+slug+'" data-content-placement="end" data-content-destination="inquiry">',html)
        if count!=1:raise ValueError('Expected one closing CTA on '+slug)
        img=pack.get('feature_image',{})
        if img.get('mobile_src'):
            tag='<img src="'+escape(img['src'])+'" alt="'+escape(img.get('alt',''))+'" loading="lazy">'
            html=html.replace(tag,'<picture><source media="(max-width:600px)" srcset="'+escape(img['mobile_src'])+'">'+tag+'</picture>')
        html=html.replace('<div class="insights-article"','<div class="insights-article consumer-specialty"')
        html=html.replace('</head>','<link rel="stylesheet" href="/assets/consumer-specialty-layout.css"></head>')
        html=html.replace('</body>','<script src="/assets/consumer-companion-events.js"></script></body>')
        out=os.path.join(root,pack['slug'],'index.html');os.makedirs(os.path.dirname(out),exist_ok=True)
        with open(out,'w',encoding='utf-8') as f:f.write(html)
