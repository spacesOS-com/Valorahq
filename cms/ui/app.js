/* Valora CMS editor. Plain DOM, no dependencies. Every action goes through the same admin API
   (/api/cms/v1) that agents use; nothing here has a private back door. */
(function () {
  'use strict';
  var app = document.getElementById('app');
  var state = { user: null, ai: false, storage: 'local', groups: [], routes: [], today: '', sitePages: [], view: 'today', current: null, date: '' };

  /* ---------- helpers ---------- */
  function h(tag, attrs, children) {
    var el = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === 'class') el.className = v;
      else if (k === 'text') el.textContent = v;
      else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), v);
      else if (v === true) el.setAttribute(k, '');
      else el.setAttribute(k, v);
    });
    [].concat(children || []).forEach(function (c) { if (c) el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return el;
  }
  function api(method, path, body) {
    return fetch('/api/cms/v1/' + path, {
      method: method, credentials: 'same-origin',
      headers: body ? { 'Content-Type': 'application/json', 'X-CMS': '1' } : (method === 'GET' ? {} : { 'X-CMS': '1' }),
      body: body ? JSON.stringify(body) : undefined
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (res.status === 401 && path !== 'login') { state.user = null; render(); }
        if (!res.ok) { var e = new Error(data.error || 'Something went wrong.'); e.status = res.status; throw e; }
        return data;
      });
    });
  }
  var toastTimer;
  function toast(message, link) {
    var old = document.querySelector('.toast'); if (old) old.remove();
    var t = h('div', { class: 'toast', role: 'status' }, [message, link ? ' ' : null, link ? h('a', { href: link.href, target: '_blank', rel: 'noopener', text: link.text }) : null]);
    document.body.appendChild(t);
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.remove(); }, 7000);
  }
  function busy(button, label, promise) {
    var was = button.textContent; button.disabled = true; button.textContent = label;
    return promise.finally(function () { button.disabled = false; button.textContent = was; });
  }
  var clone = function (v) { return JSON.parse(JSON.stringify(v)); };

  /* paths: hero.headline, faqs[2].a, faqs[+] */
  function parsePath(p) {
    var parts = [], re = /([A-Za-z_@][\w@-]*)|\[(\d+|\+)\]/g, m;
    while ((m = re.exec(p))) parts.push(m[1] !== undefined ? m[1] : (m[2] === '+' ? '+' : Number(m[2])));
    return parts;
  }
  function getAt(doc, parts) { return parts.reduce(function (n, k) { return n == null ? n : n[k]; }, doc); }
  function setAt(doc, parts, value) {
    var parent = getAt(doc, parts.slice(0, -1)), last = parts[parts.length - 1];
    if (last === '+') parent.push(value); else parent[last] = value;
  }
  function pathString(parts) {
    return parts.map(function (p, i) { return typeof p === 'number' ? '[' + p + ']' : (i ? '.' : '') + p; }).join('');
  }

  /* ---------- field presentation ---------- */
  var LABELS = { h1: 'Page heading', title: 'Title', meta_title: 'Search title', meta_description: 'Search description', body_html: 'Page content',
    faqs: 'Questions and answers', q: 'Question', a: 'Answer', key_takeaways: 'Key takeaways', keywords: 'Search phrases', tags: 'Tags shown under the heading',
    internal_links: 'Related pages', inline_ctas: 'Calls to action inside the page', cta: 'Closing call to action', feature_image: 'Main image',
    src: 'Image address', alt: 'Image description', caption: 'Caption', status: 'Status', slug: 'Page address', page_type: 'Page type',
    source_notes: 'Notes for reviewers', effective_date: 'Effective date', button_label: 'Button text', href: 'Link', after_h2: 'Show after the section titled',
    what_we_do: 'What we do', what_we_are_not: 'What we are not', always_say: 'Always say', never_say: 'Never say', pain_points: 'Pain points',
    corrections: 'Corrections the AI must remember', body_md: 'Body (Markdown)', summary: 'Answer-first summary', author_persona: 'Author persona', slot_date: 'Calendar day',
    category: 'Kind of page', illustration_alt: 'Illustration description (alt text)', noindex: 'Hide from search engines', canonical: 'Canonical address (optional)', og_image: 'Social image address (optional)', headline_accent: 'Headline (highlighted part)', price_note: 'Line under the price', faq_heading: 'FAQ heading' };
  var ADVANCED = { source_notes: 1, template_notes: 1, footer_placement: 1, suggested_url: 1, faq_jsonld: 1, avatars: 1, avatars_note: 1, calculators: 1,
    extended_team: 1, toc: 1, canonical: 1, robots: 1, og_image: 1, noindex: 1, editorial_controls: 1, inline_images: 1, custom_excerpt: 1 };
  var READONLY = { slug: 1, page_type: 1 };
  function readonly(key) { return READONLY[key] && !(state.current.kind === 'article' && key === 'slug' && !state.current.live); }
  var LIMITS = { meta_title: 60, meta_description: 155 };
  var LONG = { summary: 1, meta_description: 1, a: 1, body: 1, description: 1, subheadline: 1, intro: 1, fine_print: 1, disclaimer: 1, what_we_do: 1, caption: 1, notes: 1 };
  function label(key) {
    if (LABELS[key]) return LABELS[key];
    var s = String(key).replace(/_/g, ' ');
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  function blankLike(sample) {
    if (typeof sample === 'string') return '';
    if (typeof sample === 'number') return 0;
    if (typeof sample === 'boolean') return false;
    if (Array.isArray(sample)) return [];
    if (sample && typeof sample === 'object') { var o = {}; Object.keys(sample).forEach(function (k) { o[k] = blankLike(sample[k]); }); return o; }
    return '';
  }

  function touch() {
    var cur = state.current; if (!cur) return;
    cur.dirty = JSON.stringify(cur.doc) !== JSON.stringify(cur.original);
    cur.checkToken = null;
    var d = document.querySelector('.bar .dirty'); if (d) d.textContent = cur.dirty ? 'Unsaved changes' : '';
    renderReadiness();
  }

  function richEditor(parts, value) {
    var area = h('div', { class: 'rich__area', contenteditable: 'true', role: 'textbox', 'aria-multiline': 'true' });
    area.innerHTML = value;
    var src = h('textarea', { class: 'rich__src', hidden: true, spellcheck: 'false' });
    var sync = function () { setAt(state.current.doc, parts, src.hidden ? area.innerHTML : src.value); touch(); };
    area.addEventListener('input', sync); src.addEventListener('input', sync);
    var cmd = function (name, arg) { return function () { area.focus(); document.execCommand(name, false, arg); sync(); }; };
    var tools = h('div', { class: 'rich__tools' }, [
      h('button', { type: 'button', text: 'Heading', onclick: cmd('formatBlock', 'h2') }),
      h('button', { type: 'button', text: 'Subheading', onclick: cmd('formatBlock', 'h3') }),
      h('button', { type: 'button', text: 'Paragraph', onclick: cmd('formatBlock', 'p') }),
      h('button', { type: 'button', text: 'Bold', onclick: cmd('bold') }),
      h('button', { type: 'button', text: 'Italic', onclick: cmd('italic') }),
      h('button', { type: 'button', text: 'Bullets', onclick: cmd('insertUnorderedList') }),
      h('button', { type: 'button', text: 'Numbers', onclick: cmd('insertOrderedList') }),
      h('button', { type: 'button', text: 'Link', onclick: function () {
        var sel = window.getSelection(), range = sel.rangeCount ? sel.getRangeAt(0) : null;
        ask('Link address', 'https://… or /page/').then(function (url) {
          if (!url || !/^(https?:\/\/|\/|#|mailto:)/i.test(url)) return;
          area.focus(); if (range) { sel.removeAllRanges(); sel.addRange(range); }
          document.execCommand('createLink', false, url); sync();
        });
      } }),
      h('button', { type: 'button', text: 'Remove link', onclick: cmd('unlink') }),
      h('button', { type: 'button', text: 'HTML', onclick: function () {
        if (src.hidden) { src.value = area.innerHTML; } else { area.innerHTML = src.value; }
        src.hidden = !src.hidden; area.hidden = !area.hidden;
      } })
    ]);
    return h('div', { class: 'rich' }, [tools, area, src]);
  }

  function field(parts, key, value) {
    var path = pathString(parts);
    var wrap = h('div', { class: 'f', 'data-path': path });
    var counter = LIMITS[key] ? h('span', { class: 'count' }) : null;
    wrap.appendChild(h('div', { class: 'lab' }, [h('span', { text: label(key) }), counter]));
    var input;
    if (/_html$/.test(key)) { wrap.appendChild(richEditor(parts, value)); return wrap; }
    if (state.current.kind === 'article' && key === 'category') {
      input = h('select', {}, state.routes.filter(function (r) { return r.type === state.current.type; }).map(function (r) { return h('option', { value: r.key, text: r.label }); }));
      input.value = value;
    } else if (key === 'body_md') {
      input = h('textarea', { rows: 26, class: 'mono', spellcheck: 'true' }); input.value = value;
    } else if (key === 'slot_date') {
      input = h('input', { type: 'date', value: value });
    } else if (key === 'status' && parts.length === 1) {
      input = h('select', {}, [h('option', { value: 'draft', text: 'Draft (hidden from search engines)' }), h('option', { value: 'approved', text: 'Approved (listed in search and AI indexes)' })]);
      input.value = value;
    } else if (typeof value === 'boolean') {
      input = h('select', {}, [h('option', { value: 'true', text: 'Yes' }), h('option', { value: 'false', text: 'No' })]);
      input.value = String(value);
    } else if (typeof value === 'number') {
      input = h('input', { type: 'text', inputmode: 'numeric', value: String(value) });
    } else if (LONG[key] || String(value).length > 90) {
      input = h('textarea', { rows: Math.min(8, Math.max(2, Math.ceil(String(value).length / 80))) }); input.value = value;
    } else {
      input = h('input', { type: 'text', value: value });
    }
    if (parts.length === 1 && readonly(key)) { input.disabled = true; }
    var update = function () {
      var v = input.value;
      if (typeof value === 'boolean') v = v === 'true';
      if (typeof value === 'number') v = Number(v) || 0;
      setAt(state.current.doc, parts, v); touch();
      if (counter) { counter.textContent = String(v).length + ' / ' + LIMITS[key]; counter.classList.toggle('is-over', String(v).length > LIMITS[key]); }
    };
    input.addEventListener('input', update);
    if (counter) { counter.textContent = String(value).length + ' / ' + LIMITS[key]; counter.classList.toggle('is-over', String(value).length > LIMITS[key]); }
    wrap.appendChild(input);
    return wrap;
  }

  function listField(parts, key, arr) {
    var box = h('div', { class: 'group', 'data-path': pathString(parts) }, [h('h3', { text: label(key) })]);
    var list = h('div', { class: 'list' });
    arr.forEach(function (item, i) {
      var itemParts = parts.concat(i), body;
      if (item && typeof item === 'object' && !Array.isArray(item)) body = objectFields(itemParts, item, true);
      else {
        body = h('input', { type: 'text', value: String(item) });
        body.addEventListener('input', function () { setAt(state.current.doc, itemParts, body.value); touch(); });
      }
      var move = function (delta) { return function () {
        var j = i + delta; if (j < 0 || j >= arr.length) return;
        var t = arr[i]; arr[i] = arr[j]; arr[j] = t; touch(); renderFields();
      }; };
      list.appendChild(h('div', { class: 'list__row' }, [body, h('div', { class: 'list__tools' }, [
        h('button', { type: 'button', class: 'icon', title: 'Move up', 'aria-label': 'Move up', text: '↑', onclick: move(-1) }),
        h('button', { type: 'button', class: 'icon', title: 'Move down', 'aria-label': 'Move down', text: '↓', onclick: move(1) }),
        h('button', { type: 'button', class: 'icon', title: 'Remove', 'aria-label': 'Remove', text: '×', onclick: function () { arr.splice(i, 1); touch(); renderFields(); } })
      ])]));
    });
    box.appendChild(list);
    var template = arr.length ? arr[0] : getAt(state.current.original, parts);
    template = Array.isArray(template) ? template[0] : template;
    box.appendChild(h('div', {}, [h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: 'Add', onclick: function () {
      arr.push(template === undefined ? '' : blankLike(template)); touch(); renderFields();
    } })]));
    return box;
  }

  function objectFields(parts, obj, bare) {
    var box = h('div', { class: bare ? 'fields' : 'group' });
    if (!bare) box.appendChild(h('h3', { text: label(parts[parts.length - 1]) }));
    Object.keys(obj).forEach(function (k) {
      var v = obj[k], p = parts.concat(k);
      if (Array.isArray(v)) box.appendChild(listField(p, k, v));
      else if (v && typeof v === 'object') box.appendChild(objectFields(p, v, false));
      else box.appendChild(field(p, k, v === null ? '' : v));
    });
    return box;
  }

  function renderFields() {
    var host = document.getElementById('fields'); if (!host) return;
    var doc = state.current.doc, main = h('div', { class: 'fields' }), basics = h('div', { class: 'group' }, [h('h3', { text: 'Basics' })]);
    var advanced = h('div', { class: 'fields' }), hasAdvanced = false, hasBasics = false;
    Object.keys(doc).forEach(function (k) {
      var v = doc[k], target = ADVANCED[k] ? advanced : main, node;
      if (typeof v === 'string' && v.length > 2000 && !/_html$/.test(k)) target = advanced;
      if (Array.isArray(v)) node = listField([k], k, v);
      else if (v && typeof v === 'object') node = objectFields([k], v, false);
      else { node = field([k], k, v === null ? '' : v); if (target === main && !/_html$/.test(k)) { basics.appendChild(node); hasBasics = true; return; } }
      if (target === advanced) hasAdvanced = true;
      target.appendChild(node);
    });
    host.textContent = '';
    if (hasBasics) host.appendChild(basics);
    host.appendChild(main);
    if (hasAdvanced) host.appendChild(h('details', { class: 'adv' }, [h('summary', { text: 'Advanced fields' }), advanced]));
  }

  /* ---------- AI-readiness checklist (plain rules, no AI call) ---------- */
  function readiness(doc) {
    var body = String(doc.body_html || ''), text = body.replace(/<[^>]+>/g, ' ');
    var h2 = body.match(/<h2[^>]*>([\s\S]*?)<\/h2>/gi) || [];
    var questions = h2.filter(function (x) { return /\?\s*<\/h2>/i.test(x); }).length;
    return [
      ['Starts with a direct answer in bold', /^\s*<p>\s*<strong>/i.test(body)],
      ['Search title is 60 characters or fewer', String(doc.meta_title || '').length > 0 && String(doc.meta_title).length <= 60],
      ['Search description is 155 characters or fewer', String(doc.meta_description || '').length > 0 && String(doc.meta_description).length <= 155],
      ['At least half of the section headings are questions', h2.length > 0 && questions * 2 >= h2.length],
      ['At least 4 questions and answers', (doc.faqs || []).length >= 4],
      ['At least 3 key takeaways', (doc.key_takeaways || []).length >= 3],
      ['At least 2 related pages linked', (doc.internal_links || []).length >= 2],
      ['At least 600 words', text.split(/\s+/).filter(Boolean).length >= 600],
      ['Approved, so it is listed in the sitemap and llms.txt', (doc.status || 'approved') === 'approved']
    ];
  }
  function renderReadiness() {
    var host = document.getElementById('readiness'); if (!host || !state.current || state.current.kind !== 'pack') return;
    var doc = state.current.doc; if (doc.page_type === 'legal' || doc.page_type === 'team') { host.hidden = true; return; }
    var rows = readiness(doc), ok = rows.filter(function (r) { return r[1]; }).length;
    host.textContent = '';
    host.appendChild(h('h3', { text: 'AI readiness: ' + ok + ' of ' + rows.length }));
    rows.forEach(function (r) { host.appendChild(h('div', { class: r[1] ? 'muted' : '', text: (r[1] ? '✓ ' : '○ ') + r[0] })); });
  }

  /* ---------- AI panel ---------- */
  function applyChange(c) {
    var cur = state.current, parts = parsePath(c.path);
    if (c.kind === 'replace_text') {
      var before = getAt(cur.doc, parts);
      if (typeof before !== 'string' || before.indexOf(c.before) === -1) return false;
      setAt(cur.doc, parts, before.replace(c.before, c.after));
    } else setAt(cur.doc, parts, clone(c.after));
    return true;
  }
  function show(v) { return typeof v === 'string' ? v : JSON.stringify(v, null, 1); }
  function changeCard(c) {
    var card = h('div', { class: 'change' });
    var accept = h('button', { type: 'button', class: 'btn btn--small', text: 'Accept' });
    var reject = h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: 'Skip' });
    var done = function (note) { card.classList.add('is-done'); accept.remove(); reject.remove(); card.appendChild(h('div', { class: 'muted', text: note })); };
    accept.addEventListener('click', function () {
      if (applyChange(c)) { touch(); renderFields(); done('Applied. Save to keep it.'); } else done('Could not apply: the text has changed since.');
    });
    reject.addEventListener('click', function () { done('Skipped.'); });
    card.appendChild(h('div', { class: 'change__path', text: (c.kind === 'append' ? 'Add to ' : 'Change ') + c.path.replace('[+]', '') }));
    if (c.before !== null && c.before !== '') card.appendChild(h('div', { class: 'change__before', text: show(c.before) }));
    card.appendChild(h('div', { class: 'change__after', text: show(c.after) }));
    card.appendChild(h('div', { class: 'change__row' }, [accept, reject]));
    return card;
  }
  var AI_KEYS = ['title', 'summary', 'body_md', 'meta_title', 'meta_description', 'faqs', 'key_takeaways'];
  function aiDoc() {
    var cur = state.current; if (cur.kind !== 'article') return cur.doc;
    var d = {}; AI_KEYS.forEach(function (k) { d[k] = cur.doc[k]; }); return d;
  }
  function findingCard(f) {
    return h('div', { class: 'finding finding--' + f.severity }, [
      h('small', { text: (f.severity === 'high' ? 'Serious' : f.severity === 'medium' ? 'Worth fixing' : 'Minor') + (f.field ? ' · ' + label(f.field.split(/[.\[]/)[0]) : '') }),
      f.quote ? h('q', { text: f.quote }) : null, h('span', { text: f.issue }), f.suggestion ? h('span', { class: 'muted', text: 'Suggestion: ' + f.suggestion }) : null]);
  }
  function aiPanel() {
    var out = h('div', { class: 'stack' });
    var box = h('textarea', { rows: 3, placeholder: 'e.g. Make the heading shorter, or add a question about fees', 'aria-label': 'Tell the AI what to change' });
    var run = function (instruction, button) {
      out.textContent = '';
      return busy(button, 'Thinking…', api('POST', 'ai/edit', { doc: aiDoc(), instruction: instruction }).then(function (r) {
        out.appendChild(h('p', { text: r.summary }));
        if (!r.changes.length) out.appendChild(h('p', { class: 'muted', text: 'No changes proposed.' }));
        r.changes.forEach(function (c) { out.appendChild(changeCard(c)); });
        if (r.skipped && r.skipped.length) out.appendChild(h('p', { class: 'muted', text: r.skipped.length + ' suggestion(s) were dropped because they were not safe to apply.' }));
      }).catch(function (e) { out.appendChild(h('p', { class: 'err', text: e.message })); }));
    };
    var ask = h('button', { type: 'button', class: 'btn', text: 'Ask AI' });
    ask.addEventListener('click', function () { if (box.value.trim()) run(box.value.trim(), ask); });
    var quick = function (text, preset) { var b = h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: text }); b.addEventListener('click', function () { run(preset, b); }); return b; };
    var panel = h('aside', { class: 'ai' }, [h('h3', { text: 'AI editor' })]);
    if (!state.ai) { panel.appendChild(h('p', { class: 'ai__hint', text: 'AI is not set up on this site yet. An admin needs to add the API key.' })); return panel; }
    panel.appendChild(h('p', { class: 'ai__hint', text: 'Describe a change. You approve every edit before it is applied, and nothing is published until you publish.' }));
    panel.appendChild(box); panel.appendChild(h('div', {}, [ask]));
    panel.appendChild(h('div', { class: 'change__row wrap' }, [quick('Refresh content', 'refresh'), quick('Suggest internal links', 'links'), quick('Make AI-ready', 'ai_ready')]));
    if (state.current.kind === 'article') {
      var review = h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: 'Compliance check' });
      review.addEventListener('click', function () {
        out.textContent = '';
        busy(review, 'Reviewing…', api('POST', 'ai/check', { article: aiDoc() }).then(function (r) {
          out.appendChild(h('p', { text: r.summary }));
          r.findings.forEach(function (f) { out.appendChild(findingCard(f)); });
        }).catch(function (e) { out.appendChild(h('p', { class: 'err', text: e.message })); }));
      });
      panel.appendChild(h('div', {}, [review]));
    }
    panel.appendChild(out);
    return panel;
  }

  /* ---------- dialogs (no browser prompt/confirm boxes) ---------- */
  function modal(title, message, opts) {
    opts = opts || {};
    return new Promise(function (resolve) {
      var dlg = h('dialog'), input = opts.input ? h('input', { type: 'text', value: opts.value || '', placeholder: opts.placeholder || '' }) : null;
      var close = function (v) { dlg.close(); dlg.remove(); resolve(v); };
      var ok = h('button', { type: 'submit', class: 'btn' + (opts.danger ? ' btn--danger' : ''), text: opts.ok || 'OK' });
      var form = h('form', { class: 'dlg' }, [h('h2', { text: title }), message ? h('p', { text: message }) : null, input,
        h('div', { class: 'dlg__foot' }, [h('button', { type: 'button', class: 'btn btn--ghost', text: 'Cancel', onclick: function () { close(input ? null : false); } }), ok])]);
      form.addEventListener('submit', function (e) { e.preventDefault(); close(input ? (input.value.trim() || (opts.allowEmpty ? '' : null)) : true); });
      dlg.addEventListener('cancel', function (e) { e.preventDefault(); close(input ? null : false); });
      dlg.appendChild(form); document.body.appendChild(dlg); dlg.showModal(); if (input) input.focus();
    });
  }
  function ask(title, placeholder, value) { return modal(title, '', { input: true, placeholder: placeholder, value: value, ok: 'Continue' }); }
  function sure(title, message, ok) { return modal(title, message, { ok: ok || 'Yes', danger: true }); }

  /* ---------- shared ---------- */
  function fmt(iso) { return iso ? new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : ''; }
  var STATUS = { draft: 'Draft', 'in-review': 'In review', approved: 'Approved', scheduled: 'Scheduled', published: 'Published' };
  function statusPill(s) { return h('span', { class: 'pill pill--' + s, text: STATUS[s] || s }); }
  function can(role) { return [].slice.call(arguments).indexOf(state.user.role) !== -1; }
  function leave() { return state.current && state.current.dirty ? sure('Leave without saving?', 'You have unsaved changes on this page.', 'Leave') : Promise.resolve(true); }
  function go(view) { leave().then(function (ok) { if (!ok) return; state.view = view; state.current = null; render(); window.scrollTo(0, 0); }); }
  function table(headings, rows) {
    return h('div', { class: 'tablewrap' }, [h('table', { class: 'tbl' }, [h('thead', {}, [h('tr', {}, headings.map(function (t) { return h('th', { text: t }); }))]), h('tbody', {}, rows)])]);
  }
  function td(content) { return h('td', {}, [].concat(content)); }

  /* ---------- article editor ---------- */
  var ARTICLE_KEYS = ['title', 'slug', 'category', 'author_persona', 'slot_date', 'summary', 'body_md', 'meta_title', 'meta_description', 'faqs', 'key_takeaways', 'illustration_alt', 'noindex', 'canonical', 'og_image'];
  function articleDoc(a) { var d = {}; ARTICLE_KEYS.forEach(function (k) { d[k] = a[k]; }); return clone(d); }
  function setArticle(r) {
    var a = r.article;
    state.current = { kind: 'article', id: a.id, type: a.type, meta: a, live: a.live, doc: articleDoc(a), original: articleDoc(a), dirty: false,
      problems: r.problems || (state.current && state.current.problems) || [], previewUrl: r.preview_url || (state.current && state.current.previewUrl) };
  }
  function openArticle(id) {
    leave().then(function (ok) { if (!ok) return;
      api('GET', 'articles/' + id).then(function (r) { setArticle(r); state.view = 'article'; render(); window.scrollTo(0, 0); }).catch(function (e) { toast(e.message); });
    });
  }
  function reloadArticle() { return api('GET', 'articles/' + state.current.id).then(function (r) { setArticle(r); render(); }); }
  function saveArticle() {
    var cur = state.current, patch = {};
    ARTICLE_KEYS.forEach(function (k) { if (JSON.stringify(cur.doc[k]) !== JSON.stringify(cur.original[k])) patch[k] = cur.doc[k]; });
    if (!Object.keys(patch).length) return Promise.resolve();
    return api('PATCH', 'articles/' + cur.id, patch).then(reloadArticle);
  }
  function act(button, label, path, body, done) {
    return busy(button, label, saveArticle().then(function () { return api('POST', 'articles/' + state.current.id + '/' + path, body || {}); })
      .then(function (r) { toast(done(r)); return reloadArticle(); }).catch(function (e) { toast(e.message); return reloadArticle().catch(function () {}); }));
  }
  function illustrationCard() {
    var cur = state.current, a = cur.meta;
    var box = h('div', { class: 'group' }, [h('h3', { text: 'Illustration' }), h('p', { class: 'muted small', text: 'Required before publishing. PNG, JPEG or WebP, up to 3 MB.' })]);
    if (a.has_illustration) box.appendChild(h('img', { class: 'thumb', alt: a.illustration_alt, src: '/api/cms/v1/articles/' + a.id + '/illustration?v=' + encodeURIComponent(a.updated_at) }));
    var file = h('input', { type: 'file', accept: 'image/png,image/jpeg,image/webp', 'aria-label': 'Choose an illustration' });
    var up = h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: a.has_illustration ? 'Replace illustration' : 'Upload illustration' });
    up.addEventListener('click', function () {
      var f = file.files[0]; if (!f) { toast('Choose an image first.'); return; }
      var reader = new FileReader();
      reader.onload = function () {
        var b64 = String(reader.result).split(',')[1];
        busy(up, 'Uploading…', saveArticle().then(function () {
          return api('PUT', 'articles/' + state.current.id + '/illustration', { filename: f.name, content_type: f.type, data_base64: b64, alt: state.current.doc.illustration_alt });
        }).then(function () { toast('Illustration saved.'); return reloadArticle(); }).catch(function (e) { toast(e.message); }));
      };
      reader.readAsDataURL(f);
    });
    box.appendChild(file); box.appendChild(h('div', {}, [up]));
    return box;
  }
  function articleView() {
    var cur = state.current, a = cur.meta, s = a.status;
    var bar = h('div', { class: 'bar' }, [h('h1', { text: a.title }), statusPill(s), h('span', { class: 'dirty' })]);
    var save = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Save' });
    save.addEventListener('click', function () { busy(save, 'Saving…', saveArticle().then(function () { toast('Saved.'); }).catch(function (e) { toast(e.message); })); });
    bar.appendChild(h('a', { class: 'btn btn--ghost btn--small', href: cur.previewUrl, target: '_blank', rel: 'noopener', text: 'Preview' }));
    if (a.live && a.published_url) bar.appendChild(h('a', { class: 'btn btn--ghost btn--small', href: a.published_url, target: '_blank', rel: 'noopener', text: 'Live page' }));
    bar.appendChild(save);
    if (s === 'draft') {
      var submit = h('button', { type: 'button', class: 'btn', text: 'Send to QA' });
      submit.addEventListener('click', function () { act(submit, 'Sending…', 'submit', {}, function () { return 'Sent to QA.'; }); });
      bar.appendChild(submit);
    }
    if (s === 'in-review' && can('qa')) {
      var back = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Send back' });
      back.addEventListener('click', function () { ask('What needs to change?', 'A note for the writer').then(function (note) { if (note) act(back, 'Sending…', 'request-changes', { note: note }, function () { return 'Sent back to the writer.'; }); }); });
      var approve = h('button', { type: 'button', class: 'btn', text: 'Approve and publish' });
      approve.addEventListener('click', function () { act(approve, 'Publishing…', 'approve', {}, function () { return 'Approved and published.'; }); });
      var when = h('input', { type: 'datetime-local', 'aria-label': 'Schedule for' });
      var sched = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Approve and schedule' });
      sched.addEventListener('click', function () {
        if (!when.value) { toast('Pick a date and time first.'); return; }
        act(sched, 'Scheduling…', 'approve', { publish_at: new Date(when.value).toISOString() }, function (r) { return r.scheduled ? 'Approved. It will publish at the scheduled time.' : 'That time has passed, so it was published now.'; });
      });
      bar.appendChild(back); bar.appendChild(when); bar.appendChild(sched); bar.appendChild(approve);
    }
    if (s === 'approved' && can('qa', 'admin')) {
      var retry = h('button', { type: 'button', class: 'btn', text: 'Publish now' });
      retry.addEventListener('click', function () { act(retry, 'Publishing…', 'publish', {}, function () { return 'Published.'; }); });
      bar.appendChild(retry);
    }
    if (a.live && can('admin')) {
      var un = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Unpublish' });
      un.addEventListener('click', function () { sure('Unpublish this page?', 'It will be removed from the live site and returned to draft.', 'Unpublish').then(function (ok) { if (ok) act(un, 'Removing…', 'unpublish', {}, function () { return 'Unpublished.'; }); }); });
      bar.appendChild(un);
    }
    var notes = h('div', { class: 'stack' });
    var line = (a.type === 'advisor-article' ? 'Advisor article for insights.spacesos.com' : 'Consumer page for valorahq.com') + ' · by ' + a.author_persona;
    notes.appendChild(h('p', { class: 'muted', text: line + (a.scheduled_at ? ' · scheduled for ' + fmt(a.scheduled_at) : '') + (a.published_at ? ' · first published ' + fmt(a.published_at) : '') }));
    if (a.live && s !== 'published') notes.appendChild(h('p', { class: 'note', text: 'The published version stays live. These edits go live after QA approves them.' }));
    if (a.review_note) notes.appendChild(h('p', { class: 'note', text: 'Note: ' + a.review_note }));
    if (a.publish_error) notes.appendChild(h('p', { class: 'err', text: 'Publishing failed: ' + a.publish_error }));
    if (s === 'in-review' && !can('qa', 'admin')) notes.appendChild(h('p', { class: 'note', text: 'This is with QA and cannot be edited until QA approves it or sends it back.' }));
    if (cur.problems.length && s !== 'published') notes.appendChild(h('div', { class: 'card stack tight' }, [h('h3', { text: 'Before this can publish' })].concat(cur.problems.map(function (p) { return h('div', { text: '○ ' + p }); }))));
    var del = null;
    if (!a.live) { del = h('button', { type: 'button', class: 'link danger', text: 'Delete this article' });
      del.addEventListener('click', function () { sure('Delete this article?', 'This cannot be undone.', 'Delete').then(function (ok) { if (ok) api('DELETE', 'articles/' + a.id).then(function () { state.current = null; state.view = 'articles'; render(); }).catch(function (e) { toast(e.message); }); }); }); }
    var left = h('div', { class: 'stack' }, [notes, h('div', { id: 'fields' }), illustrationCard(), del]);
    setTimeout(renderFields, 0);
    return h('main', { class: 'main' }, [bar, h('div', { class: 'editor' }, [left, aiPanel()])]);
  }

  /* ---------- today ---------- */
  function newArticle(type, date) {
    ask(type === 'advisor-article' ? 'New advisor article' : 'New consumer page', 'Working title').then(function (title) {
      if (!title) return;
      api('POST', 'articles', { type: type, title: title, slot_date: date }).then(function (r) { openArticle(r.article.id); }).catch(function (e) { toast(e.message); });
    });
  }
  function todayView() {
    var main = h('main', { class: 'main' }), date = state.date || state.today;
    var picker = h('input', { type: 'date', value: date, 'aria-label': 'Day' });
    picker.addEventListener('change', function () { state.date = picker.value; render(); });
    var count = h('div', { class: 'count', text: '…' });
    main.appendChild(h('div', { class: 'bar' }, [h('h1', { text: date === state.today ? 'Today' : date }), picker]));
    main.appendChild(h('div', { class: 'card countcard' }, [count, h('p', { class: 'muted', text: 'Done means QA-approved and published.' })]));
    var board = h('div', { class: 'board' }); main.appendChild(board);
    api('GET', 'calendar?date=' + encodeURIComponent(date)).then(function (c) {
      count.textContent = c.done + ' of ' + c.target + ' done';
      ['advisor-article', 'consumer-page'].forEach(function (type) {
        var col = h('div', { class: 'stack' }, [h('h2', { class: 'colhead', text: type === 'advisor-article' ? 'Advisor articles · Hannah' : 'Consumer pages · Nina' })]);
        c.slots.filter(function (x) { return x.type === type; }).forEach(function (slot) {
          if (slot.article) {
            var a = slot.article;
            col.appendChild(h('button', { type: 'button', class: 'pagecard', onclick: function () { openArticle(a.id); } }, [
              h('strong', { text: a.title }), h('span', {}, [statusPill(a.status), a.has_illustration ? null : h('span', { class: 'pill pill--warn', text: 'No illustration' })]),
              h('small', { text: a.status === 'scheduled' ? 'Publishes ' + fmt(a.scheduled_at) : a.status === 'published' ? 'Published ' + fmt(a.published_at) : 'Updated ' + fmt(a.updated_at) })]));
          } else {
            col.appendChild(h('button', { type: 'button', class: 'pagecard pagecard--empty', onclick: function () { newArticle(type, date); } }, [h('strong', { text: 'Slot ' + slot.slot + ' is open' }), h('small', { text: 'Start an article' })]));
          }
        });
        board.appendChild(col);
      });
    }).catch(function (e) { board.appendChild(h('p', { class: 'err', text: e.message })); });
    return main;
  }

  /* ---------- article list ---------- */
  function articlesView() {
    var main = h('main', { class: 'main' }, [h('div', { class: 'bar' }, [h('h1', { text: 'Articles' })])]);
    var status = h('select', { 'aria-label': 'Status' }, [h('option', { value: '', text: 'Any status' })].concat(Object.keys(STATUS).map(function (k) { return h('option', { value: k, text: STATUS[k] }); })));
    var type = h('select', { 'aria-label': 'Type' }, [h('option', { value: '', text: 'Both types' }), h('option', { value: 'advisor-article', text: 'Advisor articles' }), h('option', { value: 'consumer-page', text: 'Consumer pages' })]);
    var search = h('input', { type: 'text', placeholder: 'Search title', 'aria-label': 'Search' });
    var out = h('div');
    var load = function () {
      api('GET', 'articles?status=' + status.value + '&type=' + type.value + '&q=' + encodeURIComponent(search.value)).then(function (r) {
        out.textContent = '';
        if (!r.articles.length) { out.appendChild(h('p', { class: 'muted', text: 'Nothing matches.' })); return; }
        out.appendChild(table(['Title', 'Type', 'Status', 'Day', 'Updated'], r.articles.map(function (a) {
          return h('tr', {}, [td(h('button', { type: 'button', class: 'link', text: a.title, onclick: function () { openArticle(a.id); } })),
            td(a.type === 'advisor-article' ? 'Advisor article' : 'Consumer page'), td(statusPill(a.status)), td(a.slot_date), td(fmt(a.updated_at))]);
        })));
      }).catch(function (e) { toast(e.message); });
    };
    [status, type].forEach(function (x) { x.addEventListener('change', load); }); search.addEventListener('input', load);
    main.appendChild(h('div', { class: 'filters' }, [status, type, search])); main.appendChild(out); load();
    return main;
  }

  /* ---------- create with AI ---------- */
  function engineView() {
    var main = h('main', { class: 'main' }, [h('h1', { text: 'Create with AI' }),
      h('p', { class: 'lead', text: 'Give a topic and the AI writes a full draft, built to be read and cited by AI assistants. Each one is saved as a draft for a writer to check and QA to approve; nothing is published from here.' })]);
    if (!state.ai) { main.appendChild(h('p', { class: 'err', text: 'AI is not set up yet. An admin needs to add the API key.' })); return main; }
    var type = h('select', {}, [h('option', { value: 'consumer-page', text: 'Consumer pages (valorahq.com)' }), h('option', { value: 'advisor-article', text: 'Advisor articles (insights.spacesos.com)' })]);
    var category = h('select', {});
    var fill = function () { category.textContent = ''; state.routes.filter(function (r) { return r.type === type.value; }).forEach(function (r) { category.appendChild(h('option', { value: r.key, text: r.label })); }); };
    type.addEventListener('change', fill); fill();
    var topics = h('textarea', { rows: 4, placeholder: 'One topic per line, e.g.\nFinancial advisor for airline pilots\nFinancial planning after selling a dental practice' });
    var notes = h('textarea', { rows: 2, placeholder: 'Optional: angle, points to cover, things to avoid' });
    var status = h('div', { class: 'stack' });
    var make = h('button', { type: 'button', class: 'btn', text: 'Write drafts' });
    make.addEventListener('click', function () {
      var list = topics.value.split('\n').map(function (t) { return t.trim(); }).filter(Boolean).slice(0, 10);
      if (!list.length) return;
      status.textContent = '';
      var chain = Promise.resolve();
      list.forEach(function (topic, i) {
        chain = chain.then(function () {
          var row = h('div', { class: 'idea' }, [h('span', { text: 'Writing ' + (i + 1) + ' of ' + list.length + ': ' + topic + '…' })]);
          status.appendChild(row);
          return api('POST', 'ai/draft', { topic: topic, type: type.value, category: category.value, notes: notes.value }).then(function (r) {
            row.textContent = ''; row.appendChild(h('span', { text: r.article.title }));
            row.appendChild(h('button', { type: 'button', class: 'btn btn--small', text: 'Open draft', onclick: function () { openArticle(r.article.id); } }));
          }).catch(function (e) { row.textContent = ''; row.appendChild(h('span', { class: 'err', text: topic + ': ' + e.message })); });
        });
      });
      busy(make, 'Writing…', chain);
    });
    var seed = h('input', { type: 'text', placeholder: 'An audience or theme, e.g. physicians, or solo RIA marketing' });
    var ideaList = h('div');
    var suggest = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Suggest topics' });
    suggest.addEventListener('click', function () {
      if (!seed.value.trim()) return;
      ideaList.textContent = '';
      busy(suggest, 'Thinking…', api('POST', 'ai/ideas', { seed: seed.value, type: type.value }).then(function (r) {
        r.ideas.forEach(function (idea) {
          ideaList.appendChild(h('div', { class: 'idea' }, [h('span', {}, [h('strong', { text: idea.topic }), ' ', h('span', { class: 'pill', text: idea.intent }), h('br'), h('span', { class: 'muted', text: idea.why })]),
            h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: 'Add', onclick: function () { topics.value = (topics.value.trim() ? topics.value.trim() + '\n' : '') + idea.topic; } })]));
        });
      }).catch(function (e) { ideaList.appendChild(h('p', { class: 'err', text: e.message })); }));
    });
    main.appendChild(h('div', { class: 'stack narrow' }, [
      h('div', { class: 'card stack' }, [h('h3', { text: 'What to write' }), h('label', { class: 'field' }, ['Type', type]), h('label', { class: 'field' }, ['Kind of page', category]),
        h('label', { class: 'field' }, ['Topics (up to 10)', topics]), h('label', { class: 'field' }, ['Notes for the AI', notes]), h('div', {}, [make]), status]),
      h('div', { class: 'card stack' }, [h('h3', { text: 'Need ideas?' }), h('p', { class: 'muted', text: 'Suggestions come from the AI’s general knowledge and are labelled by intent. They are not search-volume data.' }), seed, h('div', {}, [suggest]), ideaList])]));
    return main;
  }

  /* ---------- site pages (existing hand-built pages) ---------- */
  function loadSitePages() { return api('GET', 'site-pages').then(function (r) { state.sitePages = r.pages; }); }
  function sitePagesView() {
    var main = h('main', { class: 'main' }, [h('h1', { text: 'Site pages' }), h('p', { class: 'lead', text: 'The existing pages of valorahq.com: the advisor landing page, the original guides, the team page and the legal pages. Saving a change publishes it, so only QA and admins can save here.' })]);
    loadSitePages().then(function () {
      state.groups.forEach(function (g) {
        var pages = state.sitePages.filter(function (p) { return p.group === g.key; }); if (!pages.length) return;
        main.appendChild(h('h2', { class: 'colhead', text: g.label }));
        main.appendChild(h('div', { class: 'grid2' }, pages.map(function (p) {
          return h('button', { type: 'button', class: 'pagecard', onclick: function () { openSitePage(p.kind, p.id); } }, [h('strong', { text: p.title }), h('small', { text: 'valorahq.com' + p.url }),
            h('span', {}, [h('span', { class: 'pill' + (p.status === 'draft' ? ' pill--draft' : ' pill--published'), text: p.status === 'draft' ? 'Hidden from search' : 'Live' })])]);
        })));
      });
    }).catch(function (e) { main.appendChild(h('p', { class: 'err', text: e.message })); });
    return main;
  }
  function openSitePage(kind, id) {
    leave().then(function (ok) { if (!ok) return;
      api('GET', 'site-pages/' + kind + '/' + id).then(function (r) {
        state.current = { kind: kind, id: id, doc: clone(r.doc), original: clone(r.doc), sha: r.sha, url: r.url, dirty: false };
        state.view = 'sitepage'; render(); window.scrollTo(0, 0);
      }).catch(function (e) { toast(e.message); });
    });
  }
  function publishSitePage(button) {
    var cur = state.current;
    var save = function (token, acknowledge) {
      return api('PUT', 'site-pages/' + cur.kind + '/' + cur.id, { doc: cur.doc, sha: cur.sha, checkToken: token, acknowledge: acknowledge }).then(function (r) {
        cur.doc = r.doc; cur.original = clone(r.doc); cur.sha = r.sha; cur.dirty = false;
        toast(state.storage === 'local' ? 'Saved locally and the site was rebuilt.' : 'Published. The live site updates after the deploy.', r.commit_url ? { href: r.commit_url, text: 'View change' } : null);
        render();
      });
    };
    if (!state.ai) return busy(button, 'Publishing…', save(null, false).catch(function (e) { toast(e.message); }));
    return busy(button, 'Reviewing…', api('POST', 'ai/check', { kind: cur.kind, id: cur.id, doc: cur.doc }).then(function (r) {
      cur.doc = r.doc; renderFields();
      var dlg = h('dialog'), high = r.worst === 'high';
      var body = h('div', { class: 'dlg' }, [h('h2', { text: r.findings.length ? 'Compliance review: ' + r.findings.length + ' note' + (r.findings.length > 1 ? 's' : '') : 'Compliance review: nothing found' }), h('p', { text: r.summary })]);
      r.findings.forEach(function (f) { body.appendChild(findingCard(f)); });
      var ack = h('input', { type: 'checkbox' });
      var goBtn = h('button', { type: 'button', class: 'btn' + (high ? ' btn--danger' : ''), text: high ? 'Publish anyway' : 'Publish' });
      var err = h('p', { class: 'err' });
      if (high) { goBtn.disabled = true; ack.addEventListener('change', function () { goBtn.disabled = !ack.checked; });
        body.appendChild(h('label', {}, [ack, ' I have read the serious findings and want to publish anyway.'])); }
      goBtn.addEventListener('click', function () { busy(goBtn, 'Publishing…', save(r.checkToken, ack.checked).then(function () { dlg.close(); dlg.remove(); }).catch(function (e) { err.textContent = e.message; })); });
      body.appendChild(err);
      body.appendChild(h('div', { class: 'dlg__foot' }, [h('button', { type: 'button', class: 'btn btn--ghost', text: 'Back to editing', onclick: function () { dlg.close(); dlg.remove(); } }), goBtn]));
      dlg.appendChild(body); document.body.appendChild(dlg); dlg.showModal();
    }).catch(function (e) { toast(e.message); }));
  }
  function sitePageView() {
    var cur = state.current, allowed = can('qa', 'admin');
    var button = h('button', { type: 'button', class: 'btn', text: 'Review and publish', disabled: !allowed });
    button.addEventListener('click', function () { publishSitePage(button); });
    var bar = h('div', { class: 'bar' }, [h('h1', { text: cur.doc.h1 || cur.doc.title || cur.id }), h('span', { class: 'dirty' }),
      h('a', { class: 'btn btn--ghost btn--small', href: cur.url, target: '_blank', rel: 'noopener', text: 'View live page' }), button]);
    var left = h('div', { class: 'stack' }, [allowed ? null : h('p', { class: 'note', text: 'You can read this page and try edits with the AI, but only QA or an admin can publish changes to it.' }),
      cur.kind === 'pack' ? h('div', { class: 'card stack tight', id: 'readiness' }) : null, h('div', { id: 'fields' })]);
    setTimeout(function () { renderFields(); renderReadiness(); }, 0);
    return h('main', { class: 'main' }, [bar, h('div', { class: 'editor' }, [left, aiPanel()])]);
  }

  /* ---------- admin ---------- */
  function memoryView() {
    var main = h('main', { class: 'main' });
    var save = h('button', { type: 'button', class: 'btn', text: 'Save', disabled: !can('admin') });
    save.addEventListener('click', function () { busy(save, 'Saving…', api('PUT', 'brand-memory', { memory: state.current.doc }).then(function (r) { state.current.original = clone(r.memory); state.current.dirty = false; toast('Saved. The AI uses it from now on.'); render(); }).catch(function (e) { toast(e.message); })); });
    main.appendChild(h('div', { class: 'bar' }, [h('h1', { text: 'Brand memory' }), h('span', { class: 'dirty' }), save]));
    main.appendChild(h('p', { class: 'lead', text: 'The AI reads this before every draft, edit and review. Keep it true: what Valora sells, to whom, at what price, and how it speaks. When the AI gets something wrong, add a correction and it will not repeat it. This is stored privately, not in the public site repository.' }));
    main.appendChild(h('div', { id: 'fields', class: 'narrow' }));
    setTimeout(renderFields, 0);
    return main;
  }
  function openMemory() {
    leave().then(function (ok) { if (!ok) return;
      api('GET', 'brand-memory').then(function (r) { state.current = { kind: 'memory', doc: clone(r.memory), original: clone(r.memory), dirty: false }; state.view = 'memory'; render(); }).catch(function (e) { toast(e.message); });
    });
  }
  function usersView() {
    var main = h('main', { class: 'main' }, [h('h1', { text: 'People and agent tokens' }), h('p', { class: 'lead', text: 'Writers create and edit drafts. QA is the only role that can approve, and approving publishes. Admins manage people, redirects and routes. An agent token acts as the person it belongs to.' })]);
    var out = h('div', { class: 'stack' }); main.appendChild(out);
    var load = function () {
      Promise.all([api('GET', 'users'), api('GET', 'tokens')]).then(function (res) {
        out.textContent = '';
        out.appendChild(table(['Name', 'Email', 'Role', 'Persona', '', ''], res[0].users.map(function (u) {
          var role = h('select', { 'aria-label': 'Role for ' + u.name }, ['writer', 'qa', 'admin'].map(function (x) { return h('option', { value: x, text: x }); })); role.value = u.role;
          role.addEventListener('change', function () { api('PATCH', 'users/' + u.id, { role: role.value }).then(load).catch(function (e) { toast(e.message); load(); }); });
          return h('tr', { class: u.active ? '' : 'is-off' }, [td(u.name), td(u.email), td(role), td(u.persona || '—'),
            td(h('button', { type: 'button', class: 'link', text: 'New token', onclick: function () {
              ask('New agent token for ' + u.name, 'What is it for? e.g. drafting agent').then(function (name) { if (!name) return;
                api('POST', 'users/' + u.id + '/tokens', { name: name }).then(function (t) { showSecret('Token for ' + u.name, t.token); load(); }).catch(function (e) { toast(e.message); }); });
            } })),
            td(h('button', { type: 'button', class: 'link', text: u.active ? 'Deactivate' : 'Reactivate', onclick: function () { api('PATCH', 'users/' + u.id, { active: !u.active }).then(load).catch(function (e) { toast(e.message); }); } }))]);
        })));
        var f = { name: h('input', { type: 'text' }), email: h('input', { type: 'email' }), persona: h('input', { type: 'text', placeholder: 'e.g. Hannah' }), password: h('input', { type: 'password', autocomplete: 'new-password' }),
          role: h('select', {}, ['writer', 'qa', 'admin'].map(function (x) { return h('option', { value: x, text: x }); })) };
        var add = h('button', { type: 'button', class: 'btn', text: 'Add person' });
        add.addEventListener('click', function () { busy(add, 'Adding…', api('POST', 'users', { name: f.name.value, email: f.email.value, persona: f.persona.value, password: f.password.value, role: f.role.value }).then(load).catch(function (e) { toast(e.message); })); });
        out.appendChild(h('div', { class: 'card stack narrow' }, [h('h3', { text: 'Add a person' }), h('label', { class: 'field' }, ['Name', f.name]), h('label', { class: 'field' }, ['Email', f.email]), h('label', { class: 'field' }, ['Role', f.role]),
          h('label', { class: 'field' }, ['Persona (writers)', f.persona]), h('label', { class: 'field' }, ['Temporary password (12+ characters)', f.password]), h('div', {}, [add])]));
        out.appendChild(h('h2', { class: 'colhead', text: 'Active agent tokens' }));
        out.appendChild(res[1].tokens.length ? table(['Name', 'Acts as', 'Role', 'Last used', ''], res[1].tokens.map(function (t) {
          return h('tr', {}, [td(t.name), td(t.user), td(t.role), td(t.last_used_at ? fmt(t.last_used_at) : 'Never'),
            td(h('button', { type: 'button', class: 'link danger', text: 'Revoke', onclick: function () { sure('Revoke this token?', 'The agent using it stops working immediately.', 'Revoke').then(function (ok) { if (ok) api('DELETE', 'tokens/' + t.id).then(load).catch(function (e) { toast(e.message); }); }); } }))]);
        })) : h('p', { class: 'muted', text: 'No tokens yet.' }));
      }).catch(function (e) { out.appendChild(h('p', { class: 'err', text: e.message })); });
    };
    load();
    return main;
  }
  function showSecret(title, secret) {
    var dlg = h('dialog');
    var box = h('input', { type: 'text', readonly: true, value: secret, class: 'mono' });
    dlg.appendChild(h('div', { class: 'dlg' }, [h('h2', { text: title }), h('p', { text: 'Copy this now. It is shown once and cannot be recovered; only a fingerprint is stored.' }), box,
      h('div', { class: 'dlg__foot' }, [h('button', { type: 'button', class: 'btn btn--ghost', text: 'Copy', onclick: function () { box.select(); navigator.clipboard.writeText(secret).then(function () { toast('Copied.'); }); } }),
        h('button', { type: 'button', class: 'btn', text: 'Done', onclick: function () { dlg.close(); dlg.remove(); } })])]));
    document.body.appendChild(dlg); dlg.showModal(); box.select();
  }
  function redirectsView() {
    var main = h('main', { class: 'main' }, [h('h1', { text: 'Redirects and routes' }), h('p', { class: 'lead', text: 'A redirect sends visitors and search engines from an old address to a new one. Adding or removing one publishes straight away.' })]);
    var out = h('div', { class: 'stack' }); main.appendChild(out);
    var load = function () {
      Promise.all([api('GET', 'redirects'), api('GET', 'routes')]).then(function (res) {
        out.textContent = '';
        var from = h('input', { type: 'text', placeholder: '/old-page/' }), to = h('input', { type: 'text', placeholder: '/new-page/ or https://…' });
        var add = h('button', { type: 'button', class: 'btn', text: 'Add redirect', disabled: !can('admin') });
        add.addEventListener('click', function () { busy(add, 'Publishing…', api('POST', 'redirects', { from_path: from.value, to_path: to.value }).then(function () { toast('Redirect published.'); load(); }).catch(function (e) { toast(e.message); })); });
        out.appendChild(h('div', { class: 'card stack narrow' }, [h('h3', { text: 'Add a redirect' }), h('label', { class: 'field' }, ['From', from]), h('label', { class: 'field' }, ['To', to]), h('div', {}, [add])]));
        out.appendChild(res[0].redirects.length ? table(['From', 'To', 'Type', ''], res[0].redirects.map(function (r) {
          return h('tr', {}, [td(r.from_path), td(r.to_path), td(String(r.status_code)), td(can('admin') ? h('button', { type: 'button', class: 'link danger', text: 'Remove', onclick: function () { sure('Remove this redirect?', r.from_path + ' will stop forwarding.', 'Remove').then(function (ok) { if (ok) api('DELETE', 'redirects/' + r.id).then(load).catch(function (e) { toast(e.message); }); }); } }) : '')]);
        })) : h('p', { class: 'muted', text: 'No redirects yet.' }));
        out.appendChild(h('h2', { class: 'colhead', text: 'Routes: where each kind of page is published' }));
        out.appendChild(table(['Kind of page', 'Published at', ''], res[1].routes.map(function (r) {
          var where = r.type === 'advisor-article' ? 'insights.spacesos.com/<slug>/' : 'valorahq.com/' + (r.path_prefix ? r.path_prefix + '/' : '') + '<slug>/';
          return h('tr', {}, [td(r.label), td(where), td(can('admin') && r.type === 'consumer-page' ? h('button', { type: 'button', class: 'link', text: 'Change folder', onclick: function () {
            modal('Folder for ' + r.label + ' pages', 'Leave empty for none. Applies to pages published from now on.', { input: true, value: r.path_prefix, ok: 'Save', allowEmpty: true }).then(function (p) {
              if (p === null) return;
              api('PATCH', 'routes/' + r.key, { path_prefix: p }).then(function () { return api('GET', 'me'); }).then(function (m) { state.routes = m.routes; load(); }).catch(function (e) { toast(e.message); }); });
          } }) : '')]);
        })));
      }).catch(function (e) { out.appendChild(h('p', { class: 'err', text: e.message })); });
    };
    load();
    return main;
  }
  function auditView() {
    var main = h('main', { class: 'main' }, [h('h1', { text: 'Audit log' }), h('p', { class: 'lead', text: 'Every action, who did it, when, and whether it came from the editor, the API or an MCP agent.' })]);
    api('GET', 'audit?limit=300').then(function (r) {
      main.appendChild(table(['When', 'Who', 'Via', 'Action', 'On', 'Detail'], r.entries.map(function (e) {
        var detail = Object.keys(e.detail).map(function (k) { return k + ': ' + (typeof e.detail[k] === 'string' ? e.detail[k] : JSON.stringify(e.detail[k])); }).join(' · ');
        return h('tr', {}, [td(fmt(e.at)), td(e.actor_name), td(e.via), td(e.action), td(e.target_type === 'article' ? h('button', { type: 'button', class: 'link', text: 'article', onclick: function () { openArticle(e.target_id); } }) : e.target_type + ' ' + e.target_id), td(detail)]);
      })));
    }).catch(function (e) { main.appendChild(h('p', { class: 'err', text: e.message })); });
    return main;
  }
  function apiView() {
    var o = window.location.origin;
    return h('main', { class: 'main' }, [h('h1', { text: 'API and MCP for agents' }),
      h('p', { class: 'lead', text: 'Everything this editor does goes through the admin API, so an agent can do all of it without a browser. An agent uses a token created under People and tokens, and has that person’s role.' }),
      h('div', { class: 'stack narrow' }, [
        h('div', { class: 'card stack' }, [h('h3', { text: 'REST API' }), h('pre', { class: 'code', text: '# create a draft\ncurl -X POST ' + o + '/api/cms/v1/articles \\\n  -H "Authorization: Bearer $VALORA_CMS_TOKEN" -H "Content-Type: application/json" \\\n  -d \'{"type":"consumer-page","title":"Financial advisor for pilots"}\'\n\n# today\'s six slots and the done count\ncurl -H "Authorization: Bearer $VALORA_CMS_TOKEN" ' + o + '/api/cms/v1/calendar' }),
          h('p', { class: 'muted', text: 'The full route list is in cms/README.md in the repository.' })]),
        h('div', { class: 'card stack' }, [h('h3', { text: 'MCP server' }), h('p', { text: 'Streamable HTTP endpoint with the same tools: create, edit, illustrate, submit, approve, schedule, preview, calendar, redirects and audit.' }),
          h('pre', { class: 'code', text: '{\n  "mcpServers": {\n    "valora-cms": {\n      "type": "http",\n      "url": "' + o + '/api/cms/mcp",\n      "headers": { "Authorization": "Bearer ${VALORA_CMS_TOKEN}" }\n    }\n  }\n}' })])])]);
  }

  /* ---------- frame ---------- */
  function loginView() {
    var email = h('input', { type: 'email', autocomplete: 'username', required: true });
    var pass = h('input', { type: 'password', autocomplete: 'current-password', required: true });
    var err = h('p', { class: 'err', role: 'alert' });
    var button = h('button', { type: 'submit', class: 'btn', text: 'Sign in' });
    var form = h('form', { class: 'login__card' }, [h('h1', { text: 'Valora CMS' }), h('p', { class: 'muted', text: 'Staff sign-in.' }),
      h('label', { class: 'field' }, ['Email', email]), h('label', { class: 'field' }, ['Password', pass]), err, button]);
    form.addEventListener('submit', function (e) {
      e.preventDefault(); err.textContent = '';
      busy(button, 'Signing in…', api('POST', 'login', { email: email.value, password: pass.value }).then(boot).catch(function (x) { err.textContent = x.message; }));
    });
    return h('div', { class: 'login' }, [form]);
  }
  function sidebar() {
    var item = function (text, view, onclick) {
      return h('button', { type: 'button', class: 'side__item' + (state.view === view ? ' is-active' : ''), onclick: onclick || function () { go(view); } }, [h('span', { text: text })]);
    };
    var side = h('nav', { class: 'side', 'aria-label': 'CMS' }, [h('div', { class: 'side__brand' }, ['Valora ', h('span', { text: 'CMS' })]),
      h('div', {}, [h('h2', { text: 'Content' }), item('Today', 'today'), item('Articles', 'articles'), item('Create with AI', 'engine'), item('Site pages', 'sitepages')]),
      h('div', {}, [h('h2', { text: 'Manage' }), item('Redirects and routes', 'redirects'), item('Brand memory', 'memory', openMemory),
        can('admin') ? item('People and tokens', 'users') : null, can('admin', 'qa') ? item('Audit log', 'audit') : null, item('API and MCP', 'api')])]);
    side.appendChild(h('div', { class: 'side__foot' }, [h('span', { text: state.user.name + ' · ' + state.user.role }),
      h('button', { type: 'button', class: 'link', text: 'Sign out', onclick: function () { leave().then(function (ok) { if (ok) api('POST', 'logout').then(function () { state.user = null; state.current = null; render(); }); }); } })]));
    return side;
  }
  function render() {
    app.textContent = '';
    if (!state.user) { app.appendChild(loginView()); return; }
    var views = { today: todayView, articles: articlesView, engine: engineView, sitepages: sitePagesView, redirects: redirectsView, users: usersView, audit: auditView, api: apiView };
    var main = state.view === 'article' && state.current ? articleView() : state.view === 'sitepage' && state.current ? sitePageView() : state.view === 'memory' && state.current ? memoryView() : (views[state.view] || todayView)();
    app.appendChild(h('div', { class: 'shell' }, [sidebar(), main]));
  }
  function boot() {
    return api('GET', 'me').then(function (r) {
      state.user = r.user; state.ai = r.ai; state.storage = r.storage; state.groups = r.site_groups; state.routes = r.routes; state.today = r.today;
      render();
    }).catch(function () { state.user = null; render(); });
  }
  window.addEventListener('beforeunload', function (e) { if (state.current && state.current.dirty) { e.preventDefault(); e.returnValue = ''; } });
  boot();
})();
