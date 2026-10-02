'use strict';
/* Leads inbox: every inquiry, what the person read before sending it, a status, notes and an owner.
   Websites send leads with the brand's lead key. Obvious junk is kept but hidden, with the reason. */
const crypto = require('crypto');
const db = require('./db');
const growth = require('./growth');

const fail = (status, message) => Object.assign(new Error(message), { status });
const STATUSES = ['new', 'contacted', 'qualified', 'won', 'lost'];
const DISPOSABLE = new Set(['mailinator.com', 'guerrillamail.com', '10minutemail.com', 'tempmail.com', 'temp-mail.org', 'yopmail.com', 'trashmail.com', 'sharklasers.com', 'getnada.com', 'dispostable.com', 'maildrop.cc', 'throwawaymail.com', 'fakeinbox.com', 'emailondeck.com', 'mintemail.com']);
const J = (v, d) => { try { return JSON.parse(v); } catch (_) { return d; } };

/* Reasons a submission is very unlikely to be a person worth calling. Conservative on purpose:
   anything flagged is still stored and can be restored with one click. */
function spamReason(lead, honeypot) {
  if (honeypot) return 'Filled a field hidden from people';
  const email = lead.email.toLowerCase(), domain = email.split('@')[1] || '';
  if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/.test(email)) return 'No valid email address';
  if (DISPOSABLE.has(domain)) return 'Disposable email address';
  const letters = lead.name.replace(/[^a-z]/gi, '');
  if (letters.length >= 6 && !/[aeiouy]/i.test(letters)) return 'Name looks like random typing';
  if (/(.)\1{4,}/.test(lead.name)) return 'Name looks like random typing';
  if ((lead.message.match(/https?:\/\//g) || []).length >= 3) return 'Message is mostly links';
  if (/\b(seo services|backlinks? for sale|guest post offer|crypto giveaway|casino|viagra)\b/i.test(lead.message)) return 'Looks like a sales pitch or scam';
  return '';
}

function out(l) {
  return { id: l.id, brand_id: l.brand_id, received_at: l.received_at, name: l.name, email: l.email, phone: l.phone, company: l.company, action: l.action,
    message: l.message, source_page: l.source_page, journey: J(l.journey, []), utm: J(l.utm, {}), status: l.status, spam: Boolean(l.spam), spam_reason: l.spam_reason,
    assigned_to: l.assigned_to, notes: db.all('SELECT id, author_name, body, created_at FROM lead_notes WHERE lead_id = ? ORDER BY id', l.id) };
}

function brandForKey(key) {
  if (!key) return null;
  const hash = crypto.createHash('sha256').update(String(key)).digest('hex');
  return db.get("SELECT * FROM brands WHERE lead_key_hash = ? AND lead_key_hash <> ''", hash);
}

const recent = new Map(); // per-key burst limit within one server instance
function ingest(key, input) {
  const b = brandForKey(key);
  if (!b) throw fail(401, 'Unknown lead key.');
  const t = Date.now(), bucket = (recent.get(b.id) || []).filter((x) => t - x < 60 * 1000);
  if (bucket.length >= 30) throw fail(429, 'Too many submissions. Try again shortly.');
  bucket.push(t); recent.set(b.id, bucket);
  const s = (v, n) => String(v ?? '').trim().slice(0, n);
  const lead = { name: s(input.name, 120), email: s(input.email, 200), phone: s(input.phone, 40), company: s(input.company, 160),
    action: s(input.action, 40).toLowerCase().replace(/[^a-z0-9 -]/g, '') || 'contact', message: s(input.message, 4000), source_page: s(input.source_page, 300) };
  if (!lead.name && !lead.email && !lead.phone) throw fail(400, 'A lead needs at least a name, an email or a phone number.');
  const journey = (Array.isArray(input.journey) ? input.journey : []).slice(-40).map((step) => ({
    at: s(step && step.at, 40), path: s(step && step.path, 300), event: s(step && step.event, 30).toLowerCase().replace(/[^a-z_]/g, '') || 'view' })).filter((x) => x.path.startsWith('/'));
  const utm = {};
  for (const k of ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'referrer']) if (input.utm && input.utm[k]) utm[k] = s(input.utm[k], 200);
  let reason = spamReason(lead, Boolean(input.website_url || input.hp));
  if (!reason && lead.email && db.get('SELECT 1 AS x FROM leads WHERE brand_id = ? AND email = ? AND received_at >= ?', b.id, lead.email, new Date(t - 10 * 60 * 1000).toISOString())) reason = 'Duplicate of a submission in the last 10 minutes';
  const r = db.run('INSERT INTO leads (brand_id,received_at,name,email,phone,company,action,message,source_page,journey,utm,spam,spam_reason) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
    b.id, db.now(), lead.name, lead.email, lead.phone, lead.company, lead.action, lead.message, lead.source_page, JSON.stringify(journey), JSON.stringify(utm), reason ? 1 : 0, reason);
  db.audit({ name: 'website', via: 'system' }, 'lead.received', 'lead', r.lastInsertRowid, { brand: b.name, spam: Boolean(reason) });
  const saved = out(db.get('SELECT * FROM leads WHERE id = ?', r.lastInsertRowid));
  if (!reason) notify(b, saved).catch((e) => console.error('[cms] lead notification failed', e.message));
  return { ok: true };
}

/* Slack-compatible webhook, if one is configured. Sends no more than is needed to act on the lead. */
async function notify(b, lead) {
  const hook = process.env.CMS_LEAD_WEBHOOK_URL;
  if (!hook) return;
  await fetch(hook, { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: `New lead for ${b.name}: ${lead.name || lead.email} (${lead.action})${lead.company ? ', ' + lead.company : ''}. Open the leads inbox in the CMS.` }) });
}

