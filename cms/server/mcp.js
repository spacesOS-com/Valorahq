'use strict';
/* MCP server (Model Context Protocol, streamable HTTP, JSON responses) at /api/cms/mcp.
   Agents connect with the same Bearer token as the REST API and get the same permissions.
   Every tool is a thin wrapper over the functions the REST routes use, so the two can never drift. */
const auth = require('./auth');
const db = require('./db');
const articles = require('./articles');
const publisher = require('./publish');

const PROTOCOL = '2025-06-18';
const obj = (properties, required = []) => ({ type: 'object', properties, required, additionalProperties: false });
const str = (description) => ({ type: 'string', description });
const ARTICLE_FIELDS = {
  title: str('Headline.'), slug: str('URL slug: lowercase words joined by hyphens.'), body_md: str('Body in Markdown. No raw HTML.'),
  summary: str('Answer-first summary: one or two sentences that answer the headline.'), author_persona: str('Persona byline, e.g. Hannah or Nina.'),
  category: str('Route key: advisor-article, profession, specialty, city or competitor-alternative.'),
  meta_title: str('Up to 60 characters.'), meta_description: str('Up to 155 characters.'), canonical: str('Canonical URL override (https://… or /path/).'),
  og_image: str('Open Graph image URL override.'), illustration_alt: str('Alt text for the illustration.'), slot_date: str('Editorial calendar day, YYYY-MM-DD.'),
  noindex: { type: 'boolean', description: 'Publish hidden from search engines.' },
  faqs: { type: 'array', description: 'FAQ blocks; rendered with FAQPage JSON-LD.', items: obj({ q: str('Question'), a: str('Plain-text answer') }, ['q', 'a']) },
  key_takeaways: { type: 'array', items: { type: 'string' } },
  structured_data: { type: 'object', description: 'Extra schema.org JSON-LD object to emit with the page.' },
};
const ID = { id: str('Article id.') };

const TOOLS = [
  { name: 'list_articles', description: 'List articles, newest first. Filter by status, type or calendar day.',
    inputSchema: obj({ status: str('draft | in-review | approved | scheduled | published'), type: str('advisor-article | consumer-page'), date: str('YYYY-MM-DD'), q: str('Search title or slug.') }),
    run: (u, a) => ({ articles: articles.list(a) }) },
  { name: 'get_article', description: 'Get one article with every field, plus what is still missing before it can publish.', inputSchema: obj(ID, ['id']),
    run: (u, a) => { const x = articles.mustGet(a.id); return { article: x, problems: articles.problems(x, true) }; } },
  { name: 'create_article', description: 'Create a draft. Writers and above.', inputSchema: obj({ type: str('advisor-article | consumer-page'), ...ARTICLE_FIELDS }, ['type', 'title']),
    run: (u, a) => ({ article: articles.create(u, a) }) },
  { name: 'update_article', description: 'Edit fields of an article. Editing an approved or published article returns it to draft for a fresh QA pass.',
    inputSchema: obj({ ...ID, ...ARTICLE_FIELDS }, ['id']), run: (u, { id, ...rest }) => ({ article: articles.update(u, id, rest) }) },
  { name: 'set_illustration', description: 'Attach the required illustration (PNG, JPEG or WebP, up to 3 MB) as base64.',
    inputSchema: obj({ ...ID, content_type: str('image/png | image/jpeg | image/webp'), data_base64: str('The image bytes, base64-encoded.'), alt: str('Alt text.') }, ['id', 'content_type', 'data_base64', 'alt']),
    run: (u, a) => ({ article: articles.setIllustration(u, a.id, { content_type: a.content_type, data: Buffer.from(a.data_base64, 'base64'), alt: a.alt }) }) },
  { name: 'submit_for_review', description: 'Send a draft to QA. Fails with the list of missing items if it is not ready.', inputSchema: obj(ID, ['id']),
    run: (u, a) => ({ article: articles.submit(u, a.id) }) },
  { name: 'request_changes', description: 'QA only: send an article in review back to draft with a note.', inputSchema: obj({ ...ID, note: str('What needs to change.') }, ['id', 'note']),
    run: (u, a) => ({ article: articles.requestChanges(u, a.id, a.note) }) },
  { name: 'approve_article', description: 'QA only: approve an article in review. It publishes immediately, or at publish_at if that is in the future.',
    inputSchema: obj({ ...ID, publish_at: str('Optional ISO 8601 time to schedule publishing.') }, ['id']), run: (u, a, ctx) => ctx.actions.approve(u, a.id, a.publish_at) },
  { name: 'unpublish_article', description: 'Admin only: remove a published article from the site and return it to draft.', inputSchema: obj(ID, ['id']),
    run: async (u, a) => { if (u.role !== 'admin') throw Object.assign(new Error('This needs the admin role.'), { status: 403 }); return { article: await publisher.unpublish(u, a.id) }; } },
  { name: 'delete_article', description: 'Delete an unpublished article.', inputSchema: obj(ID, ['id']), run: (u, a) => { articles.remove(u, a.id); return { ok: true }; } },
  { name: 'get_preview_url', description: 'A staging link for a draft that opens without signing in, valid for 7 days.', inputSchema: obj(ID, ['id']),
    run: (u, a, ctx) => { articles.mustGet(a.id); return { preview_url: ctx.actions.previewUrl(ctx.req, a.id) }; } },
  { name: 'get_calendar', description: "The editorial calendar for a day: the six slots (3 advisor articles, 3 consumer pages), what fills each, and the day's done count.",
    inputSchema: obj({ date: str('YYYY-MM-DD; defaults to today.') }), run: (u, a) => articles.calendar(a.date) },
  { name: 'get_daily_count', description: 'How many articles are done for a day. Done means QA-passed and published.', inputSchema: obj({ date: str('YYYY-MM-DD; defaults to today.') }),
    run: (u, a) => articles.dailyCount(a.date) },
  { name: 'list_redirects', description: 'List redirects.', inputSchema: obj({}), run: () => ({ redirects: db.all('SELECT * FROM redirects ORDER BY from_path') }) },
  { name: 'add_redirect', description: 'Admin only: add a redirect and publish it.', inputSchema: obj({ from_path: str('Old site path, e.g. /old-page/'), to_path: str('New site path or https:// URL.'), status_code: { type: 'integer', enum: [301, 302] } }, ['from_path', 'to_path']),
    run: async (u, a, ctx) => { if (u.role !== 'admin') throw Object.assign(new Error('This needs the admin role.'), { status: 403 }); const row = ctx.actions.addRedirect(u, a); return { redirect: row, deploy: await publisher.publishRedirects(u) }; } },
  { name: 'get_audit_log', description: 'QA and admin: recent actions with actor and time. Pass target_id for one article.', inputSchema: obj({ target_id: str('Article id.'), limit: { type: 'integer' } }),
    run: (u, a) => { if (!['admin', 'qa'].includes(u.role)) throw Object.assign(new Error('This needs the qa or admin role.'), { status: 403 });
      const limit = Math.min(Number(a.limit) || 50, 200);
      return { entries: a.target_id ? db.all('SELECT * FROM audit_log WHERE target_id = ? ORDER BY id DESC LIMIT ?', a.target_id, limit) : db.all('SELECT * FROM audit_log ORDER BY id DESC LIMIT ?', limit) }; } },
];

