'use strict';
/* Markdown -> HTML for article bodies. Raw HTML in the source is escaped, never passed through,
   so the output is safe by construction. Supports headings, paragraphs, bold, italic, links,
   images, lists, block quotes, tables, code and horizontal rules.
   Outbound links can be tagged with UTM parameters at render time. */
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const URL_OK = /^(https?:\/\/|\/|#|mailto:)/i;

function tagLink(href, opts) {
  if (!opts || !opts.utm || !/^https?:\/\//i.test(href)) return href;
  let url;
  try { url = new URL(href); } catch (_) { return href; }
  const own = (opts.ownHosts || []).some((h) => url.hostname === h || url.hostname.endsWith('.' + h));
  if (own) return href;
  for (const [k, v] of Object.entries(opts.utm)) if (v && !url.searchParams.has(k)) url.searchParams.set(k, v);
  return url.toString();
}

function inline(text, opts) {
  const stash = [];
  const keep = (html) => `\u0000${stash.push(html) - 1}\u0000`;
  let s = String(text);
  s = s.replace(/`([^`]+)`/g, (_, c) => keep(`<code>${esc(c)}</code>`));
  s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (m, alt, src) => (URL_OK.test(src) ? keep(`<img src="${esc(src)}" alt="${esc(alt)}" loading="lazy">`) : m));
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, label, href) => {
    if (!URL_OK.test(href)) return m;
    const out = tagLink(href, opts), external = /^https?:\/\//i.test(href) && out !== href || (/^https?:\/\//i.test(href) && !(opts && (opts.ownHosts || []).some((h) => href.includes('//' + h) || href.includes('.' + h))));
    return keep(`<a href="${esc(out)}"${external ? ' target="_blank" rel="noopener"' : ''}>`) + label + keep('</a>');
  });
  s = esc(s);
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<em>$2</em>');
  return s.replace(/\u0000(\d+)\u0000/g, (_, i) => stash[Number(i)]);
}

function render(md, opts) {
  const lines = String(md || '').replace(/\r\n?/g, '\n').split('\n');
  const out = [];
  let i = 0;
  const isBlockStart = (l) => /^(#{1,6}\s|>\s?|[-*+]\s|\d+\.\s|```|---+\s*$|\|)/.test(l);
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i++; continue; }
    if (/^```/.test(line)) {
      const buf = []; i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      i++; out.push(`<pre><code>${esc(buf.join('\n'))}</code></pre>`); continue;
    }
    const h = /^(#{1,6})\s+(.*)$/.exec(line);
    if (h) { const level = Math.min(Math.max(h[1].length, 2), 4); out.push(`<h${level}>${inline(h[2].replace(/\s+#+\s*$/, ''), opts)}</h${level}>`); i++; continue; }
    if (/^---+\s*$/.test(line)) { out.push('<hr>'); i++; continue; }
    if (/^>\s?/.test(line)) {
      const buf = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ''));
      out.push(`<blockquote>${render(buf.join('\n'), opts)}</blockquote>`); continue;
    }
    if (/^[-*+]\s/.test(line) || /^\d+\.\s/.test(line)) {
      const ordered = /^\d+\.\s/.test(line), re = ordered ? /^\d+\.\s+/ : /^[-*+]\s+/, items = [];
      while (i < lines.length && re.test(lines[i])) {
        let item = lines[i++].replace(re, '');
        while (i < lines.length && /^\s{2,}\S/.test(lines[i]) && !re.test(lines[i].trim())) item += ' ' + lines[i++].trim();
        items.push(`<li>${inline(item, opts)}</li>`);
      }
      out.push(`<${ordered ? 'ol' : 'ul'}>${items.join('')}</${ordered ? 'ol' : 'ul'}>`); continue;
    }
    if (/^\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\|?\s*:?-{2,}/.test(lines[i + 1])) {
      const cells = (l) => l.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
      const head = cells(line); i += 2;
      const rows = [];
      while (i < lines.length && /^\|.*\|\s*$/.test(lines[i])) rows.push(cells(lines[i++]));
      out.push(`<table><thead><tr>${head.map((c) => `<th>${inline(c, opts)}</th>`).join('')}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${inline(c, opts)}</td>`).join('')}</tr>`).join('')}</tbody></table>`);
      continue;
    }
    const para = [];
    while (i < lines.length && lines[i].trim() && !(para.length && isBlockStart(lines[i]))) para.push(lines[i++].trim());
    out.push(`<p>${inline(para.join(' '), opts)}</p>`);
  }
  return out.join('\n');
}

module.exports = { render, esc };
