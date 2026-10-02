'use strict';
/* Routes for the growth features, mounted under /api/cms/v1. Returns undefined when the path is not one of ours.
   Everything takes ?brand=<id> (defaults to Valora). */
const growth = require('./growth');
const leads = require('./leads');
const visibility = require('./visibility');
const crawlers = require('./crawlers');

const fail = (status, message) => Object.assign(new Error(message), { status });
const need = (user, ...roles) => { if (!roles.includes(user.role)) throw fail(403, `This needs the ${roles.join(' or ')} role.`); };

async function route({ r, method, q, body, user }) {
  const brand = q.brand || body.brand_id || null;

  if (r[0] === 'brands') {
    if (r.length === 1 && method === 'GET') return { brands: growth.listBrands() };
    if (r.length === 1 && method === 'POST') { need(user, 'admin'); return { status: 201, brand: growth.createBrand(user, body) }; }
    if (r.length === 2 && method === 'PATCH') { need(user, 'admin'); return { brand: growth.updateBrand(user, r[1], body) }; }
    if (r[2] === 'lead-key' && method === 'POST') { need(user, 'admin'); return growth.rotateLeadKey(user, r[1]); }
  }
  if (r[0] === 'overview' && method === 'GET') return growth.overview(brand);

  if (r[0] === 'opportunities' && method === 'GET') return growth.opportunities(brand);
  if (r[0] === 'keywords') {
    if (r.length === 1 && method === 'GET') return { keywords: growth.listKeywords(brand, { visible: q.visible, unassigned: q.unassigned === '1' }) };
    if (r.length === 1 && method === 'POST') return growth.addKeywords(user, brand, body.keywords ?? body.text, body.source === 'ai' ? 'ai' : 'manual');
    if (r[1] === 'check' && method === 'POST') return growth.checkMany(user, brand, Array.isArray(body.ids) ? body.ids : null);
    if (r[1] === 'volumes' && method === 'POST') return growth.fetchVolumes(user, brand);
    if (r[1] === 'assign' && method === 'POST') return growth.assignKeywords(user, body.ids, { article_id: body.article_id, page_url: body.page_url });
    if (r.length === 2 && method === 'DELETE') { growth.removeKeyword(user, r[1]); return { ok: true }; }
  }
  if (r[0] === 'pages' && method === 'GET') return { pages: growth.pages(brand) };

  if (r[0] === 'leads') {
    if (r.length === 1 && method === 'GET') return { leads: leads.list(brand, { status: q.status, spam: q.spam === '1', q: q.q }), statuses: leads.STATUSES };
    if (r[1] === 'export' && method === 'GET') { need(user, 'admin', 'qa'); return { raw: leads.csv(brand), type: 'text/csv; charset=utf-8', filename: 'leads.csv' }; }
    if (r.length === 2 && method === 'PATCH') return { lead: leads.update(user, r[1], body) };
    if (r[2] === 'notes' && method === 'POST') return { lead: leads.addNote(user, r[1], body.body) };
  }

  if (r[0] === 'visibility') {
    if (r.length === 1 && method === 'GET') return visibility.report(brand, Math.min(Number(q.days) || 30, 180));
    if (r[1] === 'prompts' && method === 'POST') return visibility.addPrompts(user, brand, body.prompts ?? body.text);
    if (r[1] === 'prompts' && r[2] && method === 'DELETE') { visibility.removePrompt(user, r[2]); return { ok: true }; }
    if (r[1] === 'run' && method === 'POST') return visibility.run(user, brand, { force: body.force === true });
  }
  if (r[0] === 'crawlers') {
    if (method === 'GET') return crawlers.report(brand, Math.min(Number(q.days) || 30, 180));
    if (r[1] === 'ingest' && method === 'POST') { need(user, 'admin'); return crawlers.ingest(user, brand, body.log); }
  }
  if (r[0] === 'backlinks') {
    if (r.length === 1 && method === 'GET') return { backlinks: growth.listBacklinks(brand) };
    if (r.length === 1 && method === 'POST') return { status: 201, backlink: growth.saveBacklink(user, brand, body) };
    if (r.length === 2 && method === 'PATCH') return { backlink: growth.saveBacklink(user, brand, body, r[1]) };
  }
  return undefined;
}

module.exports = { route };
