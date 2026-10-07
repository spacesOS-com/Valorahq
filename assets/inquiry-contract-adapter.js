/* Inquiry handler adapter. Requires confirmed success; no automatic retry. */
(function(root){'use strict';
 function create(transport){
  if(typeof transport!=='function')throw Error('Transport required');
  let busy=false,generation=0;
  return {submit:async function(draft){
   if(busy)return {kind:'busy'};
   const first=(draft.firstName||'').trim(),last=(draft.lastName||'').trim(),email=(draft.email||'').trim();
   if(!first||!last||!email)return {kind:'invalid'};
   const message=(draft.motivation||'').trim();if(message.length>1000)return {kind:'invalid'};
   const source=(draft.sourceChoice||'').trim();
   const payload={name:first+' '+last,email:email,phone:(draft.phone||'').trim(),assets:(draft.assetBand||'').trim(),message:message+(source?'\nHow they heard: '+source:'')};
   const g=generation;busy=true;
   try{
    const response=await transport(payload);if(g!==generation)return {kind:'cancelled'};
    if(response&&response.status===429)return {kind:'retryLater'};
    if(!response||response.ok!==true)return {kind:'unconfirmed'};
    const body=await response.json();if(g!==generation)return {kind:'cancelled'};
    if(body&&body.status==='success'&&body.dryRun!==true)return {kind:'inquiryAccepted',bookingConfirmed:false,dryRun:body.dryRun===true};
    if(body&&body.status==='error')return {kind:'invalid'};
    return {kind:'unconfirmed'};
   }catch(_){return g===generation?{kind:'unconfirmed'}:{kind:'cancelled'}}finally{if(g===generation)busy=false;}
  },reset:function(){generation++;busy=false;}};
 }
 if(typeof module!=='undefined'&&module.exports)module.exports={create:create};else root.ValoraInquiryContractAdapter={create:create};
})(typeof globalThis!=='undefined'?globalThis:this);
