'use strict';
/* The admin API. Everything the editor can do, an agent can do here with a Bearer token.
   Base: /api/cms/v1     Auth: session cookie (people) or "Authorization: Bearer vcms_…" (agents)
   See cms/README.md for the full route list. */
const auth = require('./auth');
const db = require('./db');
const store = require('./store');
const ai = require('./ai');
const content = require('./content');
const articles = require('./articles');
const publisher = require('./publish');
const mcp = require('./mcp');

const fail = (status, message) => Object.assign(new Error(message), { status });
const isSecure = (req) => (req.headers['x-forwarded-proto'] || '').split(',')[0] === 'https';
const need = (user, ...roles) => { if (!roles.includes(user.role)) throw fail(403, `This needs the ${roles.join(' or ')} role.`); };

function send(res, status, body, headers = {}) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Robots-Tag', 'noindex');
  for (const [k, v] of Object.entries(headers)) res.setHeader(k, v);
  res.end(JSON.stringify(body));
}
function sendRaw(res, status, type, body) {
  res.statusCode = status; res.setHeader('Content-Type', type); res.setHeader('Cache-Control', 'no-store'); res.setHeader('X-Robots-Tag', 'noindex');
  res.end(body);
}

async function readBody(req, limit = 6 * 1024 * 1024) {
  const chunks = []; let size = 0;
  for await (const c of req) { size += c.length; if (size > limit) throw fail(413, 'Request too large.'); chunks.push(c); }
  const text = Buffer.concat(chunks).toString('utf8');
  try { return text ? JSON.parse(text) : {}; } catch (_) { throw fail(400, 'Invalid JSON.'); }
}

/* ---- site pages (the existing hand-built pages, edited as structured content) ---- */
async function loadDoc(kind, id) {
  const file = content.pathFor(kind, id);
  if (!file) throw fail(404, 'Page not found.');
  const found = await store.read(file);
  if (!found) return { file, doc: null, sha: null };
  let doc;
  try { doc = JSON.parse(found.text); } catch (_) { throw fail(500, 'The stored page is not valid JSON.'); }
  return { file, doc, sha: found.sha };
}
async function listSitePages() {
  const out = [];
  for (const id of Object.keys(content.LANDING)) { const { doc } = await loadDoc('landing', id); if (doc) out.push(content.summarize('landing', id, doc)); }
  const ids = (await store.list(content.PACK_DIR, '.json')).filter((id) => content.ID_RE.test(id));
  const packs = await Promise.all(ids.map(async (id) => {
    try { const { doc } = await loadDoc('pack', id); return doc && !doc.cms ? content.summarize('pack', id, doc) : null; } catch (_) { return null; }
  }));
  return out.concat(packs.filter(Boolean));
}

const memory = () => db.setting('brand_memory', content.DEFAULT_MEMORY);
async function aiContext(withPages) {
  let pages = null;
  if (withPages) {
    pages = (await listSitePages()).filter((p) => p.status !== 'draft');
    for (const a of articles.list({ status: 'published', type: 'consumer-page', limit: 300 })) pages.push({ title: a.title, url: new URL(a.published_url).pathname });
  }
  return { memory: memory(), pages };
}
const checkToken = (doc, worst) => `${worst}.${auth.sign(`check:${content.hashDoc(doc)}:${worst}`)}`;
function readCheckToken(doc, token) {
  const [worst, mac] = String(token || '').split('.');
  if (!['none', 'low', 'medium', 'high'].includes(worst) || !mac) return null;
  return auth.safeEqual(auth.sign(`check:${content.hashDoc(doc)}:${worst}`), mac) ? worst : null;
}
/* The fields of an article the AI may read and propose changes to. */
const aiView = (a) => ({ title: a.title, summary: a.summary, body_md: a.body_md, meta_title: a.meta_title, meta_description: a.meta_description, faqs: a.faqs, key_takeaways: a.key_takeaways });

/* A preview link QA can open without signing in again; valid for 7 days. */
function previewToken(id) {
  const exp = Date.now() + 7 * 24 * 3600 * 1000;
  return `${exp}.${auth.sign(`preview:${id}:${exp}`)}`;
}
function previewAllowed(id, token) {
  const [exp, mac] = String(token || '').split('.');
  return Number(exp) > Date.now() && mac && auth.safeEqual(auth.sign(`preview:${id}:${exp}`), mac);
}

