'use strict';

const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.resolve(__dirname, '..');
const consentSrc = fs.readFileSync(path.join(root, 'assets/vendor-consent.js'), 'utf8');
const calcPath = path.join(root, 'calculators/capital-gains-tax-estimate/index.html');
const calcHtml = fs.readFileSync(calcPath, 'utf8');

function sha1Prefix(file) {
  return crypto.createHash('sha1').update(fs.readFileSync(file)).digest('hex').slice(0, 8);
}

function scriptTags(html) {
  const tags = [];
  const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let match;
  while ((match = re.exec(html))) tags.push({ attrs: match[1], body: match[2] });
  return tags;
}

function executable(attrs) {
  const type = /type\s*=\s*["']([^"']+)["']/i.exec(attrs);
  if (!type) return true;
  const value = type[1].toLowerCase();
  return value === 'text/javascript' || value === 'application/javascript' || value === 'module';
}

function vendorConfig(html) {
  const match = html.match(/<script type="application\/json" id="valora-vendor-config">([\s\S]*?)<\/script>/);
  assert.ok(match, 'missing vendor config');
  return JSON.parse(match[1]);
}

function makeStorage(initial, throwing) {
  const map = new Map(Object.entries(initial || {}));
  return {
    get length() { return map.size; },
    key(index) { return Array.from(map.keys())[index] || null; },
    getItem(key) {
      if (throwing) throw new Error('blocked');
      return map.has(key) ? map.get(key) : null;
    },
    setItem(key, value) {
      if (throwing) throw new Error('blocked');
      map.set(String(key), String(value));
    },
    removeItem(key) {
      if (throwing) throw new Error('blocked');
      map.delete(key);
    },
    _map: map,
  };
}

function boot(options) {
  const network = [];
  const cookies = new Map();
  const localStorage = makeStorage(options.localStorage, options.blockStorage);
  const sessionStorage = makeStorage(options.sessionStorage);
  const location = {
    search: options.search || '',
    hostname: 'www.valorahq.com',
    reloads: 0,
    reload() { this.reloads += 1; },
  };

  function walk(node, visit) {
    visit(node);
    (node.children || []).forEach((child) => walk(child, visit));
  }

  class El {
    constructor(tag) {
      this.tag = tag;
      this.attrs = {};
      this.children = [];
      this.parentNode = null;
      this.textContent = '';
      this.className = '';
      this.id = '';
      this.type = '';
      this.async = false;
      this.crossOrigin = null;
      this.onerror = null;
      this._code = '';
      this._ran = false;
      this.listeners = {};
    }
    set text(value) {
      this._code = String(value);
      this.textContent = String(value);
    }
    get text() { return this._code; }
    set src(value) {
      this.attrs.src = String(value);
      if (value) network.push(String(value));
    }
    get src() { return this.attrs.src || ''; }
    setAttribute(name, value) { this.attrs[name] = String(value); }
    getAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attrs, name) ? this.attrs[name] : null; }
    addEventListener(type, fn) {
      (this.listeners[type] || (this.listeners[type] = [])).push(fn);
    }
    dispatchEvent(event) {
      if (!event.target) event.target = this;
      (this.listeners[event.type] || []).forEach((fn) => fn(event));
      if (this.parentNode && this.parentNode.dispatchEvent) this.parentNode.dispatchEvent(event);
    }
    appendChild(child) {
      child.parentNode = this;
      this.children.push(child);
      const type = (child.attrs.type || child.type || '').toLowerCase();
      if (child.tag === 'script' && child._code && !child._ran && (!type || type === 'text/javascript')) {
        child._ran = true;
        vm.runInNewContext(child._code, sandbox, { filename: 'vendor-snippet.js' });
      }
      return child;
    }
    insertBefore(node, ref) {
      node.parentNode = this;
      const index = this.children.indexOf(ref);
      if (index < 0) this.children.push(node);
      else this.children.splice(index, 0, node);
      return node;
    }
    removeChild(child) {
      const index = this.children.indexOf(child);
      if (index >= 0) this.children.splice(index, 1);
      child.parentNode = null;
      return child;
    }
  }

  const document = {
    listeners: {},
    cookie: '',
    createElement(tag) { return new El(tag); },
    createTextNode(text) {
      const node = new El('#text');
      node.textContent = String(text);
      return node;
    },
    getElementById(id) {
      let found = null;
      walk(document.documentElement, (node) => { if (node.id === id) found = node; });
      return found;
    },
    getElementsByTagName(tag) {
      const found = [];
      walk(document.documentElement, (node) => { if (node.tag === tag) found.push(node); });
      return found;
    },
    querySelectorAll(selector) {
      const parts = selector.split(',').map((part) => part.trim());
      const found = [];
      walk(document.documentElement, (node) => {
        if (parts.some((part) => matches(node, part))) found.push(node);
      });
      return found;
    },
    addEventListener(type, fn) {
      (document.listeners[type] || (document.listeners[type] = [])).push(fn);
    },
    dispatchEvent(event) {
      (document.listeners[event.type] || []).forEach((fn) => fn(event));
    },
  };
  Object.defineProperty(document, 'cookie', {
    get() {
      return Array.from(cookies.entries()).map(([key, value]) => key + '=' + value).join('; ');
    },
    set(value) {
      const pair = String(value).split(';')[0];
      const index = pair.indexOf('=');
      const name = pair.slice(0, index).trim();
      const stored = pair.slice(index + 1).trim();
      if (/expires=/i.test(value)) cookies.delete(name);
      else cookies.set(name, stored);
    },
  });

  function matches(node, selector) {
    if (selector === 'script[data-valora-vendor]') {
      return node.tag === 'script' && node.attrs['data-valora-vendor'] != null;
    }
    const src = /^script\[src\*="([^"]+)"\]$/.exec(selector);
    return !!(src && node.tag === 'script' && (node.attrs.src || '').includes(src[1]));
  }

  const head = new El('head');
  const body = new El('body');
  const rootEl = new El('html');
  rootEl.appendChild(head);
  rootEl.appendChild(body);
  document.documentElement = rootEl;
  document.head = head;
  document.body = body;
  const config = new El('script');
  config.attrs.type = 'application/json';
  config.id = 'valora-vendor-config';
  config.textContent = JSON.stringify(options.config);
  head.appendChild(config);
  const seed = new El('script');
  seed._code = '';
  head.appendChild(seed);

  const sandbox = {
    document,
    localStorage,
    sessionStorage,
    location,
    URLSearchParams,
    CustomEvent: class CustomEvent {
      constructor(type, init) {
        this.type = type;
        this.detail = init && init.detail;
      }
    },
    console,
  };
  sandbox.window = sandbox;
  vm.runInNewContext(consentSrc, sandbox, { filename: 'vendor-consent.js' });
  return { sandbox, network, localStorage, cookies, document, body };
}

