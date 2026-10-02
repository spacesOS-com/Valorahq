'use strict';
/* Turns an approved article into files in the site repository.
   consumer-page   -> _build/content-packs/<slug>.json            rendered by the existing build at valorahq.com/<path>/
   advisor-article -> _build/insights-articles/<slug>.json        rendered by _build/insights_site.py for insights.spacesos.com
   The illustration goes to assets/cms/. The build regenerates sitemaps, robots and llms.txt. */
const db = require('./db');
const store = require('./store');
const articles = require('./articles');
const md = require('./markdown');
const { spawnSync } = require('child_process');

const SITE = () => process.env.CMS_SITE_URL || 'https://www.valorahq.com';
const INSIGHTS = () => process.env.CMS_INSIGHTS_URL || 'https://insights.spacesos.com';
const OWN_HOSTS = ['valorahq.com', 'spacesos.com'];
const fail = (status, message) => Object.assign(new Error(message), { status });

function utmFor(a) {
  const cfg = db.setting('utm', { enabled: true, utm_source: 'valora', utm_medium: 'content' });
  if (!cfg.enabled) return null;
  return { utm_source: cfg.utm_source || 'valora', utm_medium: cfg.utm_medium || 'content', utm_campaign: a.slug };
}

function paths(a) {
  const route = db.get('SELECT * FROM routes WHERE key = ?', a.category) || { path_prefix: '', page_type: '' };
  const ill = articles.illustration(a.id);
  const image = ill ? `assets/cms/${a.type === 'advisor-article' ? 'insights-' : ''}${ill.filename}` : null;
  if (a.type === 'consumer-page') {
    const sitePath = `${route.path_prefix ? route.path_prefix + '/' : ''}${a.slug}`;
    return { file: `_build/content-packs/${a.slug}.json`, sitePath, url: `${SITE()}/${sitePath}/`, image, route, ill };
  }
  return { file: `_build/insights-articles/${a.slug}.json`, sitePath: a.slug, url: `${INSIGHTS()}/${a.slug}/`, image, route, ill };
}

/* The document the Python build renders. */
function document(a) {
  const p = paths(a);
  const body = md.render(a.body_md, { utm: utmFor(a), ownHosts: OWN_HOSTS });
  const answer = a.summary.trim() ? `<p><strong>${md.esc(a.summary.trim())}</strong></p>\n` : '';
  const image = p.image ? { src: (a.type === 'advisor-article' ? SITE() : '') + '/' + p.image, alt: a.illustration_alt, caption: '' } : null;
  const common = {
    slug: a.type === 'consumer-page' ? p.sitePath : a.slug,
    meta_title: a.meta_title, meta_description: a.meta_description, h1: a.title,
    body_html: answer + body, faqs: a.faqs, key_takeaways: a.key_takeaways,
    status: a.noindex ? 'draft' : 'approved',
    cms: { article_id: a.id, type: a.type, author_persona: a.author_persona, summary: a.summary, canonical: a.canonical,
      og_image: a.og_image || (image ? image.src : ''), structured_data: a.structured_data,
      published_at: a.published_at || new Date().toISOString(), updated_at: new Date().toISOString() },
  };
  if (image) common.feature_image = image;
  if (a.type === 'consumer-page') return { ...common, page_type: p.route.page_type || 'niche-profession', keywords: [], internal_links: [] };
  return common;
}

async function publish(actor, id) {
  const a = articles.mustGet(id);
  if (!['approved', 'scheduled'].includes(a.status) || !a.qa_passed_at) throw fail(409, 'Only a QA-approved article can be published.');
  const issues = articles.problems(a, true);
  if (issues.length) throw fail(400, 'Cannot publish: ' + issues.join(' '));
  const p = paths(a);
  const existing = await store.read(p.file);
  if (existing) {
    let owner = null;
    try { owner = (JSON.parse(existing.text).cms || {}).article_id; } catch (_) { /* treated as foreign */ }
    if (owner !== a.id) throw fail(409, 'A page that was not created in the CMS already uses this address. Choose a different slug.');
  }
  const files = [{ path: p.file, data: JSON.stringify(document(a), null, 2) + '\n' }];
  if (p.ill) files.push({ path: p.image, data: Buffer.from(p.ill.data) });
  try {
    const result = await store.commit(files, `cms: publish ${a.type} ${a.slug} (QA: ${actor.name})`, actor);
    const deploy = await store.triggerDeploy();
    const out = articles.markPublished(actor, id, p.url);
    return { article: out, commit_url: result.url, deploy };
  } catch (e) {
    articles.markPublishFailed(actor, id, e.message);
    throw e;
  }
}

async function unpublish(actor, id) {
  const a = articles.mustGet(id);
  if (!a.live) throw fail(409, 'This is not published.');
  const p = paths(a);
  const files = [{ path: p.file, data: null }];
  if (p.image) files.push({ path: p.image, data: null });
  await store.commit(files, `cms: unpublish ${a.type} ${a.slug} (${actor.name})`, actor);
  await store.triggerDeploy();
  return articles.markUnpublished(actor, id);
}

/* Exact preview: the same Python templates the build uses, run on the unsaved document. */
function preview(a, token) {
  const doc = document(a);
  const ill = articles.illustration(a.id);
  if (ill && doc.feature_image) doc.feature_image.src = `/api/cms/v1/articles/${a.id}/illustration?token=${encodeURIComponent(token || '')}`;
  doc.status = 'draft';
  const r = spawnSync('python3', ['_build/cms_preview.py'], { cwd: store.ROOT(), input: JSON.stringify({ type: a.type, doc }), encoding: 'utf8', maxBuffer: 20 * 1024 * 1024 });
  if (r.status !== 0) throw fail(500, 'The preview could not be rendered: ' + String(r.stderr || '').trim().split('\n').slice(-1)[0]);
  return r.stdout;
}

/* Redirects are published as a data file; the build turns each into a redirect page and an nginx map. */
async function publishRedirects(actor) {
  const rows = db.all('SELECT from_path, to_path, status_code FROM redirects ORDER BY from_path');
  await store.commit([{ path: '_build/data/redirects.json', data: JSON.stringify(rows, null, 2) + '\n' }], `cms: update redirects (${actor.name})`, actor);
  return store.triggerDeploy();
}

/* Scheduled posts: checked once a minute by the server. */
async function runDue() {
  for (const id of articles.due()) {
    const a = articles.get(id);
    const qa = db.get('SELECT id, name, email FROM users WHERE id = ?', a.qa_by) || { name: 'scheduler' };
    try { await publish({ ...qa, via: 'system' }, id); } catch (e) { console.error('[cms] scheduled publish failed', id, e.message); }
  }
}

module.exports = { publish, unpublish, preview, publishRedirects, runDue, paths, document };
