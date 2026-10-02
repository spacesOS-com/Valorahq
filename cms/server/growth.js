'use strict';
/* Brands, search opportunities, the pages that answer them, backlinks and the overview.
   A brand is Valora itself or a client firm; everything here is scoped to one brand.
   Search volumes and results are only ever what a provider, an import or a person supplied. */
const crypto = require('crypto');
const db = require('./db');
const search = require('./search');

const fail = (status, message) => Object.assign(new Error(message), { status });
const J = (v, d) => { try { return JSON.parse(v); } catch (_) { return d; } };
const hostOf = (url) => { try { return new URL(url).hostname.replace(/^www\./, '').toLowerCase(); } catch (_) { return ''; } };
const strList = (v, max = 30) => (Array.isArray(v) ? v : String(v || '').split(/[\n,]/)).map((x) => String(x).trim()).filter(Boolean).slice(0, max);

/* ---------- brands ---------- */
function brandOut(b) {
  return b && { id: b.id, name: b.name, domains: J(b.domains, []), aliases: J(b.aliases, []), competitors: J(b.competitors, []),
    is_default: Boolean(b.is_default), advisor_id: b.advisor_id, has_lead_key: Boolean(b.lead_key_hash) };
}
const listBrands = () => db.all('SELECT * FROM brands ORDER BY is_default DESC, name').map(brandOut);
function brand(id) {
  const b = id ? db.get('SELECT * FROM brands WHERE id = ?', Number(id)) : db.get('SELECT * FROM brands WHERE is_default = 1');
  if (!b) throw fail(404, 'Brand not found.');
  return brandOut(b);
}
function cleanBrand(input) {
  const domains = strList(input.domains, 10).map((d) => d.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, ''));
  if (domains.some((d) => !/^[a-z0-9.-]+\.[a-z]{2,}$/.test(d))) throw fail(400, 'Enter domains like example.com.');
  const competitors = (Array.isArray(input.competitors) ? input.competitors : []).slice(0, 15).map((c) => ({
    name: String((c && c.name) || '').trim().slice(0, 80),
    domains: strList(c && c.domains, 5).map((d) => d.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, '')) })).filter((c) => c.name);
  return { domains, aliases: strList(input.aliases, 10), competitors };
}
function createBrand(actor, input) {
  const name = String(input.name || '').trim();
  if (!name) throw fail(400, 'A brand needs a name.');
  const c = cleanBrand(input);
  const r = db.run('INSERT INTO brands (name,domains,aliases,competitors,advisor_id,created_at) VALUES (?,?,?,?,?,?)', name.slice(0, 120),
    JSON.stringify(c.domains), JSON.stringify(c.aliases.length ? c.aliases : [name]), JSON.stringify(c.competitors), input.advisor_id ? Number(input.advisor_id) : null, db.now());
  db.audit(actor, 'brand.create', 'brand', r.lastInsertRowid, { name });
  return brand(r.lastInsertRowid);
}
function updateBrand(actor, id, input) {
  const b = brand(id), c = cleanBrand({ domains: input.domains ?? b.domains, aliases: input.aliases ?? b.aliases, competitors: input.competitors ?? b.competitors });
  db.run('UPDATE brands SET name = ?, domains = ?, aliases = ?, competitors = ? WHERE id = ?', String(input.name || b.name).trim().slice(0, 120),
    JSON.stringify(c.domains), JSON.stringify(c.aliases), JSON.stringify(c.competitors), b.id);
  db.audit(actor, 'brand.update', 'brand', b.id, {});
  return brand(b.id);
}
/* The key a brand's website uses to send leads. Returned once; only its hash is kept. */
function rotateLeadKey(actor, id) {
  const b = brand(id), key = 'vlead_' + crypto.randomBytes(24).toString('base64url');
  db.run('UPDATE brands SET lead_key_hash = ? WHERE id = ?', crypto.createHash('sha256').update(key).digest('hex'), b.id);
  db.audit(actor, 'brand.lead_key', 'brand', b.id, {});
  return { brand_id: b.id, lead_key: key };
}