function findControl(document, action) {
  let found = null;
  (function walk(node) {
    if (node.attrs && node.attrs['data-valora-consent'] === action) found = node;
    (node.children || []).forEach(walk);
  })(document.documentElement);
  return found;
}

function click(node) {
  assert.ok(node, 'missing consent control');
  node.dispatchEvent({ type: 'click' });
}

const config = vendorConfig(calcHtml);
assert.strictEqual(config.v, 1);
assert.ok(config.vendors.some((vendor) => vendor.id === 'posthog' && vendor.snippet.includes("posthog.init('phc_swhDRhpyNrJXeLkkTpYuH9au4XstiKXqY88XAEmX2Cjk'")));
assert.ok(config.vendors.some((vendor) => vendor.id === 'rb2b' && vendor.snippet.includes('ddwl4m2hdecbv.cloudfront.net')));

const consentHash = sha1Prefix(path.join(root, 'assets/vendor-consent.js'));
const scriptHash = sha1Prefix(path.join(root, 'assets/script.js'));
assert.ok(calcHtml.includes('/assets/vendor-consent.js?v=' + consentHash));
assert.ok(calcHtml.includes('/assets/script.js?v=' + scriptHash));

for (const tag of scriptTags(calcHtml)) {
  if (!executable(tag.attrs)) continue;
  assert.ok(!tag.body.includes('posthog.init('), 'executable script still calls posthog.init');
  assert.ok(!tag.body.includes('window.reb2b'), 'executable script still starts RB2B');
  assert.ok(!tag.body.includes('ddwl4m2hdecbv.cloudfront.net'), 'executable script still points at CloudFront');
  assert.ok(!/src\s*=\s*["'][^"']*(?:posthog|cloudfront\.net)/i.test(tag.attrs));
}
assert.ok(!/<(?:script|link)\b[^>]+(?:src|href)\s*=\s*["']https?:\/\/[^"']*(?:posthog|cloudfront\.net)/i.test(calcHtml));

const advisors = fs.readFileSync(path.join(root, 'advisors.html'), 'utf8');
assert.ok(!advisors.includes('reb2b') && !advisors.includes('posthog') && !advisors.includes('cloudfront.net'));

const wealth = fs.readFileSync(path.join(root, 'find-a-financial-advisor/business-owner-wealth-planning/index.html'), 'utf8');
assert.ok(!wealth.includes('posthog') && !wealth.includes('cloudfront.net') && !wealth.includes('reb2b'));

const pre = boot({ config, localStorage: { ph_existing: '1', vz_gate_seen_v1: '1' } });
assert.deepStrictEqual(pre.network, []);
assert.strictEqual(pre.sandbox.posthog, undefined);
assert.strictEqual(pre.sandbox.reb2b, undefined);
assert.strictEqual(pre.localStorage.getItem('ph_existing'), null);
assert.strictEqual(pre.localStorage.getItem('vz_gate_seen_v1'), '1');
assert.ok(findControl(pre.document, 'grant'));
assert.ok(findControl(pre.document, 'deny'));
assert.strictEqual(pre.sandbox.location.reloads, 0);

click(findControl(pre.document, 'deny'));
assert.strictEqual(pre.localStorage.getItem('valora_vendor_consent_v1'), 'denied');
assert.deepStrictEqual(pre.network, []);
assert.strictEqual(pre.sandbox.location.reloads, 0);
assert.ok(!findControl(pre.document, 'deny'));

const allow = boot({ config });
click(findControl(allow.document, 'grant'));
assert.deepStrictEqual(allow.network, [
  'https://us-assets.i.posthog.com/static/array.js',
  'https://ddwl4m2hdecbv.cloudfront.net/b/7N850HK1EMN1/7N850HK1EMN1.js.gz',
]);
assert.ok(allow.sandbox.posthog);
assert.ok(allow.sandbox.reb2b);
allow.localStorage.setItem('opaque_vendor', '1');
allow.localStorage.setItem('vz_gate_seen_v1', '1');
allow.document.cookie = 'ph_session=abc';
allow.document.cookie = 'opaque_rb=1';
click(findControl(allow.document, 'deny'));
assert.strictEqual(allow.localStorage.getItem('valora_vendor_consent_v1'), 'denied');
assert.strictEqual(allow.localStorage.getItem('opaque_vendor'), null);
assert.strictEqual(allow.localStorage.getItem('vz_gate_seen_v1'), '1');
assert.ok(!allow.cookies.has('ph_session'));
assert.ok(!allow.cookies.has('opaque_rb'));
assert.strictEqual(allow.sandbox.posthog, undefined);
assert.strictEqual(allow.sandbox.reb2b, undefined);
assert.strictEqual(allow.document.querySelectorAll('script[data-valora-vendor], script[src*="i.posthog.com"], script[src*="ddwl4m2hdecbv.cloudfront.net"]').length, 0);
assert.strictEqual(allow.sandbox.location.reloads, 1);

const denied = boot({ config, localStorage: { valora_vendor_consent_v1: 'denied', ph_leftover: '1' } });
assert.deepStrictEqual(denied.network, []);
assert.strictEqual(denied.localStorage.getItem('ph_leftover'), null);
assert.ok(findControl(denied.document, 'grant'));

const embed = boot({
  config,
  search: '?embed=1',
  localStorage: { ph_embed: '1' },
});
assert.deepStrictEqual(embed.network, []);
assert.strictEqual(embed.document.getElementById('valora-vendor-consent'), null);
assert.strictEqual(embed.localStorage.getItem('ph_embed'), null);
assert.strictEqual(embed.sandbox.location.reloads, 0);

const embedAllowed = boot({
  config,
  search: '?embed=1',
  localStorage: { valora_vendor_consent_v1: 'granted', ph_keep: '1' },
});
assert.deepStrictEqual(embedAllowed.network, [
  'https://us-assets.i.posthog.com/static/array.js',
  'https://ddwl4m2hdecbv.cloudfront.net/b/7N850HK1EMN1/7N850HK1EMN1.js.gz',
]);
assert.strictEqual(embedAllowed.document.getElementById('valora-vendor-consent'), null);
assert.strictEqual(embedAllowed.localStorage.getItem('ph_keep'), '1');

const blocked = boot({ config, blockStorage: true });
assert.deepStrictEqual(blocked.network, []);
click(findControl(blocked.document, 'grant'));
assert.deepStrictEqual(blocked.network, []);
assert.ok((function walk(node) {
  if (/blocked storage/.test(node.textContent || '')) return true;
  return (node.children || []).some(walk);
})(blocked.body));

const scriptJs = fs.readFileSync(path.join(root, 'assets/script.js'), 'utf8');
const prefill = scriptJs.slice(scriptJs.indexOf('function prefillLocation'), scriptJs.indexOf('function rotator'));
assert.ok(prefill.includes("localStorage.getItem('valora_vendor_consent_v1') === 'granted'"));
assert.ok(prefill.indexOf('valora_vendor_consent_v1') < prefill.indexOf("fetch('https://ipapi.co/json/'"));

console.log('vendor consent tests passed');
