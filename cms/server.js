#!/usr/bin/env node
/* Valora CMS server. Serves the editor at /cms/, the admin API at /api/cms/v1/ and the MCP
   endpoint at /api/cms/mcp. In production Dokploy routes those two path prefixes on
   valorahq.com to this service. Run locally with `node cms/server.js` (see cms/README.md);
   locally it also serves the built site so previews and published pages can be opened. */
const http = require('http');
const fs = require('fs');
const path = require('path');

const SITE_ROOT = process.env.CMS_SITE_ROOT || path.resolve(__dirname, '..');
process.env.CMS_SITE_ROOT = SITE_ROOT;
process.env.CMS_DB_PATH = process.env.CMS_DB_PATH || path.join(SITE_ROOT, 'cms-data', 'cms.sqlite');
if ((process.env.CMS_SESSION_SECRET || '').length < 32) { console.error('Set CMS_SESSION_SECRET (32+ random characters).'); process.exit(1); }

const { handle } = require('./server/app');
const auth = require('./server/auth');
const publisher = require('./server/publish');
const store = require('./server/store');
auth.bootstrap();

const PORT = Number(process.env.PORT || 8000);
const UI = path.join(__dirname, 'ui');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp',
  '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };

function serveFile(res, root, rel, headers = {}) {
  let file = path.normalize(path.join(root, rel));
  if (file !== root && !file.startsWith(root + path.sep)) { res.statusCode = 403; return res.end('Forbidden'); }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!fs.existsSync(file)) { res.statusCode = 404; return res.end('Not found'); }
  res.setHeader('Content-Type', TYPES[path.extname(file)] || 'application/octet-stream');
  res.setHeader('Cache-Control', 'no-store');
  for (const [k, v] of Object.entries(headers)) res.setHeader(k, v);
  fs.createReadStream(file).pipe(res);
}

http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const p = decodeURIComponent(url.pathname);
  if (p === '/api/cms' || p.startsWith('/api/cms/')) return handle(req, res);
  if (p === '/cms') { res.statusCode = 302; res.setHeader('Location', '/cms/'); return res.end(); }
  if (p.startsWith('/cms/')) {
    return serveFile(res, UI, p.slice(5) || 'index.html', { 'X-Robots-Tag': 'noindex, nofollow', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'same-origin',
      'Content-Security-Policy': "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: blob: https:; frame-src 'self'; object-src 'none'; base-uri 'none'" });
  }
  // Local development only: the built site, so previews resolve /assets/ and published pages open.
  if (store.mode() === 'local') {
    if (/^\/(cms-data|\.git|\.claude|cms)(\/|$)/.test(p) || /\.sqlite/.test(p)) { res.statusCode = 404; return res.end('Not found'); }
    return serveFile(res, SITE_ROOT, p);
  }
  res.statusCode = 404; res.end('Not found');
}).listen(PORT, () => console.log(`Valora CMS on http://localhost:${PORT}/cms/  (storage: ${store.mode()})`));

// AI visibility is measured once a day per engine; the check below is cheap when nothing is due.
setInterval(() => { require('./server/visibility').runAllDue().catch((e) => console.error('[cms] visibility', e.message)); }, 6 * 3600 * 1000).unref();
// Scheduled posts go out within a minute of their time.
setInterval(() => { publisher.runDue().catch((e) => console.error('[cms] scheduler', e.message)); }, 60 * 1000).unref();
