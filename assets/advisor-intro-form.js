/* Advisor intro form on /for-advisors/. Posts through the same inquiry
   contract adapter and endpoint as the site-wide inquiry form; the firm
   details travel in the message field. */
(function(){'use strict';
  var form=document.querySelector('#advisorIntro');
  if(!form||!window.ValoraInquiryContractAdapter)return;
  var done=document.querySelector('#advisorIntroDone'),error=form.querySelector('.advx-form__error'),button=form.querySelector('button[type=submit]');
  var adapter=window.ValoraInquiryContractAdapter.create(async function(payload){
    var controller=new AbortController(),timer=setTimeout(function(){controller.abort()},20000);
    try{return await fetch(form.dataset.endpoint,{method:'POST',body:new URLSearchParams(payload),signal:controller.signal})}
    finally{clearTimeout(timer)}
  });
  var messages={first:'Enter your first name.',last:'Enter your last name.',email:'Enter a valid work email, for example name@yourfirm.com.',phone:'Enter a valid phone number. Include the country code if outside the US.',firm:'Enter your firm name.',website:'Enter a valid website, for example yourfirm.com.'};
  function clear(input){
    input.removeAttribute('aria-invalid');input.removeAttribute('aria-describedby');
    var old=input.closest('label').querySelector('.advx-form__field-err');if(old)old.remove();
  }
  function flag(input){
    clear(input);
    var note=document.createElement('span');note.className='advx-form__field-err';note.id='adv-err-'+input.name;note.setAttribute('role','alert');note.textContent=messages[input.name];
    input.setAttribute('aria-invalid','true');input.setAttribute('aria-describedby',note.id);input.closest('label').appendChild(note);
  }
  form.querySelectorAll('input').forEach(function(input){input.addEventListener('input',function(){clear(input);error.textContent=''})});
  form.addEventListener('submit',function(e){
    e.preventDefault();
    var v={},bad=[],phoneIntl='';
    form.querySelectorAll('input').forEach(function(input){
      v[input.name]=input.value.trim();
      var ok=input.checkValidity()&&(!input.required||v[input.name]);
      if(ok&&input.name==='phone'&&v.phone&&window.libphonenumber){
        var pn=window.libphonenumber.parsePhoneNumberFromString(v.phone,'US');
        ok=!!(pn&&pn.isValid());if(ok)phoneIntl=pn.formatInternational();
      }
      if(ok&&input.name==='website'&&v.website)ok=/^(https?:\/\/)?[a-z0-9-]+(\.[a-z0-9-]+)+(\/\S*)?$/i.test(v.website);
      if(ok)clear(input);else{flag(input);bad.push(input)}
    });
    if(bad.length){bad[0].focus();return}
    button.disabled=true;button.textContent='Sending…';error.textContent='';
    adapter.submit({firstName:v.first,lastName:v.last,email:v.email,phone:phoneIntl||v.phone,
      motivation:'[Advisor inquiry from /for-advisors/]\nFirm: '+v.firm+(v.website?'\nWebsite: '+v.website:''),
      reviewedNoticeAccepted:true}).then(function(result){
      if(result.kind==='inquiryAccepted'){
        if(window.ValoraLeads)window.ValoraLeads.send({name:v.first+' '+v.last,email:v.email,phone:phoneIntl||v.phone,company:v.firm,action:'advisor inquiry',details:{'Firm website':v.website}});
        form.hidden=true;done.hidden=false;done.focus();return}
      button.disabled=false;button.textContent=form.dataset.buttonLabel||'Get started';
      error.textContent=result.kind==='retryLater'?'Please wait before trying again.':result.kind==='invalid'?'Please check your details before sending.':'We could not confirm this request. Do not submit it again yet.';
    });
  });
})();