/* ---------- search opportunities ---------- */
function kwOut(k) {
  return { id: k.id, query: k.query, monthly_searches: k.monthly_searches, volume_source: k.volume_source, intent: k.intent, source: k.source,
    visible: k.visible, position: k.position, serp: J(k.serp, []), serp_checked_at: k.serp_checked_at, article_id: k.article_id, page_url: k.page_url };
}
function listKeywords(brandId, { visible, unassigned } = {}) {
  const where = ['brand_id = ?'], args = [brand(brandId).id];
  if (visible) { where.push('visible = ?'); args.push(visible); }
  if (unassigned) where.push("article_id IS NULL AND page_url = ''");
  return db.all(`SELECT * FROM keywords WHERE ${where.join(' AND ')} ORDER BY COALESCE(monthly_searches, -1) DESC, query LIMIT 2000`, ...args).map(kwOut);
}
/* items: [{ query, monthly_searches?, intent? }] or lines of "query, volume". Existing queries are updated, not duplicated. */
function addKeywords(actor, brandId, items, source) {
  const b = brand(brandId);
  const rows = (Array.isArray(items) ? items : String(items || '').split('\n')).map((it) => {
    if (typeof it === 'string') { const m = /^(.*?)[,\t]\s*([\d,]+)\s*$/.exec(it.trim()); return m ? { query: m[1], monthly_searches: Number(m[2].replace(/,/g, '')) } : { query: it }; }
    return it || {};
  }).map((it) => ({ query: String(it.query || '').trim().replace(/\s+/g, ' ').slice(0, 200),
    volume: Number.isFinite(Number(it.monthly_searches)) && it.monthly_searches !== null && it.monthly_searches !== '' && it.monthly_searches !== undefined ? Math.max(0, Math.round(Number(it.monthly_searches))) : null,
    intent: ['researching', 'comparing', 'ready to act'].includes(it.intent) ? it.intent : '' })).filter((it) => it.query.length >= 3).slice(0, 1000);
  let added = 0, updated = 0;
  for (const it of rows) {
    const existing = db.get('SELECT id FROM keywords WHERE brand_id = ? AND query = ?', b.id, it.query);
    if (existing) {
      if (it.volume !== null) { db.run("UPDATE keywords SET monthly_searches = ?, volume_source = ? WHERE id = ?", it.volume, source === 'provider' ? 'provider' : 'entered', existing.id); updated++; }
      continue;
    }
    db.run('INSERT INTO keywords (brand_id,query,monthly_searches,volume_source,intent,source,created_at) VALUES (?,?,?,?,?,?,?)',
      b.id, it.query, it.volume, it.volume === null ? '' : (source === 'provider' ? 'provider' : 'entered'), it.intent, source || 'manual', db.now());
    added++;
  }
  if (added || updated) db.audit(actor, 'keywords.add', 'brand', b.id, { added, updated, source: source || 'manual' });
  return { added, updated };
}
function keyword(id) { const k = db.get('SELECT * FROM keywords WHERE id = ?', Number(id)); if (!k) throw fail(404, 'Search not found.'); return k; }
function removeKeyword(actor, id) { const k = keyword(id); db.run('DELETE FROM keywords WHERE id = ?', k.id); db.audit(actor, 'keyword.delete', 'keyword', k.id, { query: k.query }); }