function list(brandId, { status, spam, q } = {}) {
  const where = ['brand_id = ?', 'spam = ?'], args = [growth.brand(brandId).id, spam ? 1 : 0];
  if (STATUSES.includes(status)) { where.push('status = ?'); args.push(status); }
  if (q) { where.push('(name LIKE ? OR email LIKE ? OR company LIKE ?)'); args.push(`%${q}%`, `%${q}%`, `%${q}%`); }
  return db.all(`SELECT * FROM leads WHERE ${where.join(' AND ')} ORDER BY received_at DESC LIMIT 500`, ...args).map(out);
}
function mustGet(id) { const l = db.get('SELECT * FROM leads WHERE id = ?', Number(id)); if (!l) throw fail(404, 'Lead not found.'); return l; }
function update(actor, id, patch) {
  const l = mustGet(id), sets = [], args = [], changed = {};
  if (patch.status !== undefined) { if (!STATUSES.includes(patch.status)) throw fail(400, 'Status must be one of: ' + STATUSES.join(', ') + '.'); sets.push('status = ?'); args.push(patch.status); changed.status = patch.status; }
  if (patch.spam !== undefined) { sets.push('spam = ?', 'spam_reason = ?'); args.push(patch.spam ? 1 : 0, patch.spam ? 'Marked as spam by ' + actor.name : ''); changed.spam = Boolean(patch.spam); }
  if (patch.assigned_to !== undefined) {
    const uid = patch.assigned_to === null || patch.assigned_to === '' ? null : Number(patch.assigned_to);
    if (uid !== null && !db.get('SELECT 1 AS x FROM users WHERE id = ? AND active = 1', uid)) throw fail(400, 'That person is not an active user.');
    sets.push('assigned_to = ?'); args.push(uid); changed.assigned_to = uid;
  }
  if (sets.length) { db.run(`UPDATE leads SET ${sets.join(', ')} WHERE id = ?`, ...args, l.id); db.audit(actor, 'lead.update', 'lead', l.id, changed); }
  return out(mustGet(id));
}
function addNote(actor, id, body) {
  const l = mustGet(id), text = String(body || '').trim().slice(0, 2000);
  if (!text) throw fail(400, 'Write a note first.');
  db.run('INSERT INTO lead_notes (lead_id,author_id,author_name,body,created_at) VALUES (?,?,?,?,?)', l.id, actor.id || null, actor.name, text, db.now());
  db.audit(actor, 'lead.note', 'lead', l.id, {});
  return out(mustGet(id));
}
function csv(brandId) {
  const cell = (v) => { let s = String(v ?? ''); if (/^[=+\-@\t\r]/.test(s) && !/^\+[\d\s().-]+$/.test(s)) s = "'" + s; return '"' + s.replace(/"/g, '""') + '"'; }; // neutralise spreadsheet formulas
  const rows = list(brandId, {}).map((l) => [l.received_at, l.name, l.email, l.phone, l.company, l.action, l.status, l.source_page, l.notes.map((n) => n.body).join(' | ')].map(cell).join(','));
  return ['received_at,name,email,phone,company,action,status,source_page,notes'].concat(rows).join('\n') + '\n';
}

module.exports = { ingest, list, update, addNote, csv, STATUSES };
