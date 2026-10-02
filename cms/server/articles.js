'use strict';
/* The core object and its workflow:
     draft -> in-review -> approved -> published        (publish happens on approve)
                        -> scheduled -> published       (approve with a future time)
   Writers create and edit. Only QA approves. Admins manage everything else.
   "Done" for the daily count means QA-passed AND published. */
const crypto = require('crypto');
const db = require('./db');

const TYPES = ['advisor-article', 'consumer-page'];
const SLOTS_PER_DAY = { 'advisor-article': 3, 'consumer-page': 3 };
const DEFAULT_PERSONA = { 'advisor-article': 'Hannah', 'consumer-page': 'Nina' };
const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const fail = (status, message) => Object.assign(new Error(message), { status });

const tz = () => process.env.CMS_TIMEZONE || 'America/New_York';
const dayOf = (date) => new Intl.DateTimeFormat('en-CA', { timeZone: tz(), year: 'numeric', month: '2-digit', day: '2-digit' }).format(date);
const today = () => dayOf(new Date());

const JSON_FIELDS = ['faqs', 'structured_data', 'key_takeaways', 'compliance_checklist', 'syndication'];
function hydrate(row) {
  if (!row) return null;
  const a = { ...row };
  for (const k of JSON_FIELDS) { try { a[k] = JSON.parse(row[k]); } catch (_) { a[k] = k === 'structured_data' || k === 'syndication' ? {} : []; } }
  a.noindex = Boolean(row.noindex); a.live = Boolean(row.live);
  a.has_illustration = Boolean(db.get('SELECT 1 AS x FROM illustrations WHERE article_id = ?', row.id));
  return a;
}
const get = (id) => hydrate(db.get('SELECT * FROM articles WHERE id = ?', id));
function mustGet(id) { const a = get(id); if (!a) throw fail(404, 'Article not found.'); return a; }

function list({ status, type, date, q, limit } = {}) {
  const where = [], args = [];
  if (status) { where.push('status = ?'); args.push(status); }
  if (type) { where.push('type = ?'); args.push(type); }
  if (date) { where.push('slot_date = ?'); args.push(date); }
  if (q) { where.push('(title LIKE ? OR slug LIKE ?)'); args.push(`%${q}%`, `%${q}%`); }
  const rows = db.all(`SELECT * FROM articles ${where.length ? 'WHERE ' + where.join(' AND ') : ''} ORDER BY updated_at DESC LIMIT ?`, ...args, Math.min(Number(limit) || 100, 500));
  return rows.map(hydrate).map(summary);
}
const summary = (a) => ({ id: a.id, type: a.type, category: a.category, title: a.title, slug: a.slug, status: a.status, author_persona: a.author_persona,
  slot_date: a.slot_date, scheduled_at: a.scheduled_at, published_at: a.published_at, published_url: a.published_url, live: a.live,
  has_illustration: a.has_illustration, qa_passed_at: a.qa_passed_at, updated_at: a.updated_at, publish_error: a.publish_error });

const slugify = (s) => String(s || '').toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80);

/* Field-level cleaning shared by create and update. Unknown fields are ignored. */
function clean(input, base) {
  const out = {};
  const str = (k, max) => { if (input[k] !== undefined) out[k] = String(input[k] ?? '').slice(0, max); };
  str('title', 200); str('body_md', 200000); str('summary', 1200); str('author_persona', 80); str('meta_title', 120);
  str('meta_description', 320); str('canonical', 400); str('og_image', 400); str('illustration_alt', 300); str('category', 60);
  if (input.slug !== undefined) out.slug = slugify(input.slug);
  if (input.slot_date !== undefined) { if (!/^\d{4}-\d{2}-\d{2}$/.test(input.slot_date)) throw fail(400, 'slot_date must be YYYY-MM-DD.'); out.slot_date = input.slot_date; }
  if (input.noindex !== undefined) out.noindex = input.noindex ? 1 : 0;
  if (input.faqs !== undefined) {
    if (!Array.isArray(input.faqs)) throw fail(400, 'faqs must be a list of { q, a }.');
    out.faqs = JSON.stringify(input.faqs.slice(0, 30).map((f) => ({ q: String((f && f.q) || '').slice(0, 300), a: String((f && f.a) || '').slice(0, 2000) })).filter((f) => f.q && f.a));
  }
  if (input.key_takeaways !== undefined) {
    if (!Array.isArray(input.key_takeaways)) throw fail(400, 'key_takeaways must be a list of sentences.');
    out.key_takeaways = JSON.stringify(input.key_takeaways.slice(0, 8).map((t) => String(t).slice(0, 400)).filter(Boolean));
  }
  if (input.structured_data !== undefined) {
    if (!input.structured_data || typeof input.structured_data !== 'object' || Array.isArray(input.structured_data)) throw fail(400, 'structured_data must be an object.');
    out.structured_data = JSON.stringify(input.structured_data).slice(0, 20000);
  }
  for (const k of ['canonical', 'og_image']) if (out[k] && !/^(https:\/\/|\/)/.test(out[k])) throw fail(400, `${k} must start with https:// or /.`);
  // Phase 2 hooks are writable through the API so agents can start populating them.
  if (input.compliance_checklist !== undefined && Array.isArray(input.compliance_checklist)) out.compliance_checklist = JSON.stringify(input.compliance_checklist).slice(0, 20000);
  if (input.advisor_id !== undefined) out.advisor_id = input.advisor_id === null ? null : Number(input.advisor_id);
  if (input.voice_profile_id !== undefined) out.voice_profile_id = input.voice_profile_id === null ? null : Number(input.voice_profile_id);
  return out;
}

