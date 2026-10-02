'use strict';
/* Staff accounts and agent tokens. People sign in with email + password and get a signed,
   HttpOnly session cookie. Agents use a personal API token (Bearer) that carries the same
   role as the staff member it belongs to, so every action is attributable to someone. */
const crypto = require('crypto');
const db = require('./db');

const SESSION_HOURS = 12;
const ROLES = ['writer', 'qa', 'admin'];
const fail = (status, message) => Object.assign(new Error(message), { status });
const secret = () => {
  const s = process.env.CMS_SESSION_SECRET || '';
  if (s.length < 32) throw fail(503, 'CMS_SESSION_SECRET is not set (32+ characters).');
  return s;
};
const sign = (text) => crypto.createHmac('sha256', secret()).update(text).digest('base64url');
const safeEqual = (a, b) => {
  const x = Buffer.from(String(a)), y = Buffer.from(String(b));
  return x.length === y.length && crypto.timingSafeEqual(x, y);
};
const sha256 = (s) => crypto.createHash('sha256').update(s).digest('hex');

function hashPassword(password, salt = crypto.randomBytes(16).toString('hex')) {
  return `scrypt:${salt}:${crypto.scryptSync(String(password), salt, 64).toString('hex')}`;
}
function checkPassword(password, stored) {
  const [scheme, salt, hash] = String(stored || '').split(':');
  if (scheme !== 'scrypt' || !salt || !hash) return false;
  return safeEqual(hashPassword(password, salt), stored);
}

const publicUser = (u) => u && ({ id: u.id, email: u.email, name: u.name, role: u.role, persona: u.persona, active: Boolean(u.active) });

/* First run: create the first admin from the environment so nobody has to touch the database. */
function bootstrap() {
  db.open();
  if (db.get('SELECT COUNT(*) AS n FROM users').n > 0) return;
  const email = process.env.CMS_BOOTSTRAP_ADMIN_EMAIL, password = process.env.CMS_BOOTSTRAP_ADMIN_PASSWORD || '';
  if (!email || password.length < 12) {
    console.warn('[cms] No users yet. Set CMS_BOOTSTRAP_ADMIN_EMAIL and CMS_BOOTSTRAP_ADMIN_PASSWORD (12+ characters) and restart.');
    return;
  }
  db.run('INSERT INTO users (email,name,role,persona,password_hash,active,created_at) VALUES (?,?,?,?,?,1,?)',
    email, process.env.CMS_BOOTSTRAP_ADMIN_NAME || 'Admin', 'admin', '', hashPassword(password), db.now());
  db.audit(null, 'user.bootstrap', 'user', email, {});
}

const attempts = new Map();
function throttled(key) {
  const t = Date.now(), rec = attempts.get(key) || { n: 0, at: t };
  if (t - rec.at > 15 * 60 * 1000) { rec.n = 0; rec.at = t; }
  rec.n += 1; attempts.set(key, rec);
  return rec.n > 8;
}

function login(email, password) {
  const key = String(email || '').trim().toLowerCase();
  if (!key || typeof password !== 'string') return null;
  if (throttled(key)) throw fail(429, 'Too many attempts. Try again in 15 minutes.');
  const user = db.get('SELECT * FROM users WHERE email = ? AND active = 1', key);
  const ok = checkPassword(password, user ? user.password_hash : hashPassword('x', '00')); // same work either way
  if (!user || !ok) { db.audit({ name: key, via: 'ui' }, 'login.failed', 'user', key, {}); return null; }
  attempts.delete(key);
  db.audit({ ...user, via: 'ui' }, 'login', 'user', user.id, {});
  return publicUser(user);
}

function sessionCookie(user, secure) {
  const body = Buffer.from(JSON.stringify({ id: user.id, exp: Date.now() + SESSION_HOURS * 3600 * 1000 })).toString('base64url');
  return `cms_session=${body}.${sign(body)}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${SESSION_HOURS * 3600}${secure ? '; Secure' : ''}`;
}
const clearCookie = (secure) => `cms_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0${secure ? '; Secure' : ''}`;

/* -> { ...user, via: 'ui' | 'api' } or null. Bearer tokens win over cookies. */
function identify(req) {
  const bearer = /^Bearer\s+(\S+)$/.exec(req.headers.authorization || '');
  if (bearer) {
    const row = db.get(`SELECT t.id AS token_id, u.* FROM api_tokens t JOIN users u ON u.id = t.user_id
                        WHERE t.token_hash = ? AND t.revoked_at IS NULL AND u.active = 1`, sha256(bearer[1]));
    if (!row) return null;
    db.run('UPDATE api_tokens SET last_used_at = ? WHERE id = ?', db.now(), row.token_id);
    return { ...publicUser(row), via: 'api' };
  }
  const m = /(?:^|;\s*)cms_session=([^;]+)/.exec(req.headers.cookie || '');
  if (!m) return null;
  const [body, mac] = m[1].split('.');
  if (!body || !mac || !safeEqual(sign(body), mac)) return null;
  let data;
  try { data = JSON.parse(Buffer.from(body, 'base64url').toString()); } catch (_) { return null; }
  if (!data || data.exp < Date.now()) return null;
  const user = db.get('SELECT * FROM users WHERE id = ? AND active = 1', data.id);
  return user ? { ...publicUser(user), via: 'ui' } : null;
}

