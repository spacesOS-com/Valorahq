'use strict';
/* Published content lives in the site repository; a publish is one commit, and the existing
   GitHub -> Dokploy flow deploys it.
   github: commit through the GitHub API (production).
   local:  write into this working tree and rerun the build (development). */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = () => process.env.CMS_SITE_ROOT || path.resolve(__dirname, '..', '..');
const mode = () => (process.env.CMS_STORAGE === 'github' ? 'github' : 'local');
const repo = () => process.env.CMS_GITHUB_REPO || 'spacesOS-com/Valorahq';
const branch = () => process.env.CMS_GITHUB_BRANCH || 'main';
const fail = (status, message) => Object.assign(new Error(message), { status });

async function gh(method, url, body) {
  const token = process.env.CMS_GITHUB_TOKEN;
  if (!token) throw fail(503, 'CMS_GITHUB_TOKEN is not set.');
  const res = await fetch(`https://api.github.com/repos/${repo()}${url}`, {
    method,
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'valora-cms', ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (_) { /* non-JSON error body */ }
  return { status: res.status, data };
}

const localSha = (text) => crypto.createHash('sha1').update(text).digest('hex');

async function list(dir, ext) {
  if (mode() === 'local') {
    const full = path.join(ROOT(), dir);
    return fs.existsSync(full) ? fs.readdirSync(full).filter((f) => f.endsWith(ext)).map((f) => f.slice(0, -ext.length)) : [];
  }
  const r = await gh('GET', `/contents/${dir}?ref=${encodeURIComponent(branch())}`);
  if (r.status === 404) return [];
  if (r.status !== 200 || !Array.isArray(r.data)) throw fail(502, 'Could not list files from GitHub.');
  return r.data.filter((f) => f.type === 'file' && f.name.endsWith(ext)).map((f) => f.name.slice(0, -ext.length));
}

/* -> { text, sha } or null */
async function read(file) {
  if (mode() === 'local') {
    const full = path.join(ROOT(), file);
    if (!fs.existsSync(full)) return null;
    const text = fs.readFileSync(full, 'utf8');
    return { text, sha: localSha(text) };
  }
  const r = await gh('GET', `/contents/${file}?ref=${encodeURIComponent(branch())}`);
  if (r.status === 404) return null;
  if (r.status !== 200 || !r.data || typeof r.data.content !== 'string') throw fail(502, 'Could not read the file from GitHub.');
  return { text: Buffer.from(r.data.content, 'base64').toString('utf8'), sha: r.data.sha };
}

/* One atomic commit. files: [{ path, data: string | Buffer | null }] (null deletes).
   expect: optional { path, sha } optimistic check for single-file edits. -> { url } */
async function commit(files, message, user, expect) {
  if (mode() === 'local') {
    if (expect) {
      const cur = await read(expect.path);
      if (Boolean(cur) !== Boolean(expect.sha) || (cur && cur.sha !== expect.sha)) throw fail(409, 'conflict');
    }
    for (const f of files) {
      const full = path.join(ROOT(), f.path);
      if (!full.startsWith(ROOT())) throw fail(400, 'Bad path.');
      if (f.data === null) { if (fs.existsSync(full)) fs.unlinkSync(full); continue; }
      fs.mkdirSync(path.dirname(full), { recursive: true });
      fs.writeFileSync(full, f.data);
    }
    rebuildLocal();
    return { url: null };
  }
  if (expect) {
    const cur = await read(expect.path);
    if (Boolean(cur) !== Boolean(expect.sha) || (cur && cur.sha !== expect.sha)) throw fail(409, 'conflict');
  }
  const ref = await gh('GET', `/git/ref/heads/${branch()}`);
  if (ref.status !== 200) throw fail(502, 'Could not read the branch from GitHub.');
  const parent = ref.data.object.sha;
  const base = await gh('GET', `/git/commits/${parent}`);
  if (base.status !== 200) throw fail(502, 'Could not read the latest commit.');
  const tree = [];
  for (const f of files) {
    if (f.data === null) { tree.push({ path: f.path, mode: '100644', type: 'blob', sha: null }); continue; }
    const blob = await gh('POST', '/git/blobs', { content: Buffer.from(f.data).toString('base64'), encoding: 'base64' });
    if (blob.status !== 201) throw fail(502, 'GitHub refused a file.');
    tree.push({ path: f.path, mode: '100644', type: 'blob', sha: blob.data.sha });
  }
  const made = await gh('POST', '/git/trees', { base_tree: base.data.tree.sha, tree });
  if (made.status !== 201) throw fail(502, 'GitHub refused the change set.');
  const c = await gh('POST', '/git/commits', { message, tree: made.data.sha, parents: [parent],
    author: { name: user.name, email: user.email || 'cms@valorahq.com' }, committer: { name: 'Valora CMS', email: 'cms@valorahq.com' } });
  if (c.status !== 201) throw fail(502, 'GitHub refused the commit.');
  const moved = await gh('PATCH', `/git/refs/heads/${branch()}`, { sha: c.data.sha });
  if (moved.status === 422) throw fail(409, 'The site changed while publishing. Try again.');
  if (moved.status !== 200) throw fail(502, 'GitHub refused to update the branch. If it is protected, allow the CMS token to push.');
  return { url: c.data.html_url };
}

function rebuildLocal() {
  const { spawnSync } = require('child_process');
  const r = spawnSync('python3', ['_build/build.py'], { cwd: ROOT(), encoding: 'utf8', env: { ...process.env, VALORA_CONVERSATION_UI_ENABLED: 'true' } });
  if (r.status !== 0) throw fail(500, 'The site build failed: ' + String(r.stderr || '').trim().split('\n').slice(-2).join(' '));
}

/* Dokploy deploys on push; an explicit hook makes it immediate and gives us a failure to report. */
async function triggerDeploy() {
  const hook = process.env.CMS_DEPLOY_HOOK_URL;
  if (!hook || mode() === 'local') return { triggered: false };
  try {
    const res = await fetch(hook, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ref: `refs/heads/${branch()}` }) });
    return { triggered: res.ok, status: res.status };
  } catch (e) { return { triggered: false, error: e.message }; }
}

module.exports = { list, read, commit, triggerDeploy, mode, ROOT };