/* Looks the search up and records who shows today, and whether the brand is among them. */
async function checkKeyword(actor, id) {
  const k = keyword(id), b = brand(k.brand_id);
  const results = await search.serp(k.query);
  const hit = results.find((r) => b.domains.some((d) => hostOf(r.url) === d || hostOf(r.url).endsWith('.' + d)));
  db.run('UPDATE keywords SET serp = ?, serp_checked_at = ?, visible = ?, position = ? WHERE id = ?',
    JSON.stringify(results), db.now(), hit ? 'yes' : 'no', hit ? hit.position : null, k.id);
  return kwOut(keyword(k.id));
}
async function checkMany(actor, brandId, ids) {
  const list = (ids && ids.length ? ids.map(keyword) : db.all('SELECT * FROM keywords WHERE brand_id = ? ORDER BY serp_checked_at IS NOT NULL, COALESCE(monthly_searches,0) DESC LIMIT 25', brand(brandId).id));
  let checked = 0; const errors = [];
  for (const k of list.slice(0, 25)) { try { await checkKeyword(actor, k.id); checked++; } catch (e) { errors.push(e.message); if (e.status === 503) break; } }
  db.audit(actor, 'keywords.check', 'brand', brandId || '', { checked });
  return { checked, error: errors[0] || null };
}
async function fetchVolumes(actor, brandId) {
  const b = brand(brandId);
  const missing = db.all('SELECT query FROM keywords WHERE brand_id = ? AND monthly_searches IS NULL LIMIT 700', b.id).map((r) => r.query);
  if (!missing.length) return { updated: 0 };
  const found = await search.volumes(missing);
  let updated = 0;
  for (const q of missing) {
    const v = found[q.toLowerCase()];
    if (Number.isFinite(v)) { db.run("UPDATE keywords SET monthly_searches = ?, volume_source = 'provider' WHERE brand_id = ? AND query = ?", v, b.id, q); updated++; }
  }
  db.audit(actor, 'keywords.volumes', 'brand', b.id, { updated });
  return { updated };
}
function assignKeywords(actor, ids, { article_id, page_url }) {
  if (article_id && !db.get('SELECT 1 AS x FROM articles WHERE id = ?', article_id)) throw fail(404, 'Article not found.');
  if (page_url && !/^https:\/\//.test(page_url)) throw fail(400, 'page_url must start with https://.');
  for (const id of ids || []) db.run('UPDATE keywords SET article_id = ?, page_url = ? WHERE id = ?', article_id || null, article_id ? '' : String(page_url || ''), keyword(id).id);
  db.audit(actor, 'keywords.assign', article_id ? 'article' : 'page', article_id || page_url || '', { count: (ids || []).length });
  return { assigned: (ids || []).length };
}

/* Opportunities = searches where the brand does not show yet. */
function opportunities(brandId) {
  const all = listKeywords(brandId);
  const open = all.filter((k) => k.visible !== 'yes');
  const known = open.filter((k) => k.monthly_searches !== null);
  return { total: all.length, open: open.length, visible: all.length - open.length, unchecked: all.filter((k) => k.visible === 'unknown').length,
    missed_searches: known.reduce((n, k) => n + k.monthly_searches, 0), volume_known_for: known.length,
    top: open.slice(0, 5), keywords: all, providers: { results: search.serpConfigured(), volumes: search.volumeConfigured() } };
}

/* Pages and the searches each one is meant to answer. */
function pages(brandId) {
  const b = brand(brandId), kws = listKeywords(b.id), map = new Map();
  const add = (key, base) => { if (!map.has(key)) map.set(key, { ...base, keywords: [] }); return map.get(key); };
  if (b.is_default) {
    for (const a of db.all("SELECT id,title,type,category,status,published_url,live,updated_at,published_at FROM articles ORDER BY updated_at DESC LIMIT 500")) {
      add('a:' + a.id, { kind: 'article', article_id: a.id, title: a.title, type: a.type, category: a.category, status: a.status, live: Boolean(a.live), url: a.published_url || '',
        stale: Boolean(a.live) && Date.now() - new Date(a.updated_at).getTime() > 120 * 24 * 3600 * 1000, updated_at: a.updated_at });
    }
  }
  for (const k of kws) {
    if (k.article_id && map.has('a:' + k.article_id)) map.get('a:' + k.article_id).keywords.push(k);
    else if (k.page_url) add('u:' + k.page_url, { kind: 'external', title: k.page_url.replace(/^https:\/\/(www\.)?/, ''), type: 'page', category: '', status: 'published', live: true, url: k.page_url, stale: false }).keywords.push(k);
  }
  if (b.is_default) for (const page of siteInventory()) {
    const known = [...map.values()].some((p) => p.url && p.url.replace(/^https?:\/\/[^/]+/, '') === page.path);
    if (!known) add('s:' + page.path, { kind: page.editable ? 'site-page' : 'code', title: page.title, type: 'page', category: page.section, status: 'published', live: true,
      url: page.path, stale: false, site_page: page.editable || null });
  }
  for (const k of kws) if (k.page_url) { const hit = map.get('s:' + k.page_url.replace(/^https?:\/\/[^/]+/, '')); if (hit && !hit.keywords.includes(k)) hit.keywords.push(k); }
  return [...map.values()].map((p) => ({ ...p, searches: p.keywords.reduce((n, k) => n + (k.monthly_searches || 0), 0),
    volume_known_for: p.keywords.filter((k) => k.monthly_searches !== null).length, keywords: p.keywords.map((k) => ({ id: k.id, query: k.query, monthly_searches: k.monthly_searches, visible: k.visible })) }));
}

/* Every page of the built site, from its sitemap. Pages that came from a content file can be edited in
   the CMS; the rest are generated by code (calculators, directories, the homepage) and are listed
   so nothing is invisible, but they are changed in the repository. */
function siteInventory() {
  const fs = require('fs'), path = require('path'), root = require('./store').ROOT();
  const map = path.join(root, 'sitemap.xml');
  if (!fs.existsSync(map)) return [];
  const { PACK_DIR, LANDING } = require('./content');
  const editable = new Map(Object.keys(LANDING).map((id) => [`/${id}/`, { kind: 'landing', id }]));
  const dir = path.join(root, PACK_DIR);
  if (fs.existsSync(dir)) for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.json'))) {
    try { const d = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); if (!d.cms) editable.set(`/${d.slug}/`, { kind: 'pack', id: f.slice(0, -5) }); } catch (_) { /* skip unreadable */ }
  }
  const out = [];
  for (const m of fs.readFileSync(map, 'utf8').matchAll(/<loc>https?:\/\/[^/]+([^<]*)<\/loc>/g)) {
    const p = m[1] || '/', file = path.join(root, p, 'index.html');
    let title = p;
    if (fs.existsSync(file)) { const t = /<title>([^<]*)<\/title>/.exec(fs.readFileSync(file, 'utf8').slice(0, 4000)); if (t) title = t[1].replace(/&amp;/g, '&').replace(/&#x27;/g, "'").replace(/\s*\|\s*Valora.*$/, '').trim() || p; }
    out.push({ path: p, title, section: p === '/' ? 'home' : p.split('/')[1], editable: editable.get(p) || null });
  }
  return out;
}

/* ---------- backlinks (a working log of authority-building; nothing is fetched or verified automatically) ---------- */
const listBacklinks = (brandId) => db.all('SELECT * FROM backlinks WHERE brand_id = ? ORDER BY id DESC LIMIT 1000', brand(brandId).id);
function saveBacklink(actor, brandId, input, id) {
  const STATUS = ['prospect', 'pitched', 'live', 'lost'];
  const src = String(input.source_url || '').trim(), status = STATUS.includes(input.status) ? input.status : 'prospect';
  if (id) {
    const row = db.get('SELECT * FROM backlinks WHERE id = ?', Number(id)); if (!row) throw fail(404, 'Backlink not found.');
    const next = STATUS.includes(input.status) ? input.status : row.status;
    db.run('UPDATE backlinks SET status = ?, notes = ?, anchor = ?, target_url = ?, live_at = ? WHERE id = ?', next, String(input.notes ?? row.notes).slice(0, 1000),
      String(input.anchor ?? row.anchor).slice(0, 200), String(input.target_url ?? row.target_url).slice(0, 400), next === 'live' ? (row.live_at || db.now()) : row.live_at, row.id);
    db.audit(actor, 'backlink.update', 'backlink', row.id, { status: next });
    return db.get('SELECT * FROM backlinks WHERE id = ?', row.id);
  }
  if (!/^https?:\/\/\S+\.\S+/.test(src)) throw fail(400, 'Enter the address of the page that links (or will link) to the site.');
  const r = db.run('INSERT INTO backlinks (brand_id,source_url,target_url,anchor,status,notes,live_at,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?)', brand(brandId).id, src.slice(0, 400),
    String(input.target_url || '').slice(0, 400), String(input.anchor || '').slice(0, 200), status, String(input.notes || '').slice(0, 1000), status === 'live' ? db.now() : null, actor.id || null, db.now());
  db.audit(actor, 'backlink.create', 'backlink', r.lastInsertRowid, { status });
  return db.get('SELECT * FROM backlinks WHERE id = ?', r.lastInsertRowid);
}

/* ---------- overview ---------- */
function overview(brandId) {
  const b = brand(brandId), opp = opportunities(b.id), since = new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString();
  const leadRows = db.all('SELECT status, spam, received_at FROM leads WHERE brand_id = ?', b.id);
  const real = leadRows.filter((l) => !l.spam);
  const runs = db.all(`SELECT r.mentioned, r.provider FROM prompt_runs r JOIN prompts p ON p.id = r.prompt_id WHERE p.brand_id = ? AND r.error = '' AND r.ran_at >= ?`, b.id, since);
  const crawl = db.get('SELECT COALESCE(SUM(hits),0) AS n FROM crawler_hits WHERE brand_id = ? AND day >= ?', b.id, since.slice(0, 10)).n;
  const links = db.all('SELECT status FROM backlinks WHERE brand_id = ?', b.id);
  return { brand: b,
    searches: { tracked: opp.total, visible: opp.visible, open: opp.open, unchecked: opp.unchecked, missed_searches: opp.missed_searches, volume_known_for: opp.volume_known_for },
    pages: b.is_default ? { published: db.get('SELECT COUNT(*) AS n FROM articles WHERE live = 1').n, in_progress: db.get("SELECT COUNT(*) AS n FROM articles WHERE live = 0").n,
      published_30d: db.get('SELECT COUNT(*) AS n FROM articles WHERE live = 1 AND published_at >= ?', since).n } : null,
    leads: { total: real.length, last_30d: real.filter((l) => l.received_at >= since).length, new: real.filter((l) => l.status === 'new').length,
      qualified: real.filter((l) => l.status === 'qualified').length, won: real.filter((l) => l.status === 'won').length, spam_filtered: leadRows.length - real.length },
    ai_visibility: { runs_30d: runs.length, mentioned_30d: runs.filter((r) => r.mentioned).length, rate: runs.length ? Math.round(100 * runs.filter((r) => r.mentioned).length / runs.length) : null },
    ai_crawler_hits_30d: crawl, backlinks: { live: links.filter((l) => l.status === 'live').length, in_progress: links.filter((l) => ['prospect', 'pitched'].includes(l.status)).length } };
}

module.exports = { listBrands, brand, createBrand, updateBrand, rotateLeadKey, listKeywords, addKeywords, removeKeyword, checkKeyword, checkMany, fetchVolumes,
  assignKeywords, opportunities, pages, listBacklinks, saveBacklink, overview, hostOf, keyword };
