'use strict';
/* Search data comes from outside providers; nothing here is estimated or invented.
   Results (SERP):  Serper.dev        SERPER_API_KEY
   Monthly volume:  DataForSEO        DATAFORSEO_LOGIN + DATAFORSEO_PASSWORD
   Without keys the features still work with numbers entered by hand, imported, or pushed by an agent.
   CMS_SEARCH_MOCK=1 returns canned data for local testing. */
const fail = (status, message) => Object.assign(new Error(message), { status });
const mock = () => process.env.CMS_SEARCH_MOCK === '1';
const serpConfigured = () => mock() || Boolean(process.env.SERPER_API_KEY);
const volumeConfigured = () => mock() || Boolean(process.env.DATAFORSEO_LOGIN && process.env.DATAFORSEO_PASSWORD);

/* -> [{ position, title, url, snippet }] */
async function serp(query) {
  if (mock()) {
    return [
      { position: 1, title: `What to know about ${query}`, url: 'https://www.schwab.com/learn/story/example', snippet: 'Mock result one for local testing.' },
      { position: 2, title: `${query}: a guide`, url: 'https://www.nerdwallet.com/article/example', snippet: 'Mock result two for local testing.' },
      ...(/pilot/i.test(query) ? [{ position: 3, title: 'Financial advisor for airline pilots', url: 'https://www.valorahq.com/financial-advisor-for-airline-pilots/', snippet: 'Mock result on the brand domain.' }] : []),
    ];
  }
  if (!process.env.SERPER_API_KEY) throw fail(503, 'Search results are not set up: add SERPER_API_KEY.');
  const res = await fetch('https://google.serper.dev/search', { method: 'POST',
    headers: { 'X-API-KEY': process.env.SERPER_API_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ q: query, gl: process.env.CMS_SEARCH_COUNTRY || 'us', num: 10 }) });
  if (!res.ok) throw fail(502, `The search provider returned an error (${res.status}).`);
  const data = await res.json();
  return (data.organic || []).slice(0, 10).map((r, i) => ({ position: r.position || i + 1, title: String(r.title || ''), url: String(r.link || ''), snippet: String(r.snippet || '') }));
}

/* -> { [query]: monthlySearches } for the queries the provider knows */
async function volumes(queries) {
  if (mock()) return Object.fromEntries(queries.map((q) => [q.toLowerCase(), 100 + (q.length * 37) % 900]));
  if (!volumeConfigured()) throw fail(503, 'Search volumes are not set up: add DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD.');
  const auth = Buffer.from(`${process.env.DATAFORSEO_LOGIN}:${process.env.DATAFORSEO_PASSWORD}`).toString('base64');
  const res = await fetch('https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live', { method: 'POST',
    headers: { Authorization: `Basic ${auth}`, 'Content-Type': 'application/json' },
    body: JSON.stringify([{ keywords: queries.slice(0, 700), location_code: Number(process.env.CMS_SEARCH_LOCATION_CODE || 2840), language_code: 'en' }]) });
  if (!res.ok) throw fail(502, `The volume provider returned an error (${res.status}).`);
  const data = await res.json();
  const out = {};
  for (const task of data.tasks || []) for (const row of task.result || []) {
    if (row && row.keyword && Number.isFinite(row.search_volume)) out[String(row.keyword).toLowerCase()] = row.search_volume;
  }
  return out;
}

module.exports = { serp, volumes, serpConfigured, volumeConfigured };
