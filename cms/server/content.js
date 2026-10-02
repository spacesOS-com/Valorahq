'use strict';
/* What the CMS is allowed to manage, and the rules a document must pass
   before it is written. Nothing outside these paths is ever touched. */
const crypto = require('crypto');

const PACK_DIR = '_build/content-packs';
const LANDING = { 'for-advisors': '_build/data/for-advisors.json' };
/* Starting brand memory. The live copy is kept in the database (it is not public) and edited in the CMS. */
const DEFAULT_MEMORY = {
  "company": {
    "name": "Valora",
    "what_we_do": "Valora publishes educational financial-planning content for individuals and provides marketing services to financial advisory firms.",
    "what_we_are_not": [
      "Valora is not a registered investment adviser and does not give investment, tax or legal advice.",
      "Valora does not guarantee clients, leads, rankings, returns or any outcome.",
      "Valora does not recommend, vet or match individuals with specific advisers."
    ]
  },
  "services": [
    {
      "name": "AEO & GEO",
      "description": "Answer engine optimization and generative engine optimization: making an advisory firm's expertise easy for AI assistants and AI-powered search to find, read and cite.",
      "pricing": ""
    },
    {
      "name": "Outbound",
      "description": "Direct outreach to people who fit the clients an advisory firm serves.",
      "pricing": ""
    },
    {
      "name": "YouTube",
      "description": "Putting an advisory firm's expertise on YouTube.",
      "pricing": ""
    }
  ],
  "pricing": [
    "Plans start at $900 per month.",
    "Month to month, no long contract.",
    "Annual option: 12 months for the price of 10."
  ],
  "buyers": [
    {
      "who": "Financial advisory firms",
      "pain_points": [
        "Want to connect with people who are already seeking their services"
      ],
      "notes": ""
    },
    {
      "who": "Individuals reading the educational guides",
      "pain_points": [
        "Want to understand a financial-planning decision before speaking to a professional"
      ],
      "notes": ""
    }
  ],
  "voice": {
    "tone": "Plain, specific and calm. No hype, no urgency.",
    "always_say": [
      "Results vary by firm, market and competition."
    ],
    "never_say": [
      "guaranteed",
      "best",
      "top-rated",
      "proven results",
      "match you with an advisor"
    ]
  },
  "corrections": [],
  "competitors": []
};
const ID_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const GROUPS = [
  { key: 'landing', label: 'Landing pages' },
  { key: 'guide', label: 'Guides' },
  { key: 'company', label: 'Company' },
  { key: 'legal', label: 'Legal' },
];

function pathFor(kind, id) {
  if (!ID_RE.test(id || '') || id.length > 80) return null;
  if (kind === 'landing') return LANDING[id] || null;
  if (kind === 'pack') return `${PACK_DIR}/${id}.json`;
  return null;
}

function groupOf(kind, doc) {
  if (kind === 'landing') return 'landing';
  if (doc.page_type === 'legal') return 'legal';
  if (doc.page_type === 'team') return 'company';
  return 'guide';
}

function summarize(kind, id, doc) {
  return {
    kind, id,
    group: groupOf(kind, doc),
    title: doc.h1 || doc.title || doc.meta_title || id,
    url: kind === 'landing' ? `/${id}/` : `/${doc.slug || id}/`,
    page_type: doc.page_type || '',
    status: kind === 'landing' ? 'approved' : (doc.status || 'approved'),
  };
}

/* ---------- HTML allowlist for *_html fields ---------- */
const TAGS = new Set(('p h2 h3 h4 ul ol li a strong em b i u br hr blockquote table thead tbody tr th td ' +
  'img figure figcaption span div section sup sub small code pre details summary cite abbr dl dt dd aside').split(' '));
const DROP_WITH_CONTENT = /<(script|style|iframe|object|embed|form|noscript|template|svg|math)\b[\s\S]*?<\/\1\s*>/gi;
const ATTRS = new Set(['href', 'src', 'alt', 'title', 'class', 'id', 'target', 'rel', 'width', 'height', 'loading',
  'decoding', 'colspan', 'rowspan', 'scope', 'open', 'srcset', 'sizes', 'aria-label', 'aria-hidden', 'role', 'start']);
const URL_OK = /^(https?:\/\/|\/|#|mailto:|tel:)/i;

function sanitizeHtml(html) {
  let out = String(html).replace(DROP_WITH_CONTENT, '').replace(/<!--[\s\S]*?-->/g, '');
  out = out.replace(/<\/?([a-zA-Z][a-zA-Z0-9]*)((?:"[^"]*"|'[^']*'|[^'">])*)>/g, (whole, name, rest) => {
    const tag = name.toLowerCase();
    if (!TAGS.has(tag)) return '';
    if (whole[1] === '/') return `</${tag}>`;
    let attrs = '';
    const re = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)(?:\s*=\s*("[^"]*"|'[^']*'|[^\s"'>]+))?/g;
    let m;
    while ((m = re.exec(rest))) {
      const key = m[1].toLowerCase();
      if (!ATTRS.has(key) && !key.startsWith('data-')) continue;
      if (m[2] === undefined) { attrs += ` ${key}`; continue; }
      let val = m[2];
      if (val[0] === '"' || val[0] === "'") val = val.slice(1, -1);
      if ((key === 'href' || key === 'src') && !URL_OK.test(val.trim())) continue;
      attrs += ` ${key}="${val.replace(/"/g, '&quot;')}"`;
    }
    const selfClose = /\/\s*$/.test(rest) ? ' /' : '';
    return `<${tag}${attrs}${selfClose}>`;
  });
  return out;
}

