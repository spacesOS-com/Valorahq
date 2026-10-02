'use strict';
/* AI visibility: ask AI assistants the questions buyers ask and record whether the brand is in
   the answer, who else is, and what was cited. Each engine needs its own key; only configured
   engines run. Answers are stored so every number on the dashboard can be traced to its source.
     Claude      ANTHROPIC_API_KEY                         (CMS_VIS_CLAUDE_MODEL, default claude-sonnet-5-5)
     ChatGPT     OPENAI_API_KEY      + CMS_VIS_OPENAI_MODEL
     Perplexity  PERPLEXITY_API_KEY  + CMS_VIS_PERPLEXITY_MODEL
     Gemini      GEMINI_API_KEY      + CMS_VIS_GEMINI_MODEL
   CMS_AI_MOCK=1 adds a "Mock" engine with canned answers for local testing. */
const db = require('./db');
const growth = require('./growth');

const fail = (status, message) => Object.assign(new Error(message), { status });
const J = (v, d) => { try { return JSON.parse(v); } catch (_) { return d; } };
const urlsIn = (text) => [...new Set((String(text).match(/https?:\/\/[^\s)\]>"']+/g) || []).map((u) => u.replace(/[.,;:]+$/, '')))].slice(0, 20);

async function post(url, headers, body) {
  const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`engine returned ${res.status}`);
  return res.json();
}

const ENGINES = {
  claude: { label: 'Claude', ready: () => Boolean(process.env.ANTHROPIC_API_KEY), model: () => process.env.CMS_VIS_CLAUDE_MODEL || 'claude-sonnet-5-5',
    async ask(q, model) {
      const d = await post('https://api.anthropic.com/v1/messages', { 'x-api-key': process.env.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01' },
        { model, max_tokens: 1200, messages: [{ role: 'user', content: q }] });
      const text = (d.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('\n');
      return { text, citations: urlsIn(text) };
    } },
  chatgpt: { label: 'ChatGPT', ready: () => Boolean(process.env.OPENAI_API_KEY && process.env.CMS_VIS_OPENAI_MODEL), model: () => process.env.CMS_VIS_OPENAI_MODEL,
    async ask(q, model) {
      const d = await post('https://api.openai.com/v1/chat/completions', { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` }, { model, messages: [{ role: 'user', content: q }] });
      const text = String((((d.choices || [])[0] || {}).message || {}).content || '');
      return { text, citations: urlsIn(text) };
    } },
  perplexity: { label: 'Perplexity', ready: () => Boolean(process.env.PERPLEXITY_API_KEY && process.env.CMS_VIS_PERPLEXITY_MODEL), model: () => process.env.CMS_VIS_PERPLEXITY_MODEL,
    async ask(q, model) {
      const d = await post('https://api.perplexity.ai/chat/completions', { Authorization: `Bearer ${process.env.PERPLEXITY_API_KEY}` }, { model, messages: [{ role: 'user', content: q }] });
      const text = String((((d.choices || [])[0] || {}).message || {}).content || '');
      return { text, citations: [...new Set([...(Array.isArray(d.citations) ? d.citations.map(String) : []), ...urlsIn(text)])].slice(0, 20) };
    } },
  gemini: { label: 'Gemini', ready: () => Boolean(process.env.GEMINI_API_KEY && process.env.CMS_VIS_GEMINI_MODEL), model: () => process.env.CMS_VIS_GEMINI_MODEL,
    async ask(q, model) {
      const d = await post(`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`, { 'x-goog-api-key': process.env.GEMINI_API_KEY },
        { contents: [{ parts: [{ text: q }] }] });
      const text = ((((d.candidates || [])[0] || {}).content || {}).parts || []).map((p) => p.text || '').join('\n');
      return { text, citations: urlsIn(text) };
    } },
  mock: { label: 'Mock', ready: () => process.env.CMS_AI_MOCK === '1', model: () => 'mock',
    async ask(q) {
      const text = /pilot/i.test(q) ? 'For pilots, firms often mentioned include Valora (https://www.valorahq.com/financial-advisor-for-airline-pilots/) and SmartAsset.'
        : 'Commonly suggested options are SmartAsset (https://smartasset.com/) and NerdWallet. Check any adviser on the SEC IAPD site.';
      return { text, citations: urlsIn(text) };
    } },
};
const engines = () => Object.entries(ENGINES).filter(([, e]) => e.ready()).map(([key, e]) => ({ key, label: e.label, model: e.model() }));

/* Where each name first appears decides the order ("position") in the answer. */
function analyse(b, text, citations) {
  const lower = text.toLowerCase();
  const first = (names, domains) => {
    let at = -1;
    for (const n of names.concat(domains)) { const i = n ? lower.indexOf(String(n).toLowerCase()) : -1; if (i !== -1 && (at === -1 || i < at)) at = i; }
    if (at === -1 && citations.some((c) => domains.some((d) => growth.hostOf(c) === d || growth.hostOf(c).endsWith('.' + d)))) at = text.length;
    return at;
  };
  const own = first(b.aliases.length ? b.aliases : [b.name], b.domains);
  const comps = b.competitors.map((c) => ({ name: c.name, at: first([c.name], c.domains || []) })).filter((c) => c.at !== -1);
  const order = [...(own !== -1 ? [{ own: true, at: own }] : []), ...comps].sort((x, y) => x.at - y.at);
  return { mentioned: own !== -1, position: own !== -1 ? order.findIndex((o) => o.own) + 1 : null, competitors: comps.sort((x, y) => x.at - y.at).map((c) => c.name) };
}

const listPrompts = (brandId) => db.all('SELECT * FROM prompts WHERE brand_id = ? ORDER BY id', growth.brand(brandId).id).map((p) => ({ id: p.id, text: p.text, active: Boolean(p.active) }));
function addPrompts(actor, brandId, items) {
  const b = growth.brand(brandId);
  const list = (Array.isArray(items) ? items : String(items || '').split('\n')).map((t) => String(t).trim().replace(/\s+/g, ' ').slice(0, 300)).filter((t) => t.length >= 8).slice(0, 100);
  let added = 0;
  for (const t of list) added += db.run('INSERT OR IGNORE INTO prompts (brand_id,text,created_at) VALUES (?,?,?)', b.id, t, db.now()).changes;
  if (added) db.audit(actor, 'prompts.add', 'brand', b.id, { added });
  return { added };
}
function removePrompt(actor, id) {
  if (!db.run('DELETE FROM prompts WHERE id = ?', Number(id)).changes) throw fail(404, 'Prompt not found.');
  db.audit(actor, 'prompt.delete', 'prompt', id, {});
}

/* One pass: every active prompt on every configured engine, at most once per engine per day. */
async function run(actor, brandId, { force } = {}) {
  const b = growth.brand(brandId), active = engines();
  if (!active.length) throw fail(503, 'No AI engine is set up for tracking yet. Add an API key for at least one.');
  const day = new Date().toISOString().slice(0, 10);
  let ran = 0, failed = 0;
  for (const p of db.all('SELECT * FROM prompts WHERE brand_id = ? AND active = 1 LIMIT 100', b.id)) {
    for (const e of active) {
      if (!force && db.get('SELECT 1 AS x FROM prompt_runs WHERE prompt_id = ? AND provider = ? AND day = ?', p.id, e.key, day)) continue;
      try {
        const { text, citations } = await ENGINES[e.key].ask(p.text, e.model);
        const a = analyse(b, text, citations);
        db.run('INSERT INTO prompt_runs (prompt_id,provider,model,ran_at,day,answer,mentioned,position,competitors,citations) VALUES (?,?,?,?,?,?,?,?,?,?)',
          p.id, e.key, e.model, db.now(), day, text.slice(0, 12000), a.mentioned ? 1 : 0, a.position, JSON.stringify(a.competitors), JSON.stringify(citations));
        ran++;
      } catch (err) {
        db.run('INSERT INTO prompt_runs (prompt_id,provider,model,ran_at,day,error) VALUES (?,?,?,?,?,?)', p.id, e.key, e.model, db.now(), day, String(err.message).slice(0, 300));
        failed++;
      }
    }
  }
  db.audit(actor, 'visibility.run', 'brand', b.id, { ran, failed });
  return { ran, failed, engines: active.map((e) => e.label) };
}

function report(brandId, days = 30) {
  const b = growth.brand(brandId), since = new Date(Date.now() - days * 24 * 3600 * 1000).toISOString().slice(0, 10);
  const rows = db.all(`SELECT r.*, p.text FROM prompt_runs r JOIN prompts p ON p.id = r.prompt_id WHERE p.brand_id = ? AND r.day >= ? ORDER BY r.id DESC`, b.id, since);
  const ok = rows.filter((r) => !r.error);
  const rate = (list) => (list.length ? Math.round(100 * list.filter((r) => r.mentioned).length / list.length) : null);
  const byEngine = engines().map((e) => { const mine = ok.filter((r) => r.provider === e.key); return { key: e.key, label: e.label, model: e.model, runs: mine.length, rate: rate(mine) }; });
  const voice = new Map([[b.name, ok.filter((r) => r.mentioned).length]]);
  const cited = new Map();
  for (const r of ok) {
    for (const c of J(r.competitors, [])) voice.set(c, (voice.get(c) || 0) + 1);
    for (const u of J(r.citations, [])) { const h = growth.hostOf(u); if (h) cited.set(h, (cited.get(h) || 0) + 1); }
  }
  const byDay = [...new Set(ok.map((r) => r.day))].sort().map((d) => ({ day: d, rate: rate(ok.filter((r) => r.day === d)), runs: ok.filter((r) => r.day === d).length }));
  const prompts = listPrompts(b.id).map((p) => {
    const mine = ok.filter((r) => r.prompt_id === p.id), latest = {};
    for (const r of mine) if (!latest[r.provider]) latest[r.provider] = { provider: r.provider, mentioned: Boolean(r.mentioned), position: r.position, competitors: J(r.competitors, []), citations: J(r.citations, []), answer: r.answer, ran_at: r.ran_at };
    return { ...p, runs: mine.length, rate: rate(mine), latest: Object.values(latest) };
  });
  return { days, engines: byEngine, runs: ok.length, failed: rows.length - ok.length, last_error: (rows.find((r) => r.error) || {}).error || null, rate: rate(ok),
    share_of_voice: [...voice.entries()].map(([name, mentions]) => ({ name, mentions, own: name === b.name })).sort((x, y) => y.mentions - x.mentions),
    cited_domains: [...cited.entries()].map(([domain, count]) => ({ domain, count, own: b.domains.includes(domain) })).sort((x, y) => y.count - x.count).slice(0, 20), by_day: byDay, prompts };
}

async function runAllDue() {
  for (const b of growth.listBrands()) {
    if (!db.get('SELECT 1 AS x FROM prompts WHERE brand_id = ? AND active = 1', b.id) || !engines().length) continue;
    try { await run({ name: 'scheduler', via: 'system' }, b.id); } catch (e) { console.error('[cms] visibility run failed', e.message); }
  }
}

module.exports = { engines, listPrompts, addPrompts, removePrompt, run, report, runAllDue };