function createUser(actor, { email, name, role, persona, password }) {
  email = String(email || '').trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) throw fail(400, 'Enter a valid email.');
  if (!String(name || '').trim()) throw fail(400, 'Enter a name.');
  if (!ROLES.includes(role)) throw fail(400, 'Role must be writer, qa or admin.');
  if (String(password || '').length < 12) throw fail(400, 'The password needs at least 12 characters.');
  if (db.get('SELECT 1 FROM users WHERE email = ?', email)) throw fail(409, 'Someone with that email already exists.');
  const r = db.run('INSERT INTO users (email,name,role,persona,password_hash,active,created_at) VALUES (?,?,?,?,?,1,?)',
    email, String(name).trim(), role, String(persona || '').trim(), hashPassword(password), db.now());
  db.audit(actor, 'user.create', 'user', r.lastInsertRowid, { email, role });
  return publicUser(db.get('SELECT * FROM users WHERE id = ?', r.lastInsertRowid));
}

function updateUser(actor, id, patch) {
  const user = db.get('SELECT * FROM users WHERE id = ?', id);
  if (!user) throw fail(404, 'User not found.');
  const next = { name: user.name, role: user.role, persona: user.persona, active: user.active, password_hash: user.password_hash };
  if (patch.name !== undefined) next.name = String(patch.name).trim() || user.name;
  if (patch.persona !== undefined) next.persona = String(patch.persona).trim();
  if (patch.role !== undefined) { if (!ROLES.includes(patch.role)) throw fail(400, 'Role must be writer, qa or admin.'); next.role = patch.role; }
  if (patch.active !== undefined) next.active = patch.active ? 1 : 0;
  if (patch.password !== undefined) { if (String(patch.password).length < 12) throw fail(400, 'The password needs at least 12 characters.'); next.password_hash = hashPassword(patch.password); }
  const losingAdmin = user.role === 'admin' && user.active && (next.role !== 'admin' || !next.active);
  if (losingAdmin && db.get("SELECT COUNT(*) AS n FROM users WHERE role = 'admin' AND active = 1").n <= 1) throw fail(400, 'There must be at least one active admin.');
  db.run('UPDATE users SET name=?, role=?, persona=?, active=?, password_hash=? WHERE id=?', next.name, next.role, next.persona, next.active, next.password_hash, id);
  if (!next.active) db.run('UPDATE api_tokens SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL', db.now(), id);
  db.audit(actor, 'user.update', 'user', id, { fields: Object.keys(patch).filter((k) => k !== 'password').concat(patch.password !== undefined ? ['password'] : []) });
  return publicUser(db.get('SELECT * FROM users WHERE id = ?', id));
}

/* The token is returned once; only its hash is stored. */
function createToken(actor, userId, name) {
  const user = db.get('SELECT * FROM users WHERE id = ? AND active = 1', userId);
  if (!user) throw fail(404, 'User not found.');
  const token = 'vcms_' + crypto.randomBytes(30).toString('base64url');
  const r = db.run('INSERT INTO api_tokens (user_id,name,token_hash,created_at) VALUES (?,?,?,?)', userId, String(name || 'token').slice(0, 80), sha256(token), db.now());
  db.audit(actor, 'token.create', 'token', r.lastInsertRowid, { for: user.email, name });
  return { id: Number(r.lastInsertRowid), token, name, user: user.email };
}
function revokeToken(actor, id) {
  const r = db.run('UPDATE api_tokens SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL', db.now(), id);
  if (!r.changes) throw fail(404, 'Token not found.');
  db.audit(actor, 'token.revoke', 'token', id, {});
}
const listUsers = () => db.all('SELECT * FROM users ORDER BY name').map(publicUser);
const listTokens = () => db.all(`SELECT t.id, t.name, t.created_at, t.last_used_at, u.email AS user, u.role FROM api_tokens t
                                 JOIN users u ON u.id = t.user_id WHERE t.revoked_at IS NULL ORDER BY t.id DESC`);

module.exports = { bootstrap, login, identify, sessionCookie, clearCookie, hashPassword, sign, safeEqual, sha256,
  createUser, updateUser, listUsers, createToken, revokeToken, listTokens, ROLES };
