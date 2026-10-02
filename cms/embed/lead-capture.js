/* Valora CMS lead capture for a brand's website. Not loaded anywhere by default.

   <script src="/path/to/lead-capture.js" data-endpoint="https://www.valorahq.com/api/cms/public/leads" data-lead-key="vlead_…"></script>

   It remembers which pages were viewed in this browser tab (sessionStorage only: no cookies,
   nothing sent until a lead is submitted) and exposes:

     ValoraLeads.send({ name, email, phone, company, action: 'contact', message }).then(ok => …)

   Review with whoever owns the site's privacy notice before switching it on: the page history
   is sent with the lead. */
(function () {
  'use strict';
  var script = document.currentScript, endpoint = script && script.dataset.endpoint, key = script && script.dataset.leadKey, KEY = 'valora_journey';
  if (!endpoint || !key) return;
  function read() { try { return JSON.parse(sessionStorage.getItem(KEY) || '[]'); } catch (_) { return []; } }
  function add(event) {
    try { var j = read(); j.push({ at: new Date().toISOString(), path: location.pathname, event: event }); sessionStorage.setItem(KEY, JSON.stringify(j.slice(-40))); } catch (_) { /* storage unavailable: send without history */ }
  }
  add('view');
  var params = new URLSearchParams(location.search), utm = { referrer: document.referrer ? new URL(document.referrer).hostname : '' };
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'].forEach(function (k) { if (params.get(k)) utm[k] = params.get(k); });
  window.ValoraLeads = {
    send: function (lead) {
      add('submit_form');
      var body = Object.assign({}, lead, { lead_key: key, source_page: location.pathname, journey: read(), utm: utm });
      return fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(function (r) { return r.ok; }).catch(function () { return false; });
    }
  };
})();