/* Shared by HTTP routes and MCP tools so both behave identically. */
const actions = {
  async approve(user, id, publishAt) {
    const a = articles.approve(user, id, publishAt);
    if (a.status === 'scheduled') return { article: a, scheduled: true };
    return publisher.publish(user, id);
  },
  previewUrl(req, id) {
    const host = req.headers['x-forwarded-host'] || req.headers.host;
    return `${isSecure(req) ? 'https' : 'http'}://${host}/api/cms/v1/preview/${id}?token=${previewToken(id)}`;
  },
  addRedirect(user, body) {
    const from = String(body.from_path || '').trim(), to = String(body.to_path || '').trim();
    const code = Number(body.status_code) === 302 ? 302 : 301;
    if (!/^\/(?:[a-z0-9._-]+\/)*[a-z0-9._-]*$/.test(from) || from === '/') throw fail(400, 'from_path must be a site path such as /old-page/.');
    if (!/^(https:\/\/|\/)/.test(to)) throw fail(400, 'to_path must be a site path or an https:// address.');
    if (from === to) throw fail(400, 'A page cannot redirect to itself.');
    if (db.get('SELECT 1 AS x FROM redirects WHERE from_path = ?', to)) throw fail(400, 'That destination is itself redirected. Point to the final address.');
    if (db.get('SELECT 1 AS x FROM redirects WHERE from_path = ?', from)) throw fail(409, 'There is already a redirect from that path.');
    const r = db.run('INSERT INTO redirects (from_path,to_path,status_code,created_by,created_at) VALUES (?,?,?,?,?)', from, to, code, user.id, db.now());
    db.audit(user, 'redirect.create', 'redirect', r.lastInsertRowid, { from, to, code });
    return db.get('SELECT * FROM redirects WHERE id = ?', r.lastInsertRowid);
  },
};