async function handle(req, res, ctx) {
  const reply = (id, result, error) => ctx.send(res, 200, error ? { jsonrpc: '2.0', id, error } : { jsonrpc: '2.0', id, result });
  if (req.method !== 'POST') { res.statusCode = 405; res.setHeader('Allow', 'POST'); return res.end(); }
  const user = auth.identify(req);
  if (!user || user.via !== 'api') { res.setHeader('WWW-Authenticate', 'Bearer'); return ctx.send(res, 401, { error: 'Send an API token: Authorization: Bearer vcms_…' }); }
  let msg;
  try { msg = await ctx.readBody(req); } catch (_) { return reply(null, null, { code: -32700, message: 'Parse error' }); }
  if (Array.isArray(msg)) return reply(null, null, { code: -32600, message: 'Batch requests are not supported.' });
  const { id, method, params } = msg || {};
  if (id === undefined) { res.statusCode = 202; return res.end(); } // notifications need no reply
  if (method === 'initialize') return reply(id, { protocolVersion: PROTOCOL, capabilities: { tools: {} }, serverInfo: { name: 'valora-cms', version: '1.0.0' },
    instructions: 'Valora CMS. Writers create and edit drafts, QA approves (which publishes), admins manage redirects. Your token has the role: ' + user.role + '.' });
  if (method === 'ping') return reply(id, {});
  if (method === 'tools/list') return reply(id, { tools: TOOLS.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })) });
  if (method === 'tools/call') {
    const tool = TOOLS.find((t) => t.name === (params && params.name));
    if (!tool) return reply(id, null, { code: -32602, message: 'Unknown tool.' });
    const actor = { ...user, via: 'mcp' };
    try {
      const out = await tool.run(actor, (params && params.arguments) || {}, { ...ctx, req });
      return reply(id, { content: [{ type: 'text', text: JSON.stringify(out) }], isError: false });
    } catch (e) {
      if (!e.status || e.status >= 500) console.error('[cms mcp]', e.message);
      return reply(id, { content: [{ type: 'text', text: e.status && e.status < 500 ? e.message : 'Something went wrong on the server.' }], isError: true });
    }
  }
  return reply(id, null, { code: -32601, message: 'Method not found.' });
}

module.exports = { handle, TOOLS };
