'use strict';
/* AI crawler analytics: which AI bots read which pages. Fed with web-server access log lines
   (nginx "combined" format); only requests from known AI crawlers are counted, and nothing about
   human visitors is stored. */
const db = require('./db');
const growth = require('./growth');

const BOTS = [
  ['GPTBot', /GPTBot/i, 'OpenAI training crawler'], ['OAI-SearchBot', /OAI-SearchBot/i, 'ChatGPT search index'], ['ChatGPT-User', /ChatGPT-User/i, 'ChatGPT fetching a page for a user'],
  ['ClaudeBot', /ClaudeBot|anthropic-ai/i, 'Anthropic crawler'], ['Claude-User', /Claude-User/i, 'Claude fetching a page for a user'], ['Claude-SearchBot', /Claude-SearchBot/i, 'Claude search index'],
  ['PerplexityBot', /PerplexityBot/i, 'Perplexity index'], ['Perplexity-User', /Perplexity-User/i, 'Perplexity fetching a page for a user'],
  ['Google-Extended', /Google-Extended/i, 'Google AI training control'], ['Applebot-Extended', /Applebot-Extended/i, 'Apple AI training'],
  ['Bytespider', /Bytespider/i, 'ByteDance crawler'], ['Amazonbot', /Amazonbot/i, 'Amazon crawler'], ['Meta-ExternalAgent', /meta-externalagent/i, 'Meta AI crawler'],
  ['CCBot', /CCBot/i, 'Common Crawl'], ['DuckAssistBot', /DuckAssistBot/i, 'DuckDuckGo AI answers'], ['MistralAI-User', /MistralAI-User/i, 'Mistral fetching a page for a user'],
];
const MONTHS = { Jan: '01', Feb: '02', Mar: '03', Apr: '04', May: '05', Jun: '06', Jul: '07', Aug: '08', Sep: '09', Oct: '10', Nov: '11', Dec: '12' };
const LINE = /\[(\d{2})\/([A-Za-z]{3})\/(\d{4}):[^\]]*\]\s+"(?:GET|HEAD)\s+(\S+)[^"]*"\s+(\d{3})\s+\S+\s+"[^"]*"\s+"([^"]*)"/;

function ingest(actor, brandId, text) {
  const b = growth.brand(brandId), counts = new Map();
  let lines = 0, matched = 0;
  for (const line of String(text || '').split('\n')) {
    if (!line) continue;
    lines++;
    const m = LINE.exec(line);
    if (!m || m[5][0] !== '2' || !MONTHS[m[2]]) continue;
    const bot = BOTS.find(([, re]) => re.test(m[6]));
    if (!bot) continue;
    const path = m[4].split('?')[0].slice(0, 300);
    if (/\.(css|js|png|jpe?g|webp|svg|ico|woff2?|map)$/i.test(path)) continue;
    const key = `${m[3]}-${MONTHS[m[2]]}-${m[1]}\t${bot[0]}\t${path}`;
    counts.set(key, (counts.get(key) || 0) + 1); matched++;
  }
  for (const [key, hits] of counts) {
    const [day, bot, path] = key.split('\t');
    db.run('INSERT INTO crawler_hits (brand_id,day,bot,path,hits) VALUES (?,?,?,?,?) ON CONFLICT(brand_id,day,bot,path) DO UPDATE SET hits = hits + excluded.hits', b.id, day, bot, path, hits);
  }
  db.audit(actor, 'crawlers.ingest', 'brand', b.id, { lines, matched });
  return { lines, matched };
}

function report(brandId, days = 30) {
  const b = growth.brand(brandId), since = new Date(Date.now() - days * 24 * 3600 * 1000).toISOString().slice(0, 10);
  const info = Object.fromEntries(BOTS.map(([name, , what]) => [name, what]));
  return { days,
    total: db.get('SELECT COALESCE(SUM(hits),0) AS n FROM crawler_hits WHERE brand_id = ? AND day >= ?', b.id, since).n,
    bots: db.all('SELECT bot, SUM(hits) AS hits, COUNT(DISTINCT path) AS pages, MAX(day) AS last_seen FROM crawler_hits WHERE brand_id = ? AND day >= ? GROUP BY bot ORDER BY hits DESC', b.id, since).map((r) => ({ ...r, what: info[r.bot] || '' })),
    pages: db.all('SELECT path, SUM(hits) AS hits, COUNT(DISTINCT bot) AS bots FROM crawler_hits WHERE brand_id = ? AND day >= ? GROUP BY path ORDER BY hits DESC LIMIT 50', b.id, since),
    by_day: db.all('SELECT day, SUM(hits) AS hits FROM crawler_hits WHERE brand_id = ? AND day >= ? GROUP BY day ORDER BY day', b.id, since) };
}

module.exports = { ingest, report };