async function handle(req, res) {
  try {
    const url = new URL(req.url, 'http://localhost');
    const seg = url.pathname.replace(/^\/api\/cms\/?/, '').replace(/\/+$/, '').split('/').filter(Boolean);
    const method = req.method || 'GET';
    const q = Object.fromEntries(url.searchParams);

    if (seg[0] === 'health') return send(res, 200, { ok: true });
    if (seg[0] === 'mcp') return mcp.handle(req, res, { readBody, send, actions });
    if (seg[0] !== 'v1') throw fail(404, 'Not found. The API lives under /api/cms/v1.');
    const r = seg.slice(1);

    /* previews and their assets: a signed link is enough */
    if (r[0] === 'preview-assets' && r[1] === 'insights.css') return sendRaw(res, 200, 'text/css; charset=utf-8', require('fs').readFileSync(require('path').join(store.ROOT(), '_insights-site', 'styles.css')));
    const signedPreview = (r[0] === 'preview' && r[1] && previewAllowed(r[1], q.token));
    const user = auth.identify(req);

    if (r[0] === 'login' && method === 'POST') {
      if (req.headers['x-cms'] !== '1') throw fail(403, 'Missing request header.');
      const body = await readBody(req);
      await new Promise((ok) => setTimeout(ok, 300));
      const u = auth.login(body.email, body.password);
      if (!u) throw fail(401, 'That email and password do not match.');
      return send(res, 200, { user: u }, { 'Set-Cookie': auth.sessionCookie(u, isSecure(req)) });
    }
    if (r[0] === 'logout' && method === 'POST') return send(res, 200, { ok: true }, { 'Set-Cookie': auth.clearCookie(isSecure(req)) });

    if (r[0] === 'preview' && r[1] && method === 'GET') {
      if (!user && !signedPreview) throw fail(401, 'Please sign in.');
      return sendRaw(res, 200, 'text/html; charset=utf-8', publisher.preview(articles.mustGet(r[1]), previewToken(r[1])));
    }
    if (r[0] === 'articles' && r[2] === 'illustration' && method === 'GET') {
      if (!user && !previewAllowed(r[1], q.token)) throw fail(401, 'Please sign in.');
      const ill = articles.illustration(r[1]);
      if (!ill) throw fail(404, 'No illustration.');
      return sendRaw(res, 200, ill.content_type, Buffer.from(ill.data));
    }

    if (!user) throw fail(401, 'Please sign in, or send an API token.');
    // Browser sessions must send a custom header on writes; a cross-site form cannot.
    if (method !== 'GET' && user.via === 'ui' && req.headers['x-cms'] !== '1') throw fail(403, 'Missing request header.');
    const body = method === 'GET' || method === 'DELETE' ? {} : await readBody(req);

    if (r[0] === 'me') return send(res, 200, { user, ai: ai.configured(), storage: store.mode(), site_groups: content.GROUPS,
      routes: db.all('SELECT * FROM routes ORDER BY position'), today: articles.today() });

    /* ---- articles ---- */
    if (r[0] === 'articles') {
      if (r.length === 1 && method === 'GET') return send(res, 200, { articles: articles.list(q) });
      if (r.length === 1 && method === 'POST') return send(res, 201, { article: articles.create(user, body) });
      const id = r[1];
      if (r.length === 2 && method === 'GET') { const a = articles.mustGet(id); return send(res, 200, { article: a, problems: articles.problems(a, true), preview_url: actions.previewUrl(req, id) }); }
      if (r.length === 2 && method === 'PATCH') return send(res, 200, { article: articles.update(user, id, body) });
      if (r.length === 2 && method === 'DELETE') { articles.remove(user, id); return send(res, 200, { ok: true }); }
      if (r[2] === 'illustration' && method === 'PUT') {
        const data = Buffer.from(String(body.data_base64 || ''), 'base64');
        return send(res, 200, { article: articles.setIllustration(user, id, { filename: body.filename, content_type: body.content_type, data, alt: body.alt }) });
      }
      if (r[2] === 'submit' && method === 'POST') return send(res, 200, { article: articles.submit(user, id) });
      if (r[2] === 'request-changes' && method === 'POST') return send(res, 200, { article: articles.requestChanges(user, id, body.note) });
      if (r[2] === 'approve' && method === 'POST') return send(res, 200, await actions.approve(user, id, body.publish_at));
      if (r[2] === 'publish' && method === 'POST') { need(user, 'qa', 'admin'); return send(res, 200, await publisher.publish(user, id)); }
      if (r[2] === 'unpublish' && method === 'POST') { need(user, 'admin'); return send(res, 200, { article: await publisher.unpublish(user, id) }); }
      if (r[2] === 'revisions' && method === 'GET') return send(res, 200, { revisions: articles.revisions(id) });
      if (r[2] === 'preview-url' && method === 'GET') return send(res, 200, { preview_url: actions.previewUrl(req, id) });
    }
    if (r[0] === 'calendar' && method === 'GET') return send(res, 200, articles.calendar(q.date));
    if (r[0] === 'stats' && r[1] === 'daily' && method === 'GET') return send(res, 200, articles.dailyCount(q.date));

    /* ---- AI ---- */
    if (r[0] === 'ai' && method === 'POST') {
      if (r[1] === 'edit') {
        const doc = body.article_id ? aiView(articles.mustGet(body.article_id)) : body.doc;
        if (content.typeOf(doc) !== 'object' || !String(body.instruction || '').trim()) throw fail(400, 'Tell the AI what to change.');
        const proposal = await ai.edit(body.doc && content.typeOf(body.doc) === 'object' ? body.doc : doc, body.instruction, await aiContext(true));
        for (const c of proposal.changes) if (/_html$/.test(c.path) && typeof c.after === 'string') c.after = content.sanitizeHtml(c.after);
        return send(res, 200, proposal);
      }
      if (r[1] === 'check') {
        if (body.article_id || body.article) {
          const doc = body.article && content.typeOf(body.article) === 'object' ? body.article : aiView(articles.mustGet(body.article_id));
          return send(res, 200, await ai.check(doc, await aiContext(false)));
        }
        const { doc: previous } = await loadDoc(body.kind, body.id);
        const result = content.validate(body.kind, body.id, body.doc, previous);
        if (result.error) throw fail(400, result.error);
        const review = await ai.check(result.doc, await aiContext(false));
        return send(res, 200, { ...review, doc: result.doc, checkToken: checkToken(result.doc, review.worst) });
      }
      if (r[1] === 'draft') {
        if (!articles.TYPES.includes(body.type)) throw fail(400, 'type must be advisor-article or consumer-page.');
        if (!String(body.topic || '').trim()) throw fail(400, 'Enter a topic.');
        const draft = await ai.draft({ topic: body.topic, type: body.type, notes: body.notes }, await aiContext(true));
        let slug = articles.slugify(draft.slug || draft.title), n = 2;
        const base = slug;
        while (db.get('SELECT 1 AS x FROM articles WHERE type = ? AND slug = ?', body.type, slug)) slug = `${base}-${n++}`;
        const a = articles.create(user, { ...draft, slug, type: body.type, category: body.category, slot_date: body.slot_date });
        if (draft.review_notes.length) db.run('UPDATE articles SET review_note = ? WHERE id = ?', 'AI draft. Verify before approving: ' + draft.review_notes.join(' | ').slice(0, 1800), a.id);
        db.audit(user, 'ai.draft', 'article', a.id, { topic: String(body.topic).slice(0, 200) });
        return send(res, 201, { article: articles.get(a.id) });
      }
      if (r[1] === 'ideas') {
        if (!String(body.seed || '').trim()) throw fail(400, 'Enter an audience or theme.');
        const existing = articles.list({ limit: 300 }).map((a) => a.title).concat((await listSitePages()).map((p) => p.title));
        return send(res, 200, { ideas: await ai.ideas({ seed: body.seed, existing, type: body.type }, await aiContext(false)) });
      }
    }

    /* ---- site pages ---- */
    if (r[0] === 'site-pages') {
      if (r.length === 1 && method === 'GET') return send(res, 200, { pages: await listSitePages() });
      if (r.length === 3) {
        const [, kind, id] = r;
        const { file, doc: previous, sha } = await loadDoc(kind, id);
        if (method === 'GET') { if (!previous) throw fail(404, 'Page not found.'); return send(res, 200, { ...content.summarize(kind, id, previous), doc: previous, sha }); }
        if (method === 'PUT') {
          need(user, 'qa', 'admin'); // changing a live page is a publish, and only QA signs off
          if (!previous) throw fail(404, 'Page not found. New pages are created as articles.');
          if (body.sha !== sha) throw fail(409, 'Someone else changed this page while you were editing. Reload it to see their version.');
          const result = content.validate(kind, id, body.doc, previous);
          if (result.error) throw fail(400, result.error);
          const worst = readCheckToken(result.doc, body.checkToken);
          if (!worst && ai.configured()) throw fail(400, 'Run the compliance review on this exact version before publishing.');
          if (worst === 'high' && body.acknowledge !== true) throw fail(400, 'Confirm that you have read the serious findings before publishing.');
          const saved = await store.commit([{ path: file, data: content.serialize(result.doc) }], `cms: update ${id} (${user.name})`, user, { path: file, sha });
          await store.triggerDeploy();
          db.audit(user, 'site_page.publish', 'site_page', `${kind}/${id}`, { review: worst || 'unavailable' });
          const fresh = await store.read(file);
          return send(res, 200, { ...content.summarize(kind, id, result.doc), doc: result.doc, sha: fresh.sha, commit_url: saved.url });
        }
      }
    }

    /* ---- brand memory ---- */
    if (r[0] === 'brand-memory') {
      if (method === 'GET') return send(res, 200, { memory: memory() });
      if (method === 'PUT') {
        need(user, 'admin');
        if (content.typeOf(body.memory) !== 'object' || JSON.stringify(body.memory).length > 60000) throw fail(400, 'Brand memory must be an object under 60 KB.');
        db.setSetting('brand_memory', body.memory); db.audit(user, 'brand_memory.update', 'settings', 'brand_memory', {});
        return send(res, 200, { memory: memory() });
      }
    }

    /* ---- admin: users, tokens, routes, redirects, audit ---- */
    if (r[0] === 'users') {
      need(user, 'admin');
      if (r.length === 1 && method === 'GET') return send(res, 200, { users: auth.listUsers() });
      if (r.length === 1 && method === 'POST') return send(res, 201, { user: auth.createUser(user, body) });
      if (r.length === 2 && method === 'PATCH') return send(res, 200, { user: auth.updateUser(user, Number(r[1]), body) });
      if (r[2] === 'tokens' && method === 'POST') return send(res, 201, auth.createToken(user, Number(r[1]), body.name));
    }
    if (r[0] === 'tokens') {
      need(user, 'admin');
      if (method === 'GET') return send(res, 200, { tokens: auth.listTokens() });
      if (method === 'DELETE' && r[1]) { auth.revokeToken(user, Number(r[1])); return send(res, 200, { ok: true }); }
    }
    if (r[0] === 'routes') {
      if (method === 'GET') return send(res, 200, { routes: db.all('SELECT * FROM routes ORDER BY position') });
      if (method === 'PATCH' && r[1]) {
        need(user, 'admin');
        const route = db.get('SELECT * FROM routes WHERE key = ?', r[1]);
        if (!route) throw fail(404, 'Route not found.');
        const prefix = String(body.path_prefix ?? route.path_prefix).replace(/^\/+|\/+$/g, '');
        if (prefix && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(prefix)) throw fail(400, 'The path prefix may only contain lowercase letters, numbers and hyphens.');
        db.run('UPDATE routes SET path_prefix = ?, label = ? WHERE key = ?', prefix, String(body.label || route.label).slice(0, 80), r[1]);
        db.audit(user, 'route.update', 'route', r[1], { path_prefix: prefix });
        return send(res, 200, { route: db.get('SELECT * FROM routes WHERE key = ?', r[1]) });
      }
    }
    if (r[0] === 'redirects') {
      if (method === 'GET') return send(res, 200, { redirects: db.all('SELECT * FROM redirects ORDER BY from_path') });
      need(user, 'admin');
      if (method === 'POST') { const row = actions.addRedirect(user, body); const deploy = await publisher.publishRedirects(user); return send(res, 201, { redirect: row, deploy }); }
      if (method === 'DELETE' && r[1]) {
        const done = db.run('DELETE FROM redirects WHERE id = ?', Number(r[1]));
        if (!done.changes) throw fail(404, 'Redirect not found.');
        db.audit(user, 'redirect.delete', 'redirect', r[1], {});
        return send(res, 200, { ok: true, deploy: await publisher.publishRedirects(user) });
      }
    }
    if (r[0] === 'audit' && method === 'GET') {
      need(user, 'admin', 'qa');
      const limit = Math.min(Number(q.limit) || 100, 500);
      const rows = q.target_id ? db.all('SELECT * FROM audit_log WHERE target_id = ? ORDER BY id DESC LIMIT ?', q.target_id, limit) : db.all('SELECT * FROM audit_log ORDER BY id DESC LIMIT ?', limit);
      return send(res, 200, { entries: rows.map((e) => ({ ...e, detail: JSON.parse(e.detail || '{}') })) });
    }
    /* Phase 2 hooks: advisors and voice profiles are readable and writable by API; no UI yet. */
    if (r[0] === 'advisors') {
      need(user, 'admin');
      if (method === 'GET') return send(res, 200, { advisors: db.all('SELECT * FROM advisors ORDER BY name'), voice_profiles: db.all('SELECT * FROM voice_profiles') });
      if (method === 'POST') {
        if (!String(body.name || '').trim()) throw fail(400, 'A name is required.');
        const made = db.run('INSERT INTO advisors (name,firm,email,website,profile_slug,publish_endpoint,created_at) VALUES (?,?,?,?,?,?,?)',
          String(body.name).trim(), String(body.firm || ''), String(body.email || ''), String(body.website || ''), String(body.profile_slug || ''), String(body.publish_endpoint || ''), db.now());
        db.audit(user, 'advisor.create', 'advisor', made.lastInsertRowid, {});
        return send(res, 201, { advisor: db.get('SELECT * FROM advisors WHERE id = ?', made.lastInsertRowid) });
      }
    }
    throw fail(404, 'Not found.');
  } catch (err) {
    const status = err.status || 500;
    if (status >= 500) console.error('[cms]', err.message);
    send(res, status, { error: status === 500 ? 'Something went wrong on the server.' : err.message, ...(err.issues ? { issues: err.issues } : {}) });
  }
}

module.exports = { handle, actions };
