/* Review-only dispatch seam. No network, visitor identifiers or storage.
 * A separately reviewed sink must subscribe to valora-content-event. */
(function(){
  'use strict';
  document.addEventListener('click',function(event){
    var link=event.target.closest && event.target.closest('a[data-content-event]');
    if(!link)return;
    var name=link.getAttribute('data-content-event');
    if(name!=='content_cta_click' && name!=='content_internal_link_click')return;
    var url;try{url=new URL(link.getAttribute('href'),location.href);}catch(_){return;}
    if(url.origin!==location.origin || url.search || url.hash)return;
    var page=link.getAttribute('data-content-page'),placement=link.getAttribute('data-content-placement');
    if(!['selling-a-business','business-owner-wealth-planning'].includes(page) || !['mid','body','end','shell'].includes(placement))return;
    document.dispatchEvent(new CustomEvent('valora-content-event',{detail:{name:name,page:page,placement:placement,destination:url.pathname}}));
  });
})();