function walkStrings(node, fn, key) {
  if (typeof node === 'string') return fn(node, key);
  if (Array.isArray(node)) return node.map((v) => walkStrings(v, fn, key));
  if (node && typeof node === 'object') {
    const o = {};
    for (const k of Object.keys(node)) o[k] = walkStrings(node[k], fn, k);
    return o;
  }
  return node;
}

const typeOf = (v) => (Array.isArray(v) ? 'array' : v === null ? 'null' : typeof v);

/* Returns { doc } (cleaned) or { error }. `previous` is the stored version, or null for a new page. */
function validate(kind, id, doc, previous) {
  if (typeOf(doc) !== 'object') return { error: 'The page must be a JSON object.' };
  const size = Buffer.byteLength(JSON.stringify(doc));
  if (size > 600 * 1024) return { error: 'This page is too large to save.' };

  let clean = walkStrings(doc, (s, key) => (key && /_html$/.test(key) ? sanitizeHtml(s) : s));
  for (const k of Object.keys(clean)) if (k.startsWith('_')) delete clean[k];

  if (previous) {
    for (const k of Object.keys(previous)) {
      if (!(k in clean)) return { error: `The field "${k}" cannot be removed.` };
      if (typeOf(previous[k]) !== typeOf(clean[k])) return { error: `The field "${k}" has the wrong shape.` };
    }
    if (kind === 'landing') {
      const bad = shapeMismatch(previous, clean, '');
      if (bad) return { error: `The field "${bad}" has the wrong shape.` };
    }
  }

  if (kind === 'pack') {
    if (previous ? clean.slug !== previous.slug : clean.slug !== id) return { error: 'The page address (slug) cannot be changed.' };
    for (const k of ['meta_title', 'meta_description', 'body_html']) {
      if (typeof clean[k] !== 'string' || !clean[k].trim()) return { error: `"${k}" is required.` };
    }
    if (typeof (clean.h1 || clean.title) !== 'string' || !(clean.h1 || clean.title).trim()) return { error: 'A page heading is required.' };
    if (clean.faqs !== undefined) {
      if (!Array.isArray(clean.faqs)) return { error: 'FAQs must be a list.' };
      for (const f of clean.faqs) {
        if (typeOf(f) !== 'object' || typeof f.q !== 'string' || typeof f.a !== 'string' || !f.q.trim() || !f.a.trim()) {
          return { error: 'Every FAQ needs a question and an answer.' };
        }
      }
      // Keep the machine-readable FAQ copy identical to the visible one.
      if ('faq_jsonld' in clean && (!previous || JSON.stringify(previous.faqs) !== JSON.stringify(clean.faqs))) {
        const ld = { '@context': 'https://schema.org', '@type': 'FAQPage',
          mainEntity: clean.faqs.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })) };
        clean.faq_jsonld = typeof clean.faq_jsonld === 'string' ? JSON.stringify(ld) : ld;
      }
    }
    if (clean.status !== undefined && !['draft', 'approved'].includes(clean.status)) return { error: 'Status must be draft or approved.' };
    if (!previous && !['niche-profession', 'city', 'life-event', 'asset-type', 'employer'].includes(clean.page_type)) {
      return { error: 'New pages must be a guide type.' };
    }
  }
  if (kind === 'landing') {
    if (!previous) return { error: 'Landing pages cannot be created from the CMS yet.' };
    if (!Array.isArray(clean.faqs) || clean.faqs.some((f) => !f || typeof f.q !== 'string' || typeof f.a !== 'string')) {
      return { error: 'Every FAQ needs a question and an answer.' };
    }
  }
  return { doc: clean };
}

/* Landing pages are laid out by code, so their structure is fixed: same keys, same types;
   lists may grow or shrink but their items keep the same shape. */
function shapeMismatch(a, b, at) {
  const ta = typeOf(a), tb = typeOf(b);
  if (ta !== tb) return at || '(root)';
  if (ta === 'object') {
    for (const k of Object.keys(a)) {
      if (!(k in b)) return `${at}${at ? '.' : ''}${k}`;
      const bad = shapeMismatch(a[k], b[k], `${at}${at ? '.' : ''}${k}`);
      if (bad) return bad;
    }
  } else if (ta === 'array' && a.length) {
    for (let i = 0; i < b.length; i++) {
      const bad = shapeMismatch(a[0], b[i], `${at}[${i}]`);
      if (bad) return bad;
    }
  }
  return null;
}

const serialize = (doc) => JSON.stringify(doc, null, 2) + '\n';
const hashDoc = (doc) => crypto.createHash('sha256').update(JSON.stringify(doc)).digest('hex');

module.exports = { PACK_DIR, LANDING, DEFAULT_MEMORY, GROUPS, ID_RE, pathFor, summarize, validate, sanitizeHtml, serialize, hashDoc, typeOf };
