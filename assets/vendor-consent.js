/* Valora vendor consent.
   PostHog and RB2B stay inert until localStorage valora_vendor_consent_v1
   is exactly "granted". Anything else, including a missing or blocked
   store, is a deny. ?embed=1 never shows this notice and never treats a
   hidden notice as permission; it loads the tools only when that stored
   allow choice is readable. Revoke deletes the vendor scripts and the
   storage they added, then reloads so already-running vendor code stops.
   The page config is JSON, not an executable script. To port: replace the
   eager PostHog and RB2B script tags with #valora-vendor-config plus this file. */
(function () {
  'use strict';

  var STORAGE_KEY = 'valora_vendor_consent_v1';
  var POPUP_KEY = 'vz_gate_seen_v1';
  var KEEP = {};
  KEEP[STORAGE_KEY] = true;
  KEEP[POPUP_KEY] = true;

  if (window.__valoraVendorConsentBooted) return;
  window.__valoraVendorConsentBooted = true;

  var loaded = false;
  var storageBlocked = false;
  var baseline = null;

  function isVendorName(name) {
    if (!name || KEEP[name]) return false;
    return /(^ph_|__ph|posthog|reb2b|rb2b)/i.test(name);
  }

  function storeNames(store) {
    var names = [];
    if (!store) return names;
    try {
      for (var i = 0; i < store.length; i++) {
        var key = store.key(i);
        if (key) names.push(key);
      }
    } catch (e) {}
    return names;
  }

  function cookieNames() {
    var names = [];
    var raw = '';
    try { raw = document.cookie || ''; } catch (e) { return names; }
    raw.split(';').forEach(function (part) {
      var name = part.split('=')[0].trim();
      if (name) names.push(name);
    });
    return names;
  }

  function expireCookie(name) {
    var expires = '; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    document.cookie = name + '=' + expires;
    var host = '';
    try { host = window.location.hostname || ''; } catch (e) {}
    if (host && host !== 'localhost') {
      document.cookie = name + '=' + expires + '; domain=' + host;
      document.cookie = name + '=' + expires + '; domain=.' + host;
    }
  }

  function clearKnownVendorStorage() {
    [window.localStorage, window.sessionStorage].forEach(function (store) {
      storeNames(store).forEach(function (name) {
        if (!isVendorName(name)) return;
        try { store.removeItem(name); } catch (e) {}
      });
    });
    cookieNames().forEach(function (name) {
      if (isVendorName(name)) expireCookie(name);
    });
  }

  function rememberBaseline() {
    baseline = {
      local: storeNames(window.localStorage),
      session: storeNames(window.sessionStorage),
      cookies: cookieNames()
    };
  }

  function clearAddedSinceBaseline() {
    if (!baseline) return;
    function drop(store, before) {
      if (!store) return;
      storeNames(store).forEach(function (name) {
        if (!name || KEEP[name] || before.indexOf(name) !== -1) return;
        try { store.removeItem(name); } catch (e) {}
      });
    }
    drop(window.localStorage, baseline.local);
    drop(window.sessionStorage, baseline.session);
    cookieNames().forEach(function (name) {
      if (!KEEP[name] && baseline.cookies.indexOf(name) === -1) expireCookie(name);
    });
  }

  function readConsent() {
    try {
      var value = window.localStorage.getItem(STORAGE_KEY);
      if (value === 'granted' || value === 'denied') return value;
    } catch (e) {}
    return null;
  }

  function writeConsent(value) {
    try {
      window.localStorage.setItem(STORAGE_KEY, value);
      return window.localStorage.getItem(STORAGE_KEY) === value;
    } catch (e) {
      return false;
    }
  }

  function isEmbed() {
    try {
      return new URLSearchParams(window.location.search).get('embed') === '1';
    } catch (e) {
      return true;
    }
  }

  function readConfig() {
    var el = document.getElementById('valora-vendor-config');
    if (!el) return null;
    try {
      var data = JSON.parse(el.textContent || '');
      if (!data || !data.vendors || !data.vendors.length) return null;
      return data;
    } catch (e) {
      return null;
    }
  }

  function dispatchConsent(state) {
    try {
      document.dispatchEvent(new CustomEvent('valora:vendor-consent', { detail: { state: state } }));
    } catch (e) {}
  }

  function loadVendors() {
    if (loaded || readConsent() !== 'granted') return;
    var config = readConfig();
    if (!config) return;
    rememberBaseline();
    loaded = true;
    config.vendors.forEach(function (vendor) {
      if (!vendor || !vendor.snippet) return;
      var script = document.createElement('script');
      script.setAttribute('data-valora-vendor', vendor.id || 'vendor');
      script.text = vendor.snippet;
      (document.head || document.documentElement).appendChild(script);
    });
  }

  function stopVendors() {
    var nodes = document.querySelectorAll(
      'script[data-valora-vendor], script[src*="i.posthog.com"], script[src*="ddwl4m2hdecbv.cloudfront.net"]'
    );
    Array.prototype.forEach.call(nodes, function (node) {
      if (node.parentNode) node.parentNode.removeChild(node);
    });
    try { delete window.posthog; } catch (e) { window.posthog = undefined; }
    try { delete window.reb2b; } catch (e) { window.reb2b = undefined; }
    loaded = false;
  }

  function ensureStyles() {
    if (document.getElementById('valora-vendor-consent-style')) return;
    var style = document.createElement('style');
    style.id = 'valora-vendor-consent-style';
    style.textContent = [
      '.valora-vendor-consent{position:fixed;left:16px;right:16px;bottom:16px;z-index:400;display:flex;flex-wrap:wrap;gap:12px 16px;align-items:center;justify-content:space-between;max-width:880px;margin:0 auto;padding:14px 16px;background:#1e3b2a;color:#efebe0;border-radius:16px;box-shadow:0 12px 40px rgba(20,28,22,.28);font:15px/1.45 Inter,Arial,sans-serif}',
      '.valora-vendor-consent p{margin:0;flex:1 1 260px}',
      '.valora-vendor-consent a{color:#e8cc83}',
      '.valora-vendor-consent__actions{display:flex;flex-wrap:wrap;gap:8px}',
      '.valora-vendor-consent button{font:inherit;cursor:pointer;border-radius:999px;padding:8px 14px;border:1px solid transparent}',
      '.valora-vendor-consent button[data-valora-consent="grant"]{background:#efebe0;color:#1e3b2a}',
      '.valora-vendor-consent button[data-valora-consent="deny"]{background:transparent;color:#efebe0;border-color:#8aa394}',
      'body.embed-mode .valora-vendor-consent{display:none !important}',
      '@media (max-width:640px){.valora-vendor-consent{left:8px;right:8px;bottom:8px}}'
    ].join('');
    (document.head || document.documentElement).appendChild(style);
  }

  function addText(parent, text) {
    parent.appendChild(document.createTextNode(text));
  }

  function renderBanner() {
    var existing = document.getElementById('valora-vendor-consent');
    if (isEmbed() || !readConfig()) {
      if (existing && existing.parentNode) existing.parentNode.removeChild(existing);
      return;
    }
    ensureStyles();
    var root = existing;
    if (!root) {
      root = document.createElement('div');
      root.id = 'valora-vendor-consent';
      root.className = 'valora-vendor-consent';
      root.setAttribute('role', 'region');
      root.setAttribute('aria-label', 'Analytics consent');
      root.addEventListener('click', function (event) {
        var node = event.target;
        var action = null;
        while (node && node !== root) {
          if (node.getAttribute && node.getAttribute('data-valora-consent')) {
            action = node.getAttribute('data-valora-consent');
            break;
          }
          node = node.parentNode;
        }
        if (action === 'grant') grant();
        else if (action === 'deny') deny();
      });
      (document.body || document.documentElement).appendChild(root);
    }
    while (root.children.length) root.removeChild(root.children[0]);

    var state = readConsent();
    var copy = 'Analytics and visitor identification stay off until you allow them. ';
    if (state === 'granted') copy = 'Analytics and visitor identification are on for this browser. ';
    else if (state === 'denied') copy = 'Analytics and visitor identification stay off on this browser. ';
    var paragraph = document.createElement('p');
    addText(paragraph, copy);
    var link = document.createElement('a');
    link.href = '/cookies/';
    link.textContent = 'Cookie and Analytics Notice';
    paragraph.appendChild(link);
    addText(paragraph, '.');
    if (storageBlocked) {
      addText(paragraph, ' This browser blocked storage, so the tools stay off.');
    }
    root.appendChild(paragraph);

    var actions = document.createElement('div');
    actions.className = 'valora-vendor-consent__actions';
    if (state !== 'granted') {
      var allow = document.createElement('button');
      allow.type = 'button';
      allow.setAttribute('data-valora-consent', 'grant');
      allow.textContent = 'Allow';
      actions.appendChild(allow);
    }
    if (state !== 'denied') {
      var reject = document.createElement('button');
      reject.type = 'button';
      reject.setAttribute('data-valora-consent', 'deny');
      reject.textContent = state === 'granted' ? 'Turn off' : "Don't allow";
      actions.appendChild(reject);
    }
    root.appendChild(actions);
  }

  function grant() {
    if (!writeConsent('granted')) {
      storageBlocked = true;
      renderBanner();
      return;
    }
    storageBlocked = false;
    loadVendors();
    dispatchConsent('granted');
    renderBanner();
  }

  function deny() {
    var hadLoaded = loaded;
    writeConsent('denied');
    storageBlocked = false;
    clearAddedSinceBaseline();
    clearKnownVendorStorage();
    stopVendors();
    dispatchConsent('denied');
    renderBanner();
    if (hadLoaded) {
      try { window.location.reload(); } catch (e) {}
    }
  }

  function boot() {
    if (readConsent() !== 'granted') clearKnownVendorStorage();
    if (readConsent() === 'granted') loadVendors();
    if (document.body) renderBanner();
    else document.addEventListener('DOMContentLoaded', renderBanner);
  }

  boot();
})();
