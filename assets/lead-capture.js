/* Sends successful inquiries to the Valora CMS leads inbox.
   Loaded only when the site build is given a lead key (see lead_capture_include in _build/partials.py);
   another brand's site can load it the same way:

   <script src="lead-capture.js" data-endpoint="https://www.valorahq.com/api/cms/public/leads" data-lead-key="vlead_…"></script>

   It remembers which pages were viewed in this browser tab (sessionStorage only: no cookies, and
   nothing leaves the browser until the person submits a form) and exposes
   ValoraLeads.send({ name, email, phone, company, action, message, details }) and
   ValoraLeads.update(details) for answers given afterwards. The page history is sent
   with the lead, so the site's privacy notice should say so. */
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
  var ref = null;
  function post(body) { return fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); }
  window.ValoraLeads = {
    // lead: { name, email, phone, company, action, message, details: { "Question": "Answer" } }
    send: function (lead) {
      add('submit_form');
      var body = Object.assign({}, lead, { lead_key: key, source_page: location.pathname, journey: read(), utm: utm });
      return post(body).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) { ref = d && d.lead_ref; return Boolean(d); }).catch(function () { return false; });
    },
    // Answers given after the first submission (optional later steps) are added to the same lead.
    update: function (details, message) {
      if (!ref) return Promise.resolve(false);
      return post({ lead_key: key, lead_ref: ref, details: details, message: message || '' }).then(function (r) { return r.ok; }).catch(function () { return false; });
    }
  };
})();