function snapshot(actor, id) {
  const row = db.get('SELECT * FROM articles WHERE id = ?', id);
  db.run('INSERT INTO revisions (article_id,snapshot,actor_id,created_at) VALUES (?,?,?,?)', id, JSON.stringify(row), actor.id || null, db.now());
}

function create(actor, input) {
  if (!TYPES.includes(input.type)) throw fail(400, 'type must be advisor-article or consumer-page.');
  const fields = clean(input);
  if (!fields.title || !fields.title.trim()) throw fail(400, 'A title is required.');
  const routes = db.all('SELECT key FROM routes WHERE type = ?', input.type).map((r) => r.key);
  const category = routes.includes(fields.category) ? fields.category : routes[0];
  const slug = fields.slug || slugify(fields.title);
  if (!SLUG_RE.test(slug)) throw fail(400, 'The slug may only contain lowercase letters, numbers and hyphens.');
  if (db.get('SELECT 1 AS x FROM articles WHERE type = ? AND slug = ?', input.type, slug)) throw fail(409, 'That slug is already used by another ' + input.type + '.');
  const id = crypto.randomUUID(), t = db.now();
  db.run(`INSERT INTO articles (id,type,category,title,slug,body_md,summary,author_persona,status,meta_title,meta_description,canonical,og_image,
            faqs,structured_data,key_takeaways,noindex,illustration_alt,slot_date,created_by,updated_by,created_at,updated_at,compliance_checklist,advisor_id,voice_profile_id)
          VALUES (?,?,?,?,?,?,?,?,'draft',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
    id, input.type, category, fields.title.trim(), slug, fields.body_md || '', fields.summary || '',
    fields.author_persona || actor.persona || DEFAULT_PERSONA[input.type], fields.meta_title || '', fields.meta_description || '',
    fields.canonical || '', fields.og_image || '', fields.faqs || '[]', fields.structured_data || '{}', fields.key_takeaways || '[]',
    fields.noindex || 0, fields.illustration_alt || '', fields.slot_date || today(), actor.id, actor.id, t, t,
    fields.compliance_checklist || '[]', fields.advisor_id ?? null, fields.voice_profile_id ?? null);
  db.audit(actor, 'article.create', 'article', id, { type: input.type, slug });
  return get(id);
}

function update(actor, id, input) {
  const a = mustGet(id);
  if (actor.role === 'writer' && a.status === 'in-review') throw fail(409, 'This is with QA. Ask QA to send it back before editing.');
  const fields = clean(input, a);
  if (fields.title !== undefined && !fields.title.trim()) throw fail(400, 'A title is required.');
  if (fields.slug !== undefined && fields.slug !== a.slug) {
    if (a.live) throw fail(409, 'The slug of a published page cannot change. Publish a new page and add a redirect instead.');
    if (!SLUG_RE.test(fields.slug)) throw fail(400, 'The slug may only contain lowercase letters, numbers and hyphens.');
    if (db.get('SELECT 1 AS x FROM articles WHERE type = ? AND slug = ? AND id <> ?', a.type, fields.slug, id)) throw fail(409, 'That slug is already in use.');
  }
  if (fields.category !== undefined && !db.get('SELECT 1 AS x FROM routes WHERE key = ? AND type = ?', fields.category, a.type)) delete fields.category;
  const keys = Object.keys(fields);
  if (!keys.length) return a;
  snapshot(actor, id);
  // Any content change after sign-off needs a fresh QA pass; the live copy stays up until then.
  const contentKeys = keys.filter((k) => !['slot_date', 'compliance_checklist', 'advisor_id', 'voice_profile_id'].includes(k));
  const reset = contentKeys.length && ['approved', 'scheduled', 'published'].includes(a.status);
  const sets = keys.map((k) => `${k} = ?`).concat(['updated_by = ?', 'updated_at = ?'], reset ? ["status = 'draft'", 'scheduled_at = NULL', 'qa_passed_at = NULL'] : []);
  db.run(`UPDATE articles SET ${sets.join(', ')} WHERE id = ?`, ...keys.map((k) => fields[k]), actor.id, db.now(), id);
  db.audit(actor, 'article.update', 'article', id, { fields: keys, returned_to_draft: Boolean(reset) });
  return get(id);
}

/* What must be true before an article can go to QA, and again before it can publish. */
function problems(a, forPublish) {
  const out = [];
  if (!a.title.trim()) out.push('Add a title.');
  if (!SLUG_RE.test(a.slug)) out.push('Add a valid slug.');
  if (a.body_md.trim().split(/\s+/).length < 120) out.push('The body is too short (120 words minimum).');
  if (!a.summary.trim()) out.push('Add the answer-first summary.');
  if (!a.meta_title.trim()) out.push('Add a meta title.'); else if (a.meta_title.length > 60) out.push('The meta title is over 60 characters.');
  if (!a.meta_description.trim()) out.push('Add a meta description.'); else if (a.meta_description.length > 155) out.push('The meta description is over 155 characters.');
  if (!a.faqs.length) out.push('Add at least one FAQ.');
  if (forPublish) {
    if (!a.has_illustration) out.push('Add an illustration. Every post needs one before it can publish.');
    else if (!a.illustration_alt.trim()) out.push('Describe the illustration (alt text).');
  }
  return out;
}

function submit(actor, id) {
  const a = mustGet(id);
  if (a.status !== 'draft') throw fail(409, `Only a draft can be submitted (this is ${a.status}).`);
  const issues = problems(a, false);
  if (issues.length) throw Object.assign(fail(400, 'Not ready for QA: ' + issues.join(' ')), { issues });
  db.run("UPDATE articles SET status = 'in-review', review_note = '', updated_at = ? WHERE id = ?", db.now(), id);
  db.audit(actor, 'article.submit', 'article', id, {});
  return get(id);
}

function requestChanges(actor, id, note) {
  if (actor.role !== 'qa') throw fail(403, 'Only QA can send an article back.');
  const a = mustGet(id);
  if (a.status !== 'in-review') throw fail(409, 'Only an article in review can be sent back.');
  db.run("UPDATE articles SET status = 'draft', review_note = ?, updated_at = ? WHERE id = ?", String(note || '').slice(0, 2000), db.now(), id);
  db.audit(actor, 'article.request_changes', 'article', id, { note: String(note || '').slice(0, 500) });
  return get(id);
}

/* QA sign-off. Returns the article in 'approved' (publish now) or 'scheduled'. The caller publishes. */
function approve(actor, id, publishAt) {
  if (actor.role !== 'qa') throw fail(403, 'Only QA can approve.');
  const a = mustGet(id);
  if (a.status !== 'in-review') throw fail(409, `Only an article in review can be approved (this is ${a.status}).`);
  const issues = problems(a, true);
  if (issues.length) throw Object.assign(fail(400, 'Cannot approve yet: ' + issues.join(' ')), { issues });
  let when = null;
  if (publishAt) {
    const d = new Date(publishAt);
    if (Number.isNaN(d.getTime())) throw fail(400, 'publish_at is not a valid date and time.');
    if (d.getTime() > Date.now() + 30 * 1000) when = d.toISOString();
  }
  db.run('UPDATE articles SET status = ?, scheduled_at = ?, qa_passed_at = ?, qa_by = ?, slot_date = ?, publish_error = ?, updated_at = ? WHERE id = ?',
    when ? 'scheduled' : 'approved', when, db.now(), actor.id, when ? dayOf(new Date(when)) : a.slot_date, '', db.now(), id);
  db.audit(actor, when ? 'article.schedule' : 'article.approve', 'article', id, when ? { publish_at: when } : {});
  return get(id);
}

function markPublished(actor, id, url) {
  const t = db.now();
  db.run("UPDATE articles SET status = 'published', published_at = COALESCE(published_at, ?), published_url = ?, live = 1, scheduled_at = NULL, publish_error = '', slot_date = CASE WHEN published_at IS NULL THEN ? ELSE slot_date END, updated_at = ? WHERE id = ?",
    t, url, today(), t, id);
  db.audit(actor, 'article.publish', 'article', id, { url });
  return get(id);
}
function markPublishFailed(actor, id, message) {
  db.run("UPDATE articles SET status = 'approved', publish_error = ?, updated_at = ? WHERE id = ?", String(message).slice(0, 500), db.now(), id);
  db.audit(actor, 'article.publish_failed', 'article', id, { error: String(message).slice(0, 500) });
}
function markUnpublished(actor, id) {
  db.run("UPDATE articles SET status = 'draft', live = 0, published_url = NULL, qa_passed_at = NULL, scheduled_at = NULL, updated_at = ? WHERE id = ?", db.now(), id);
  db.audit(actor, 'article.unpublish', 'article', id, {});
  return get(id);
}

function remove(actor, id) {
  const a = mustGet(id);
  if (a.live) throw fail(409, 'Unpublish this before deleting it.');
  if (actor.role === 'writer' && a.created_by !== actor.id) throw fail(403, 'Writers can only delete their own drafts.');
  db.run('DELETE FROM articles WHERE id = ?', id);
  db.audit(actor, 'article.delete', 'article', id, { slug: a.slug, type: a.type });
}

function setIllustration(actor, id, { filename, content_type, data, alt }) {
  const a = mustGet(id);
  if (actor.role === 'writer' && a.status === 'in-review') throw fail(409, 'This is with QA. Ask QA to send it back before editing.');
  const EXT = { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp' };
  if (!EXT[content_type]) throw fail(400, 'The illustration must be a PNG, JPEG or WebP image.');
  if (!Buffer.isBuffer(data) || data.length < 100) throw fail(400, 'The image is empty.');
  if (data.length > 3 * 1024 * 1024) throw fail(400, 'The image is larger than 3 MB.');
  const magic = { 'image/png': [0x89, 0x50, 0x4e, 0x47], 'image/jpeg': [0xff, 0xd8, 0xff], 'image/webp': [0x52, 0x49, 0x46, 0x46] }[content_type];
  if (!magic.every((b, i) => data[i] === b)) throw fail(400, 'That file is not a valid ' + EXT[content_type].toUpperCase() + ' image.');
  db.run(`INSERT INTO illustrations (article_id,filename,content_type,data,updated_at) VALUES (?,?,?,?,?)
          ON CONFLICT(article_id) DO UPDATE SET filename = excluded.filename, content_type = excluded.content_type, data = excluded.data, updated_at = excluded.updated_at`,
    id, `${a.slug}.${EXT[content_type]}`, content_type, data, db.now());
  if (alt !== undefined) db.run('UPDATE articles SET illustration_alt = ? WHERE id = ?', String(alt).slice(0, 300), id);
  if (['approved', 'scheduled', 'published'].includes(a.status)) db.run("UPDATE articles SET status = 'draft', scheduled_at = NULL, qa_passed_at = NULL WHERE id = ?", id);
  db.run('UPDATE articles SET updated_at = ?, updated_by = ? WHERE id = ?', db.now(), actor.id, id);
  db.audit(actor, 'article.illustration', 'article', id, { content_type, bytes: data.length });
  return get(id);
}
const illustration = (id) => db.get('SELECT * FROM illustrations WHERE article_id = ?', id);

/* Today's board: 3 advisor articles + 3 consumer pages, and the count that matters. */
function calendar(date) {
  const day = /^\d{4}-\d{2}-\d{2}$/.test(date || '') ? date : today();
  const rows = db.all('SELECT * FROM articles WHERE slot_date = ? ORDER BY created_at', day).map(hydrate);
  const slots = [];
  for (const type of TYPES) {
    const mine = rows.filter((a) => a.type === type);
    for (let i = 0; i < Math.max(SLOTS_PER_DAY[type], mine.length); i++) {
      slots.push({ type, slot: i + 1, persona: DEFAULT_PERSONA[type], article: mine[i] ? summary(mine[i]) : null, extra: i >= SLOTS_PER_DAY[type] });
    }
  }
  return { date: day, target: SLOTS_PER_DAY['advisor-article'] + SLOTS_PER_DAY['consumer-page'], slots, ...dailyCount(day) };
}
function dailyCount(date) {
  const day = /^\d{4}-\d{2}-\d{2}$/.test(date || '') ? date : today();
  const done = db.all("SELECT type, published_at FROM articles WHERE qa_passed_at IS NOT NULL AND live = 1 AND published_at IS NOT NULL")
    .filter((r) => dayOf(new Date(r.published_at)) === day);
  return { date: day, done: done.length, done_by_type: { 'advisor-article': done.filter((r) => r.type === 'advisor-article').length, 'consumer-page': done.filter((r) => r.type === 'consumer-page').length } };
}
const due = () => db.all("SELECT id FROM articles WHERE status = 'scheduled' AND scheduled_at <= ?", db.now()).map((r) => r.id);
const revisions = (id) => db.all('SELECT id, actor_id, created_at FROM revisions WHERE article_id = ? ORDER BY id DESC LIMIT 50', id);

module.exports = { TYPES, get, mustGet, list, create, update, submit, requestChanges, approve, markPublished, markPublishFailed, markUnpublished,
  remove, setIllustration, illustration, calendar, dailyCount, due, revisions, problems, slugify, today, summary };
