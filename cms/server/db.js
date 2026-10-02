'use strict';
/* SQLite (built into Node) on a persistent volume. One file holds everything that must not
   live in the public repo: staff accounts, drafts, the audit log, brand memory. Published
   content is committed to the repo by publish.js; this database is the system of record for
   work in progress and for who did what. */
const { DatabaseSync } = require('node:sqlite');
const path = require('path');
const fs = require('fs');

let db;
function open() {
  if (db) return db;
  const file = process.env.CMS_DB_PATH || path.join(process.cwd(), 'cms-data', 'cms.sqlite');
  if (file !== ':memory:') fs.mkdirSync(path.dirname(file), { recursive: true });
  db = new DatabaseSync(file);
  db.exec('PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON;');
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE, name TEXT NOT NULL,
      role TEXT NOT NULL CHECK (role IN ('writer','qa','admin')), persona TEXT NOT NULL DEFAULT '',
      password_hash TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS api_tokens (
      id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), name TEXT NOT NULL,
      token_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL, last_used_at TEXT, revoked_at TEXT);
    CREATE TABLE IF NOT EXISTS articles (
      id TEXT PRIMARY KEY, type TEXT NOT NULL CHECK (type IN ('advisor-article','consumer-page')),
      category TEXT NOT NULL DEFAULT '', title TEXT NOT NULL, slug TEXT NOT NULL, body_md TEXT NOT NULL DEFAULT '',
      summary TEXT NOT NULL DEFAULT '', author_persona TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','in-review','approved','scheduled','published')),
      meta_title TEXT NOT NULL DEFAULT '', meta_description TEXT NOT NULL DEFAULT '', canonical TEXT NOT NULL DEFAULT '',
      og_image TEXT NOT NULL DEFAULT '', faqs TEXT NOT NULL DEFAULT '[]', structured_data TEXT NOT NULL DEFAULT '{}',
      key_takeaways TEXT NOT NULL DEFAULT '[]', noindex INTEGER NOT NULL DEFAULT 0,
      illustration_alt TEXT NOT NULL DEFAULT '', slot_date TEXT NOT NULL,
      scheduled_at TEXT, published_at TEXT, published_url TEXT, live INTEGER NOT NULL DEFAULT 0,
      qa_passed_at TEXT, qa_by INTEGER REFERENCES users(id), review_note TEXT NOT NULL DEFAULT '', publish_error TEXT NOT NULL DEFAULT '',
      created_by INTEGER REFERENCES users(id), updated_by INTEGER REFERENCES users(id), created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
      /* Phase 2 hooks: advisor-owned content. No UI yet. */
      advisor_id INTEGER REFERENCES advisors(id), voice_profile_id INTEGER REFERENCES voice_profiles(id),
      compliance_checklist TEXT NOT NULL DEFAULT '[]', advisor_approval TEXT NOT NULL DEFAULT 'not-required',
      syndication TEXT NOT NULL DEFAULT '{}',
      UNIQUE (type, slug));
    CREATE TABLE IF NOT EXISTS illustrations (
      article_id TEXT PRIMARY KEY REFERENCES articles(id) ON DELETE CASCADE, filename TEXT NOT NULL,
      content_type TEXT NOT NULL, data BLOB NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS revisions (
      id INTEGER PRIMARY KEY, article_id TEXT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
      snapshot TEXT NOT NULL, actor_id INTEGER, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit_log (
      id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor_id INTEGER, actor_name TEXT NOT NULL, via TEXT NOT NULL,
      action TEXT NOT NULL, target_type TEXT NOT NULL DEFAULT '', target_id TEXT NOT NULL DEFAULT '', detail TEXT NOT NULL DEFAULT '{}');
    CREATE TABLE IF NOT EXISTS redirects (
      id INTEGER PRIMARY KEY, from_path TEXT NOT NULL UNIQUE, to_path TEXT NOT NULL,
      status_code INTEGER NOT NULL DEFAULT 301, created_by INTEGER, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS routes (
      key TEXT PRIMARY KEY, label TEXT NOT NULL, type TEXT NOT NULL, path_prefix TEXT NOT NULL DEFAULT '',
      page_type TEXT NOT NULL DEFAULT '', position INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    /* Phase 2 hooks */
    CREATE TABLE IF NOT EXISTS advisors (
      id INTEGER PRIMARY KEY, name TEXT NOT NULL, firm TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '',
      website TEXT NOT NULL DEFAULT '', profile_slug TEXT NOT NULL DEFAULT '', publish_endpoint TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS voice_profiles (
      id INTEGER PRIMARY KEY, advisor_id INTEGER NOT NULL REFERENCES advisors(id), name TEXT NOT NULL,
      profile TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS advisor_approvals (
      id INTEGER PRIMARY KEY, article_id TEXT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
      advisor_id INTEGER NOT NULL REFERENCES advisors(id), status TEXT NOT NULL DEFAULT 'pending',
      note TEXT NOT NULL DEFAULT '', decided_at TEXT);
    /* ---- growth: brands (Valora itself and client firms), search opportunities, leads, AI visibility ---- */
    CREATE TABLE IF NOT EXISTS brands (
      id INTEGER PRIMARY KEY, name TEXT NOT NULL, domains TEXT NOT NULL DEFAULT '[]', aliases TEXT NOT NULL DEFAULT '[]',
      competitors TEXT NOT NULL DEFAULT '[]', advisor_id INTEGER REFERENCES advisors(id), is_default INTEGER NOT NULL DEFAULT 0,
      lead_key_hash TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS keywords (
      id INTEGER PRIMARY KEY, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, query TEXT NOT NULL COLLATE NOCASE,
      monthly_searches INTEGER, volume_source TEXT NOT NULL DEFAULT '', intent TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT 'manual',
      visible TEXT NOT NULL DEFAULT 'unknown' CHECK (visible IN ('unknown','no','yes')), position INTEGER,
      serp TEXT NOT NULL DEFAULT '[]', serp_checked_at TEXT, article_id TEXT REFERENCES articles(id) ON DELETE SET NULL,
      page_url TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, UNIQUE (brand_id, query));
    CREATE TABLE IF NOT EXISTS leads (
      id INTEGER PRIMARY KEY, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, received_at TEXT NOT NULL,
      name TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '', company TEXT NOT NULL DEFAULT '',
      action TEXT NOT NULL DEFAULT 'contact', message TEXT NOT NULL DEFAULT '', source_page TEXT NOT NULL DEFAULT '',
      journey TEXT NOT NULL DEFAULT '[]', utm TEXT NOT NULL DEFAULT '{}',
      status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','contacted','qualified','won','lost')),
      spam INTEGER NOT NULL DEFAULT 0, spam_reason TEXT NOT NULL DEFAULT '', assigned_to INTEGER REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS lead_notes (
      id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE, author_id INTEGER, author_name TEXT NOT NULL,
      body TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS prompts (
      id INTEGER PRIMARY KEY, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, text TEXT NOT NULL,
      active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, UNIQUE (brand_id, text));
    CREATE TABLE IF NOT EXISTS prompt_runs (
      id INTEGER PRIMARY KEY, prompt_id INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE, provider TEXT NOT NULL, model TEXT NOT NULL,
      ran_at TEXT NOT NULL, day TEXT NOT NULL, answer TEXT NOT NULL DEFAULT '', mentioned INTEGER NOT NULL DEFAULT 0, position INTEGER,
      competitors TEXT NOT NULL DEFAULT '[]', citations TEXT NOT NULL DEFAULT '[]', error TEXT NOT NULL DEFAULT '');
    CREATE TABLE IF NOT EXISTS crawler_hits (
      brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, day TEXT NOT NULL, bot TEXT NOT NULL, path TEXT NOT NULL,
      hits INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (brand_id, day, bot, path));
    CREATE TABLE IF NOT EXISTS backlinks (
      id INTEGER PRIMARY KEY, brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE, source_url TEXT NOT NULL,
      target_url TEXT NOT NULL DEFAULT '', anchor TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL DEFAULT 'prospect' CHECK (status IN ('prospect','pitched','live','lost')),
      notes TEXT NOT NULL DEFAULT '', live_at TEXT, created_by INTEGER, created_at TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS keywords_brand ON keywords(brand_id);
    CREATE INDEX IF NOT EXISTS leads_brand ON leads(brand_id, received_at);
    CREATE INDEX IF NOT EXISTS runs_prompt ON prompt_runs(prompt_id, day);
    CREATE INDEX IF NOT EXISTS articles_status ON articles(status);
    CREATE INDEX IF NOT EXISTS articles_slot ON articles(slot_date);
    CREATE INDEX IF NOT EXISTS audit_at ON audit_log(at);
  `);
  seed();
  return db;
}

const now = () => new Date().toISOString();

function seed() {
  const routes = [
    ['advisor-article', 'Advisor article', 'advisor-article', '', ''],
    ['profession', 'Profession page', 'consumer-page', '', 'niche-profession'],
    ['specialty', 'Specialty page', 'consumer-page', '', 'niche-profession'],
    ['city', 'City page', 'consumer-page', '', 'city'],
    ['competitor-alternative', 'Competitor alternative page', 'consumer-page', 'alternatives', 'niche-profession'],
  ];
  const ins = db.prepare('INSERT OR IGNORE INTO routes (key,label,type,path_prefix,page_type,position) VALUES (?,?,?,?,?,?)');
  routes.forEach((r, i) => ins.run(...r, i));
  if (!db.prepare('SELECT COUNT(*) AS n FROM brands').get().n) {
    db.prepare('INSERT INTO brands (name,domains,aliases,competitors,is_default,created_at) VALUES (?,?,?,?,1,?)')
      .run('Valora', JSON.stringify(['valorahq.com']), JSON.stringify(['Valora', 'ValoraHQ']), '[]', now());
  }
}

const all = (sql, ...args) => open().prepare(sql).all(...args);
const get = (sql, ...args) => open().prepare(sql).get(...args);
const run = (sql, ...args) => open().prepare(sql).run(...args);

function setting(key, fallback) {
  const row = get('SELECT value FROM settings WHERE key = ?', key);
  if (!row) return fallback;
  try { return JSON.parse(row.value); } catch (_) { return fallback; }
}
function setSetting(key, value) {
  run('INSERT INTO settings (key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value = excluded.value', key, JSON.stringify(value));
}

function audit(actor, action, targetType, targetId, detail) {
  run('INSERT INTO audit_log (at,actor_id,actor_name,via,action,target_type,target_id,detail) VALUES (?,?,?,?,?,?,?,?)',
    now(), actor && actor.id ? actor.id : null, actor ? actor.name : 'system', actor ? (actor.via || 'ui') : 'system',
    action, targetType || '', String(targetId || ''), JSON.stringify(detail || {}));
}

module.exports = { open, all, get, run, now, setting, setSetting, audit };
