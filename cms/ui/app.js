/* Valora CMS editor. Plain DOM, no dependencies. Every action goes through the same admin API
   (/api/cms/v1) that agents use; nothing here has a private back door. */
(function () {
  'use strict';
  var app = document.getElementById('app');
  var state = { user: null, ai: false, storage: 'local', groups: [], routes: [], today: '', sitePages: [], view: 'overview', current: null, date: '', brands: [], brand: null, users: [], tab: 'edit' };

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
    var ideasRow = h('div', { class: 'change__row wrap' });
    var suggestBtn = h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: 'Suggest improvements' });
    suggestBtn.addEventListener('click', function () {
      busy(suggestBtn, 'Reading the page…', api('POST', 'ai/suggest', { doc: aiDoc() }).then(function (r) {
        ideasRow.textContent = '';
        r.suggestions.forEach(function (sg) { var b = h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: sg.label }); b.addEventListener('click', function () { run(sg.instruction, b); }); ideasRow.appendChild(b); });
        if (!r.suggestions.length) ideasRow.appendChild(h('span', { class: 'muted', text: 'Nothing to suggest.' }));
      }).catch(function (e) { toast(e.message); }));
    });
    panel.appendChild(h('div', {}, [suggestBtn])); panel.appendChild(ideasRow);
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
      api('GET', 'articles/' + id).then(function (r) { setArticle(r); state.tab = 'edit'; state.view = 'article'; render(); window.scrollTo(0, 0); }).catch(function (e) { toast(e.message); });
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
    var tabs = h('div', { class: 'tabs', role: 'tablist' }, ['edit', 'preview'].map(function (t) {
      return h('button', { type: 'button', class: state.tab === t ? 'is-on' : '', text: t === 'edit' ? 'Edit' : 'Preview', onclick: function () {
        if (t === 'preview' && cur.dirty) { saveArticle().then(function () { state.tab = t; render(); }).catch(function (e) { toast(e.message); }); return; }
        state.tab = t; render();
      } });
    }));
    var left;
    if (state.tab === 'preview') {
      var pane = h('div', { class: 'previewpane' }), frame = h('iframe', { src: cur.previewUrl, title: 'Page preview' });
      var size = function (cls, text) { return h('button', { type: 'button', class: 'link', text: text, onclick: function () { pane.className = 'previewpane' + (cls ? ' ' + cls : ''); } }); };
      pane.appendChild(h('div', { class: 'previewpane__bar' }, [h('span', { text: (a.type === 'advisor-article' ? 'insights.spacesos.com/' : 'valorahq.com/') + a.slug + '/' }), size('', 'Desktop'), size('is-tablet', 'Tablet'), size('is-mobile', 'Phone'),
        h('a', { href: cur.previewUrl, target: '_blank', rel: 'noopener', text: 'Open in a new tab' })]));
      pane.appendChild(h('div', { class: 'previewpane__stage' }, [frame]));
      left = h('div', { class: 'stack' }, [tabs, notes, pane]);
    } else {
      left = h('div', { class: 'stack' }, [h('div', {}, [tabs]), notes, h('div', { id: 'fields' }), illustrationCard(), del]);
      setTimeout(renderFields, 0);
    }
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
    var main = h('main', { class: 'main' }, [head('Page creation', 'Pages built for *AI and people*', 'Give a topic and the AI writes a full draft, built to be read and cited by AI assistants. Each one is saved as a draft for a writer to check and QA to approve; nothing is published from here.')]);
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
    var main = h('main', { class: 'main' }, [head('Site pages', 'The pages *already on the site*', 'The advisor landing page, the original guides, the team page and the legal pages. Saving a change publishes it, so only QA and admins can save here.')]);
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
    var main = h('main', { class: 'main' }, [head('Team', 'People and *agent tokens*', 'Writers create and edit drafts. QA is the only role that can approve, and approving publishes. Admins manage people, redirects and routes. An agent token acts as the person it belongs to.')]);
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
    var main = h('main', { class: 'main' }, [head('Site structure', 'Redirects and *routes*', 'A redirect sends visitors and search engines from an old address to a new one. Adding or removing one publishes straight away.')]);
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
    var main = h('main', { class: 'main' }, [head('Audit log', 'Who did *what, and when*', 'Every action, who did it, when, and whether it came from the editor, the API or an MCP agent.')]);
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
    return h('main', { class: 'main' }, [head('For agents', 'API and *MCP*', 'Everything this editor does goes through the admin API, so an agent can do all of it without a browser. An agent uses a token created under People and tokens, and has that person’s role.'),
      h('div', { class: 'stack narrow' }, [
        h('div', { class: 'card stack' }, [h('h3', { text: 'REST API' }), h('pre', { class: 'code', text: '# create a draft\ncurl -X POST ' + o + '/api/cms/v1/articles \\\n  -H "Authorization: Bearer $VALORA_CMS_TOKEN" -H "Content-Type: application/json" \\\n  -d \'{"type":"consumer-page","title":"Financial advisor for pilots"}\'\n\n# today\'s six slots and the done count\ncurl -H "Authorization: Bearer $VALORA_CMS_TOKEN" ' + o + '/api/cms/v1/calendar' }),
          h('p', { class: 'muted', text: 'The full route list is in cms/README.md in the repository.' })]),
        h('div', { class: 'card stack' }, [h('h3', { text: 'MCP server' }), h('p', { text: 'Streamable HTTP endpoint with the same tools: create, edit, illustrate, submit, approve, schedule, preview, calendar, redirects and audit.' }),
          h('pre', { class: 'code', text: '{\n  "mcpServers": {\n    "valora-cms": {\n      "type": "http",\n      "url": "' + o + '/api/cms/mcp",\n      "headers": { "Authorization": "Bearer ${VALORA_CMS_TOKEN}" }\n    }\n  }\n}' })])])]);
  }

  /* ---------- growth screens (scoped to the selected brand) ---------- */
  function bq(path) { return path + (path.indexOf('?') === -1 ? '?' : '&') + 'brand=' + state.brand; }
  function brandNow() { return state.brands.find(function (b) { return b.id === state.brand; }) || state.brands[0]; }
  function num(n) { return Number(n || 0).toLocaleString(); }
  function head(eyebrow, title, lead) {
    var h1 = h('h1');
    String(title).split('*').forEach(function (part, i) { h1.appendChild(i % 2 ? h('em', { text: part }) : document.createTextNode(part)); });
    return h('header', { class: 'head' }, [h('p', { class: 'eyebrow', text: eyebrow }), h1, lead ? h('p', { class: 'lead', text: lead }) : null]);
  }
  function stat(value, label, sub, alert) { return h('div', { class: 'stat' + (alert ? ' stat--alert' : '') }, [h('b', { text: value }), h('span', { text: label }), sub ? h('small', { text: sub }) : null]); }
  function textModal(title, message, placeholder, ok) {
    return new Promise(function (resolve) {
      var dlg = h('dialog'), ta = h('textarea', { rows: 8, placeholder: placeholder });
      var close = function (v) { dlg.close(); dlg.remove(); resolve(v); };
      var form = h('form', { class: 'dlg' }, [h('h2', { text: title }), message ? h('p', { text: message }) : null, ta,
        h('div', { class: 'dlg__foot' }, [h('button', { type: 'button', class: 'btn btn--ghost', text: 'Cancel', onclick: function () { close(null); } }), h('button', { type: 'submit', class: 'btn', text: ok || 'Add' })])]);
      form.addEventListener('submit', function (e) { e.preventDefault(); close(ta.value.trim() || null); });
      dlg.addEventListener('cancel', function (e) { e.preventDefault(); close(null); });
      dlg.appendChild(form); document.body.appendChild(dlg); dlg.showModal(); ta.focus();
    });
  }

  function overviewView() {
    var b = brandNow(), main = h('main', { class: 'main' }, [head(b.name, 'How ' + b.name + ' is *being found*', 'Searches, pages, AI answers and leads in one place. Every number here comes from tracked data; anything not measured yet says so.')]);
    api('GET', bq('overview')).then(function (o) {
      var s = o.searches, v = o.ai_visibility, l = o.leads;
      main.appendChild(h('div', { class: 'stats' }, [
        stat(num(s.open), 'opportunities to get found', s.tracked ? num(s.visible) + ' of ' + num(s.tracked) + ' tracked searches already show ' + b.name : 'No searches tracked yet', s.open > 0),
        stat(s.volume_known_for ? num(s.missed_searches) : '—', 'searches a month not finding you', s.volume_known_for ? 'Across ' + num(s.volume_known_for) + ' searches with known volume' : 'Add search volumes to see this'),
        stat(v.rate === null ? '—' : v.rate + '%', 'of AI answers mention ' + b.name, v.runs_30d ? num(v.runs_30d) + ' answers checked in 30 days' : 'No AI answers checked yet'),
        stat(num(l.last_30d), 'leads in the last 30 days', num(l.new) + ' new · ' + num(l.qualified) + ' qualified · ' + num(l.won) + ' won'),
        o.pages ? stat(num(o.pages.published), 'pages published from the CMS', num(o.pages.published_30d) + ' in the last 30 days · ' + num(o.pages.in_progress) + ' in progress') : null,
        stat(num(o.ai_crawler_hits_30d), 'AI crawler visits in 30 days', o.ai_crawler_hits_30d ? '' : 'No server logs ingested yet'),
        stat(num(o.backlinks.live), 'backlinks live', num(o.backlinks.in_progress) + ' in progress'),
        l.spam_filtered ? stat(num(l.spam_filtered), 'junk submissions filtered', 'Kept, hidden from the inbox') : null]));
      main.appendChild(h('div', { class: 'row' }, [h('button', { type: 'button', class: 'btn', text: 'See opportunities', onclick: function () { go('opportunities'); } }),
        h('button', { type: 'button', class: 'btn btn--ghost', text: 'Open leads', onclick: function () { go('leads'); } }), h('button', { type: 'button', class: 'btn btn--ghost', text: "Today's calendar", onclick: function () { go('today'); } })]));
    }).catch(function (e) { main.appendChild(h('p', { class: 'err', text: e.message })); });
    return main;
  }

  function visPill(k) { return h('span', { class: 'pill pill--' + k.visible, text: k.visible === 'yes' ? 'Showing' + (k.position ? ' #' + k.position : '') : k.visible === 'no' ? 'Not visible yet' : 'Not checked' }); }
  function opportunitiesView() {
    var b = brandNow(), main = h('main', { class: 'main' }), body = h('div', { class: 'stack' });
    var selected = {}, active = null;
    var load = function () {
      api('GET', bq('opportunities')).then(function (o) {
        main.textContent = ''; body.textContent = '';
        main.appendChild(head('Search opportunities', '*' + num(o.open) + ' opportunit' + (o.open === 1 ? 'y' : 'ies') + '* to get found',
          o.total ? 'These are searches your future clients make where ' + b.name + ' does not show yet. Write a page that answers them directly.' : 'Add the searches your future clients make. The CMS tracks whether ' + b.name + ' shows for each one and what to write next.'));
        var add = h('button', { type: 'button', class: 'btn', text: 'Add searches' });
        add.addEventListener('click', function () {
          textModal('Add searches', 'One per line. If you know the monthly volume from a keyword tool, add it after a comma.', 'financial advisor for pilots, 320\nhow much does a financial advisor cost', 'Add').then(function (text) {
            if (text) api('POST', bq('keywords'), { text: text }).then(function (r) { toast(r.added + ' added, ' + r.updated + ' updated.'); load(); }).catch(function (e) { toast(e.message); });
          });
        });
        var check = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Check search results' });
        check.addEventListener('click', function () { busy(check, 'Checking…', api('POST', bq('keywords/check'), { ids: Object.keys(selected).map(Number) }).then(function (r) { toast(r.error ? r.error : r.checked + ' searches checked.'); load(); }).catch(function (e) { toast(e.message); })); });
        var vol = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Get monthly volumes' });
        vol.addEventListener('click', function () { busy(vol, 'Fetching…', api('POST', bq('keywords/volumes'), {}).then(function (r) { toast(r.updated + ' volumes updated.'); load(); }).catch(function (e) { toast(e.message); })); });
        var write = h('button', { type: 'button', class: 'btn', text: 'Write a page for the selected searches' });
        write.addEventListener('click', function () {
          var ids = Object.keys(selected).map(Number); if (!ids.length) { toast('Tick the searches the page should answer first.'); return; }
          var first = o.keywords.find(function (k) { return k.id === ids[0]; });
          busy(write, 'Writing…', api('POST', 'ai/draft', { type: 'consumer-page', topic: first.query, keyword_ids: ids }).then(function (r) { openArticle(r.article.id); }).catch(function (e) { toast(e.message); }));
        });
        main.appendChild(h('div', { class: 'toolbar' }, [add, check, vol, h('span', { class: 'grow' }), state.ai && b.is_default ? write : null]));
        if (!o.providers.results || !o.providers.volumes) main.appendChild(h('p', { class: 'note', text: (!o.providers.results ? 'Search results are not connected, so visibility cannot be checked automatically. ' : '') + (!o.providers.volumes ? 'Monthly volumes are not connected; enter them by hand or leave them blank. ' : '') + 'Nothing is estimated.' }));
        main.appendChild(body);
        if (!o.total) return;
        if (o.top.length) {
          if (!active || !o.top.some(function (k) { return k.id === active; })) active = o.top[0].id;
          var chips = h('div', { class: 'chips' }), serp = h('div', { class: 'card' });
          var show = function () {
            var k = o.top.find(function (x) { return x.id === active; });
            chips.textContent = '';
            o.top.forEach(function (x) { chips.appendChild(h('button', { type: 'button', class: 'chip' + (x.id === active ? ' is-on' : ''), text: x.query, onclick: function () { active = x.id; show(); } })); });
            serp.textContent = '';
            var left = h('div', {}, [h('div', { class: 'serp__dots' }, [h('i'), h('i'), h('i')]), h('div', { class: 'serp__bar', text: k.query })]);
            if (!k.serp.length) left.appendChild(h('p', { class: 'muted', text: k.serp_checked_at ? 'No results came back for this search.' : 'Results have not been checked for this search yet.' }));
            k.serp.slice(0, 5).forEach(function (r) {
              var own = b.domains.some(function (d) { return r.url.indexOf(d) !== -1; });
              left.appendChild(h('div', { class: 'result' + (own ? ' is-own' : '') }, [h('small', { text: r.url.replace(/^https?:\/\//, '') }), h('strong', { text: r.title }), h('span', { text: r.snippet })]));
            });
            var right = k.visible === 'yes' ? h('div', { class: 'miss miss--ok' }, [h('b', { text: '#' + (k.position || '') }), h('span', { text: b.name + ' shows for this search.' })])
              : k.monthly_searches === null ? h('div', { class: 'miss miss--idle' }, [h('b', { text: '—' }), h('span', { text: 'Monthly volume not known yet.' })])
              : h('div', { class: 'miss' + (k.visible === 'unknown' ? ' miss--idle' : '') }, [h('b', { text: num(k.monthly_searches) }), h('span', { text: k.visible === 'no' ? "searches last month didn't find you" : 'searches a month. Visibility not checked yet.' })]);
            serp.appendChild(h('div', { class: 'serp' }, [left, right]));
          };
          show();
          body.appendChild(h('p', { class: 'colhead', text: 'Top searches not finding ' + b.name }));
          body.appendChild(chips); body.appendChild(serp);
        }
        body.appendChild(h('p', { class: 'colhead', text: 'All tracked searches' }));
        body.appendChild(table(['', 'Search', 'Monthly searches', 'Status', 'Answered by', ''], o.keywords.map(function (k) {
          var box = h('input', { type: 'checkbox', 'aria-label': 'Select ' + k.query }); box.checked = Boolean(selected[k.id]);
          box.addEventListener('change', function () { if (box.checked) selected[k.id] = true; else delete selected[k.id]; });
          var vcell = h('td', { class: 'num', text: k.monthly_searches === null ? '—' : num(k.monthly_searches) });
          return h('tr', {}, [td(box), td(k.query), vcell, td(visPill(k)),
            td(k.article_id ? h('button', { type: 'button', class: 'link', text: 'Open page', onclick: function () { openArticle(k.article_id); } }) : k.page_url ? h('a', { href: k.page_url, target: '_blank', rel: 'noopener', text: 'Live page' }) : h('span', { class: 'muted', text: 'No page yet' })),
            td(h('button', { type: 'button', class: 'link danger', text: 'Remove', onclick: function () { api('DELETE', 'keywords/' + k.id).then(load).catch(function (e) { toast(e.message); }); } }))]);
        })));
      }).catch(function (e) { main.appendChild(h('p', { class: 'err', text: e.message })); });
    };
    load();
    return main;
  }

  function pagesView() {
    var b = brandNow(), main = h('main', { class: 'main' }, [head('Pages', "Let's get you on top of *your customer's mind*", 'Every page of the site, and the searches each one is meant to answer.')]);
    var filter = h('select', { 'aria-label': 'Show' }, [['all', 'All pages'], ['cms', 'Written in the CMS'], ['site-page', 'Editable site pages'], ['code', 'Built in code'], ['stale', 'Due a refresh']].map(function (o) { return h('option', { value: o[0], text: o[1] }); }));
    var search = h('input', { type: 'text', placeholder: 'Search pages', 'aria-label': 'Search pages' }), out = h('div', { class: 'stack' }), all = [];
    var KIND = { article: 'CMS page', 'site-page': 'Site page', code: 'Built in code', external: 'External page' };
    var draw = function () {
      out.textContent = '';
      var q = search.value.toLowerCase();
      var rows = all.filter(function (p) { return (filter.value === 'all' || (filter.value === 'cms' && p.kind === 'article') || filter.value === p.kind || (filter.value === 'stale' && p.stale)) && (!q || (p.title + ' ' + p.url).toLowerCase().indexOf(q) !== -1); });
      if (!rows.length) out.appendChild(h('p', { class: 'muted', text: 'No pages match.' }));
      rows.slice(0, 200).forEach(function (p) {
        var actions = h('div', { class: 'row' });
        if (p.kind === 'article') actions.appendChild(h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: 'Edit', onclick: function () { openArticle(p.article_id); } }));
        if (p.kind === 'site-page' && p.site_page) actions.appendChild(h('button', { type: 'button', class: 'btn btn--ghost btn--small', text: 'Edit', onclick: function () { openSitePage(p.site_page.kind, p.site_page.id); } }));
        if (p.live && p.url) actions.appendChild(h('a', { class: 'btn btn--ghost btn--small', href: p.url, target: '_blank', rel: 'noopener', text: 'Go to live page' }));
        var row = h('div', { class: 'pagerow' }, [h('div', { class: 'pagerow__top' }, [h('div', { class: 'stack tight' }, [
          h('div', {}, [h('span', { class: 'pill' + (p.kind === 'code' ? ' pill--code' : ''), text: KIND[p.kind] || p.kind }), p.category ? h('span', { class: 'pill', text: p.category }) : null,
            p.kind === 'article' ? statusPill(p.status) : h('span', { class: 'pill pill--published', text: 'Published' }), p.stale ? h('span', { class: 'pill pill--warn', text: 'Due a refresh' }) : null]),
          h('h3', { text: p.title }), p.kind === 'code' ? h('small', { class: 'muted', text: 'Generated by the site build. To change it, edit the code in the repository.' }) : null]), actions])]);
        if (p.keywords.length) {
          var known = p.volume_known_for, label = known ? 'Helps you show up for ' + num(p.searches) + '+ searches a month, including:' : 'Answers ' + p.keywords.length + ' tracked search' + (p.keywords.length > 1 ? 'es' : '') + ' (volumes not known yet):';
          row.appendChild(h('details', {}, [h('summary', { text: label }), h('div', { class: 'chips' }, p.keywords.map(function (k) { return h('span', { class: 'chip chip--static', text: k.query }); }))]));
        }
        out.appendChild(row);
      });
      if (rows.length > 200) out.appendChild(h('p', { class: 'muted', text: 'Showing the first 200 of ' + rows.length + '. Search to narrow down.' }));
    };
    filter.addEventListener('change', draw); search.addEventListener('input', draw);
    main.appendChild(h('div', { class: 'toolbar' }, [filter, search])); main.appendChild(out);
    api('GET', bq('pages')).then(function (r) { all = r.pages; if (!all.length) out.appendChild(h('p', { class: 'muted', text: b.is_default ? 'No pages yet.' : 'Link tracked searches to this brand’s pages from Opportunities to see them here.' })); else draw(); }).catch(function (e) { out.appendChild(h('p', { class: 'err', text: e.message })); });
    return main;
  }

  var LEAD_STATUS = { 'new': 'New lead', contacted: 'Contacted', qualified: 'Qualified', won: 'Won', lost: 'Lost' };
  function leadsView() {
    var b = brandNow(), main = h('main', { class: 'main' }, [head('Leads dashboard', 'Everything you need to *close more deals*', 'Each inquiry, what the person read before sending it, and where it stands.')]);
    var status = h('select', { 'aria-label': 'Status' }, [h('option', { value: '', text: 'Any status' })].concat(Object.keys(LEAD_STATUS).map(function (k) { return h('option', { value: k, text: LEAD_STATUS[k] }); })));
    var search = h('input', { type: 'text', placeholder: 'Search name, email or company', 'aria-label': 'Search' });
    var spam = h('input', { type: 'checkbox', id: 'showspam' }), out = h('div');
    var exportBtn = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Export' });
    exportBtn.addEventListener('click', function () {
      busy(exportBtn, 'Exporting…', fetch('/api/cms/v1/' + bq('leads/export'), { credentials: 'same-origin' }).then(function (r) { if (!r.ok) throw new Error('Only QA and admins can export leads.'); return r.blob(); }).then(function (blob) {
        var a = h('a', { href: URL.createObjectURL(blob), download: 'leads.csv' }); document.body.appendChild(a); a.click(); a.remove();
      }).catch(function (e) { toast(e.message); }));
    });
    var journey = function (l) {
      var dlg = h('dialog'), steps = h('div', { class: 'journey' });
      if (!l.journey.length) steps.appendChild(h('p', { class: 'muted', text: 'No page history was sent with this lead.' }));
      l.journey.forEach(function (st, i) {
        if (i) steps.appendChild(h('div', { class: 'journey__arrow', text: '↓' }));
        steps.appendChild(h('div', { class: 'journey__step' }, [h('b', { text: String(i + 1) }), h('div', {}, [h('small', { text: st.at ? fmt(st.at) : '' }), h('div', { text: st.path }), h('em', { text: st.event.replace(/_/g, ' ') })])]));
      });
      dlg.appendChild(h('div', { class: 'dlg' }, [h('h2', { text: 'Lead journey: ' + (l.name || l.email) }), l.message ? h('p', { class: 'answer', text: l.message }) : null, steps,
        h('div', { class: 'dlg__foot' }, [h('button', { type: 'button', class: 'btn', text: 'Close', onclick: function () { dlg.close(); dlg.remove(); } })])]));
      document.body.appendChild(dlg); dlg.showModal();
    };
    var load = function () {
      api('GET', bq('leads?status=' + status.value + '&q=' + encodeURIComponent(search.value) + (spam.checked ? '&spam=1' : ''))).then(function (r) {
        out.textContent = '';
        if (!r.leads.length) { out.appendChild(h('div', { class: 'card stack' }, [h('h3', { text: spam.checked ? 'No filtered submissions.' : 'No leads yet.' }),
          h('p', { class: 'muted', text: b.has_lead_key ? 'Leads appear here as soon as the website sends them.' : 'This brand’s website is not connected yet. An admin can create its lead key under Brands.' })])); return; }
        out.appendChild(table(['When', 'Name', 'Action', 'Status', 'Owner', 'Notes', ''], r.leads.map(function (l) {
          var d = new Date(l.received_at);
          var st = h('select', { 'aria-label': 'Status' }, Object.keys(LEAD_STATUS).map(function (k) { return h('option', { value: k, text: LEAD_STATUS[k] }); })); st.value = l.status;
          st.addEventListener('change', function () { api('PATCH', 'leads/' + l.id, { status: st.value }).catch(function (e) { toast(e.message); load(); }); });
          var owner = h('select', { 'aria-label': 'Owner' }, [h('option', { value: '', text: 'Unassigned' })].concat(state.users.map(function (u) { return h('option', { value: u.id, text: u.name }); }))); owner.value = l.assigned_to || '';
          owner.addEventListener('change', function () { api('PATCH', 'leads/' + l.id, { assigned_to: owner.value || null }).catch(function (e) { toast(e.message); load(); }); });
          var last = l.notes[l.notes.length - 1];
          var note = h('button', { type: 'button', class: 'link', text: last ? last.body : 'Add a note', onclick: function () { ask('Note on ' + (l.name || l.email), 'What happened?').then(function (text) { if (text) api('POST', 'leads/' + l.id + '/notes', { body: text }).then(load).catch(function (e) { toast(e.message); }); }); } });
          return h('tr', {}, [td(h('div', { class: 'when' }, [d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }), h('small', { text: d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) })])),
            td(h('div', { class: 'who' }, [h('strong', { text: l.name || '—' }), l.email ? h('span', { text: l.email }) : null, l.phone ? h('span', { text: l.phone }) : null, l.company ? h('span', { text: l.company }) : null, l.spam ? h('span', { class: 'danger', text: l.spam_reason }) : null])),
            td(l.action.replace(/\b\w/g, function (c) { return c.toUpperCase(); })), td(st), td(owner), td(note),
            td(h('div', { class: 'stack tight' }, [h('button', { type: 'button', class: 'link', text: 'View journey', onclick: function () { journey(l); } }),
              h('button', { type: 'button', class: 'link' + (l.spam ? '' : ' danger'), text: l.spam ? 'Not spam' : 'Mark as spam', onclick: function () { api('PATCH', 'leads/' + l.id, { spam: !l.spam }).then(load).catch(function (e) { toast(e.message); }); } })]))]);
        })));
      }).catch(function (e) { out.textContent = ''; out.appendChild(h('p', { class: 'err', text: e.message })); });
    };
    [status, spam].forEach(function (x) { x.addEventListener('change', load); }); search.addEventListener('input', load);
    main.appendChild(h('div', { class: 'toolbar' }, [search, status, h('label', { class: 'row small', for: 'showspam' }, [spam, 'Show filtered spam']), h('span', { class: 'grow' }), exportBtn]));
    main.appendChild(out); load();
    return main;
  }

  function barRow(label, value, max, own, suffix) {
    var fill = h('b'); fill.style.width = (max ? Math.round(100 * value / max) : 0) + '%';
    return h('div', { class: 'bar2' + (own ? ' is-own' : '') }, [h('span', { text: label }), h('i', {}, [fill]), h('span', { class: 'muted', text: value + (suffix || '') })]);
  }
  function visibilityView() {
    var b = brandNow(), main = h('main', { class: 'main' }, [head('AI visibility', 'What AI assistants say when *buyers ask*', 'The CMS asks each connected AI assistant your tracked prompts once a day and records whether ' + b.name + ' is in the answer, who else is, and what was cited.')]);
    var body = h('div', { class: 'stack' });
    var add = h('button', { type: 'button', class: 'btn', text: 'Add prompts' });
    add.addEventListener('click', function () { textModal('Prompts to track', 'One per line, phrased the way a buyer would ask an AI assistant.', 'Who are good financial advisors for airline pilots?\nHow do I choose a fee-only financial advisor?', 'Add').then(function (text) { if (text) api('POST', bq('visibility/prompts'), { text: text }).then(function (r) { toast(r.added + ' added.'); load(); }).catch(function (e) { toast(e.message); }); }); });
    var run = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Run now' });
    run.addEventListener('click', function () { busy(run, 'Asking…', api('POST', bq('visibility/run'), {}).then(function (r) { toast(r.ran + ' answers recorded' + (r.failed ? ', ' + r.failed + ' failed' : '') + '.'); load(); }).catch(function (e) { toast(e.message); })); });
    main.appendChild(h('div', { class: 'toolbar' }, [add, run])); main.appendChild(body);
    var load = function () {
      api('GET', bq('visibility')).then(function (v) {
        body.textContent = '';
        if (!v.engines.length) body.appendChild(h('p', { class: 'note', text: 'No AI assistant is connected yet. An admin needs to add an API key for at least one (Claude, ChatGPT, Perplexity or Gemini).' }));
        body.appendChild(h('div', { class: 'stats' }, [stat(v.rate === null ? '—' : v.rate + '%', 'of answers mention ' + b.name, num(v.runs) + ' answers in ' + v.days + ' days')].concat(v.engines.map(function (e) { return stat(e.rate === null ? '—' : e.rate + '%', e.label, e.runs ? num(e.runs) + ' answers · ' + e.model : 'Not run yet'); }))));
        if (v.last_error) body.appendChild(h('p', { class: 'note', text: v.failed + ' request(s) failed. Latest error: ' + v.last_error }));
        if (v.runs) {
          var maxV = Math.max.apply(null, v.share_of_voice.map(function (x) { return x.mentions; }).concat([1]));
          body.appendChild(h('div', { class: 'card stack' }, [h('h3', { text: 'Share of voice' }), h('p', { class: 'muted small', text: 'How many answers mention each name. Add competitors under Brands to compare.' })].concat(v.share_of_voice.map(function (x) { return barRow(x.name, x.mentions, maxV, x.own); }))));
          if (v.cited_domains.length) { var maxC = v.cited_domains[0].count; body.appendChild(h('div', { class: 'card stack' }, [h('h3', { text: 'Sources the answers cite' })].concat(v.cited_domains.slice(0, 10).map(function (x) { return barRow(x.domain, x.count, maxC, x.own); })))); }
        }
        body.appendChild(h('p', { class: 'colhead', text: 'Tracked prompts' }));
        if (!v.prompts.length) body.appendChild(h('p', { class: 'muted', text: 'No prompts yet. Add the questions your buyers ask.' }));
        v.prompts.forEach(function (p) {
          var row = h('div', { class: 'pagerow' }, [h('div', { class: 'pagerow__top' }, [h('div', { class: 'stack tight' }, [h('h3', { text: p.text }),
            h('div', {}, p.latest.length ? p.latest.map(function (l) { return h('span', { class: 'pill pill--' + (l.mentioned ? 'yes' : 'no'), text: l.provider + ': ' + (l.mentioned ? 'mentioned' + (l.position ? ' #' + l.position : '') : 'not mentioned') }); }) : [h('span', { class: 'pill pill--unknown', text: 'Not run yet' })])]),
            h('button', { type: 'button', class: 'link danger', text: 'Remove', onclick: function () { api('DELETE', 'visibility/prompts/' + p.id).then(load).catch(function (e) { toast(e.message); }); } })])]);
          if (p.latest.length) row.appendChild(h('details', {}, [h('summary', { text: 'Read the latest answers' })].concat(p.latest.map(function (l) {
            return h('div', { class: 'stack tight' }, [h('p', { class: 'colhead', text: l.provider + ' · ' + fmt(l.ran_at) }), h('div', { class: 'answer', text: l.answer }), l.competitors.length ? h('p', { class: 'muted small', text: 'Also mentioned: ' + l.competitors.join(', ') }) : null]);
          }))));
          body.appendChild(row);
        });
      }).catch(function (e) { body.appendChild(h('p', { class: 'err', text: e.message })); });
    };
    load();
    return main;
  }

  function crawlersView() {
    var b = brandNow(), main = h('main', { class: 'main' }, [head('AI crawlers', 'Which AI bots are *reading your pages*', 'Counted from the website’s server logs. Only known AI crawlers are counted; nothing about human visitors is stored.')]);
    var body = h('div', { class: 'stack' }); main.appendChild(body);
    var load = function () {
      api('GET', bq('crawlers')).then(function (c) {
        body.textContent = '';
        if (!c.total) body.appendChild(h('p', { class: 'note', text: 'No server logs have been ingested for this brand yet.' }));
        else {
          body.appendChild(h('div', { class: 'stats' }, [stat(num(c.total), 'AI crawler visits in ' + c.days + ' days'), stat(num(c.bots.length), 'different AI bots'), stat(num(c.pages.length), 'pages read')]));
          body.appendChild(table(['Bot', 'What it is', 'Visits', 'Pages', 'Last seen'], c.bots.map(function (x) { return h('tr', {}, [td(x.bot), td(x.what), h('td', { class: 'num', text: num(x.hits) }), h('td', { class: 'num', text: num(x.pages) }), td(x.last_seen)]); })));
          body.appendChild(h('p', { class: 'colhead', text: 'Most-read pages' }));
          body.appendChild(table(['Page', 'Visits', 'Bots'], c.pages.slice(0, 25).map(function (x) { return h('tr', {}, [td(x.path), h('td', { class: 'num', text: num(x.hits) }), h('td', { class: 'num', text: num(x.bots) })]); })));
        }
        if (can('admin')) {
          var ta = h('textarea', { rows: 6, class: 'mono', placeholder: 'Paste nginx access log lines (combined format)' });
          var go2 = h('button', { type: 'button', class: 'btn btn--ghost', text: 'Ingest log lines' });
          go2.addEventListener('click', function () { if (ta.value.trim()) busy(go2, 'Reading…', api('POST', bq('crawlers/ingest'), { log: ta.value }).then(function (r) { toast(r.matched + ' AI crawler visits found in ' + r.lines + ' lines.'); load(); }).catch(function (e) { toast(e.message); })); });
          body.appendChild(h('div', { class: 'card stack' }, [h('h3', { text: 'Add server logs' }), h('p', { class: 'muted small', text: 'In production a scheduled job posts the logs to the API (see the README). You can also paste lines here.' }), ta, h('div', {}, [go2])]));
        }
      }).catch(function (e) { body.appendChild(h('p', { class: 'err', text: e.message })); });
    };
    load();
    return main;
  }

  function backlinksView() {
    var main = h('main', { class: 'main' }, [head('Backlinks', 'Authority, *one link at a time*', 'A working log of the sites you are pitching and the links that are live. Nothing here is fetched or verified automatically.')]);
    var out = h('div'), src = h('input', { type: 'text', placeholder: 'https://site-that-links.com/article' }), target = h('input', { type: 'text', placeholder: 'Page on your site it links to (optional)' });
    var add = h('button', { type: 'button', class: 'btn', text: 'Add' });
    var load = function () {
      api('GET', bq('backlinks')).then(function (r) {
        out.textContent = '';
        out.appendChild(r.backlinks.length ? table(['Linking page', 'Links to', 'Status', 'Notes'], r.backlinks.map(function (l) {
          var st = h('select', { 'aria-label': 'Status' }, ['prospect', 'pitched', 'live', 'lost'].map(function (x) { return h('option', { value: x, text: x.charAt(0).toUpperCase() + x.slice(1) }); })); st.value = l.status;
          st.addEventListener('change', function () { api('PATCH', 'backlinks/' + l.id, { status: st.value }).catch(function (e) { toast(e.message); load(); }); });
          return h('tr', {}, [td(h('a', { href: l.source_url, target: '_blank', rel: 'noopener noreferrer', text: l.source_url.replace(/^https?:\/\//, '').slice(0, 60) })), td(l.target_url || '—'), td(st),
            td(h('button', { type: 'button', class: 'link', text: l.notes || 'Add a note', onclick: function () { ask('Note', 'Contact, date pitched, next step', l.notes).then(function (t) { if (t) api('PATCH', 'backlinks/' + l.id, { notes: t }).then(load).catch(function (e) { toast(e.message); }); }); } }))]);
        })) : h('p', { class: 'muted', text: 'No backlinks logged yet.' }));
      }).catch(function (e) { out.appendChild(h('p', { class: 'err', text: e.message })); });
    };
    add.addEventListener('click', function () { busy(add, 'Adding…', api('POST', bq('backlinks'), { source_url: src.value, target_url: target.value }).then(function () { src.value = ''; target.value = ''; load(); }).catch(function (e) { toast(e.message); })); });
    main.appendChild(h('div', { class: 'toolbar' }, [src, target, add])); main.appendChild(out); load();
    return main;
  }

  function brandsView() {
    var main = h('main', { class: 'main' }, [head('Brands', 'Valora and the *firms you work for*', 'Each brand has its own searches, AI prompts, leads, crawler logs and backlinks. Use the switcher at the top of the menu to move between them.')]);
    var out = h('div', { class: 'stack' }); main.appendChild(out);
    var compText = function (b) { return b.competitors.map(function (c) { return c.name + (c.domains.length ? ' | ' + c.domains.join(' ') : ''); }).join('\n'); };
    var parseComp = function (text) { return text.split('\n').map(function (line) { var p = line.split('|'); return { name: (p[0] || '').trim(), domains: (p[1] || '').trim().split(/\s+/).filter(Boolean) }; }).filter(function (c) { return c.name; }); };
    var refresh = function () { return api('GET', 'brands').then(function (r) { state.brands = r.brands; }); };
    var form = function (b) {
      var f = { name: h('input', { type: 'text', value: b ? b.name : '' }), domains: h('input', { type: 'text', value: b ? b.domains.join(', ') : '', placeholder: 'example.com' }),
        aliases: h('input', { type: 'text', value: b ? b.aliases.join(', ') : '', placeholder: 'Names AI answers might use' }), comp: h('textarea', { rows: 3, placeholder: 'One per line: Name | domain.com' }) };
      f.comp.value = b ? compText(b) : '';
      var save = h('button', { type: 'button', class: 'btn', text: b ? 'Save' : 'Add brand', disabled: !can('admin') });
      save.addEventListener('click', function () {
        var body = { name: f.name.value, domains: f.domains.value, aliases: f.aliases.value, competitors: parseComp(f.comp.value) };
        busy(save, 'Saving…', api(b ? 'PATCH' : 'POST', b ? 'brands/' + b.id : 'brands', body).then(refresh).then(function () { toast('Saved.'); render(); }).catch(function (e) { toast(e.message); }));
      });
      var key = b && can('admin') ? h('button', { type: 'button', class: 'btn btn--ghost', text: b.has_lead_key ? 'Replace lead key' : 'Create lead key' }) : null;
      if (key) key.addEventListener('click', function () {
        (b.has_lead_key ? sure('Replace the lead key?', 'The website stops sending leads until it is updated with the new key.', 'Replace') : Promise.resolve(true)).then(function (ok) {
          if (ok) api('POST', 'brands/' + b.id + '/lead-key', {}).then(function (r) { showSecret('Lead key for ' + b.name, r.lead_key); return refresh(); }).catch(function (e) { toast(e.message); });
        });
      });
      return h('div', { class: 'card stack narrow' }, [h('h3', { text: b ? b.name + (b.is_default ? ' (this site)' : '') : 'Add a brand' }), h('label', { class: 'field' }, ['Name', f.name]), h('label', { class: 'field' }, ['Website domains', f.domains]),
        h('label', { class: 'field' }, ['Also known as', f.aliases]), h('label', { class: 'field' }, ['Competitors to compare against', f.comp]), h('div', { class: 'row' }, [save, key]),
        b ? h('p', { class: 'muted small', text: b.has_lead_key ? 'Website connected for leads.' : 'Website not connected for leads yet.' }) : null]);
    };
    state.brands.forEach(function (b) { out.appendChild(form(b)); });
    if (can('admin')) out.appendChild(form(null));
    return main;
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
  var ICONS = {
    overview: '<path d="M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6v-9h-6v9Zm0-16v5h6V4h-6Z"/>', opportunities: '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    pages: '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.8 3 2.8 14 0 17M12 3.5c-2.8 3-2.8 14 0 17"/>', leads: '<circle cx="9" cy="8.5" r="3.2"/><path d="M3 19.5c.6-3.4 3-5 6-5s5.4 1.6 6 5M16 5.6a3.2 3.2 0 0 1 0 5.8M18 14.8c1.7.6 2.7 2.2 3 4.7"/>',
    visibility: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/>', crawlers: '<rect x="5" y="8" width="14" height="10" rx="3"/><path d="M12 8V4.5M9 13h.01M15 13h.01M2.5 13h2.5M19 13h2.5"/>',
    backlinks: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.700-5.700l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.700 5.700l1-1"/>', today: '<rect x="3.500" y="5" width="17" height="15.500" rx="2.500"/><path d="M3.500 10h17M8 3v4M16 3v4"/>',
    articles: '<path d="M6 3.500h9l4 4V20.500H6v-17Z"/><path d="M14.500 3.500V8H19M9 12.500h7M9 16h7"/>', engine: '<path d="m12 3 1.800 5.200L19 10l-5.200 1.800L12 17l-1.800-5.200L5 10l5.200-1.800L12 3ZM18.500 16l.8 2.200 2.200.8-2.200.8-.8 2.200-.8-2.200-2.200-.8 2.200-.8.8-2.200Z"/>',
    sitepages: '<rect x="3.500" y="4.500" width="17" height="15" rx="2.500"/><path d="M3.500 9h17M7.500 13h5M7.500 16h8"/>', redirects: '<path d="M4 8h12l-3-3M20 16H8l3 3"/>',
    memory: '<path d="M12 4.500c-3 0-5 2-5 4.500 0 1-.5 1.500-1.200 2.200C5 12 4.500 13 4.500 14c0 2.500 2 4.500 4.500 4.500h6c2.500 0 4.500-2 4.500-4.500 0-1-.5-2-1.300-2.800C17.500 10.500 17 10 17 9c0-2.500-2-4.500-5-4.500Z"/><path d="M12 4.500v14"/>', brands: '<path d="M4 20V9l8-5 8 5v11M9.500 20v-6h5v6"/>',
    users: '<circle cx="12" cy="8.500" r="3.500"/><path d="M5 20c.7-3.800 3.500-5.500 7-5.500s6.300 1.700 7 5.500"/>', audit: '<path d="M12 7v5l3 2"/><circle cx="12" cy="12" r="8.500"/>', api: '<path d="m8.500 8-4 4 4 4M15.500 8l4 4-4 4M13.500 5l-3 14"/>'
  };
  function icon(name) {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('fill', 'none'); svg.setAttribute('stroke', 'currentColor'); svg.setAttribute('stroke-width', '1.6');
    svg.setAttribute('stroke-linecap', 'round'); svg.setAttribute('stroke-linejoin', 'round'); svg.setAttribute('aria-hidden', 'true');
    svg.innerHTML = ICONS[name] || '';
    return svg;
  }
  function sidebar() {
    var item = function (text, view, onclick) {
      return h('button', { type: 'button', class: 'side__item' + (state.view === view ? ' is-active' : ''), onclick: onclick || function () { go(view); } }, [icon(view), h('span', { text: text })]);
    };
    var logo = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    logo.setAttribute('viewBox', '0 0 32 32'); logo.setAttribute('fill', 'none'); logo.setAttribute('stroke', 'currentColor'); logo.setAttribute('stroke-width', '1.6'); logo.setAttribute('aria-hidden', 'true');
    logo.innerHTML = '<circle cx="16" cy="16" r="13"/><path d="M8 17c2-6 5-6 7 0s5 6 8 0" stroke-linecap="round"/>';
    var pick = h('select', { 'aria-label': 'Brand' }, state.brands.map(function (b) { return h('option', { value: b.id, text: b.name }); })); pick.value = state.brand;
    pick.addEventListener('change', function () { leave().then(function (ok) { if (!ok) { pick.value = state.brand; return; } state.brand = Number(pick.value); state.current = null; if (['article', 'sitepage', 'memory'].indexOf(state.view) !== -1) state.view = 'overview'; render(); }); });
    var own = brandNow().is_default;
    var side = h('nav', { class: 'side', 'aria-label': 'CMS' }, [h('div', { class: 'side__brand' }, [logo, 'Valora', h('small', { text: 'CMS' })]), h('div', { class: 'side__switch' }, [pick]),
      h('div', {}, [h('h2', { text: 'Growth' }), item('Overview', 'overview'), item('Opportunities', 'opportunities'), item('Pages', 'pages'), item('Leads', 'leads'), item('AI visibility', 'visibility'), item('AI crawlers', 'crawlers'), item('Backlinks', 'backlinks')]),
      own ? h('div', {}, [h('h2', { text: 'Content' }), item('Today', 'today'), item('Articles', 'articles'), item('Create with AI', 'engine'), item('Site pages', 'sitepages')]) : null,
      h('div', {}, [h('h2', { text: 'Manage' }), item('Brands', 'brands'), own ? item('Redirects and routes', 'redirects') : null, item('Brand memory', 'memory', openMemory),
        can('admin') ? item('People and tokens', 'users') : null, can('admin', 'qa') ? item('Audit log', 'audit') : null, item('API and MCP', 'api')])]);
    side.appendChild(h('div', { class: 'side__foot' }, [h('span', { text: state.user.name + ' · ' + state.user.role }),
      h('button', { type: 'button', class: 'link', text: 'Sign out', onclick: function () { leave().then(function (ok) { if (ok) api('POST', 'logout').then(function () { state.user = null; state.current = null; render(); }); }); } })]));
    return side;
  }
  function render() {
    app.textContent = '';
    if (!state.user) { app.appendChild(loginView()); return; }
    var views = { overview: overviewView, opportunities: opportunitiesView, pages: pagesView, leads: leadsView, visibility: visibilityView, crawlers: crawlersView, backlinks: backlinksView, brands: brandsView,
      today: todayView, articles: articlesView, engine: engineView, sitepages: sitePagesView, redirects: redirectsView, users: usersView, audit: auditView, api: apiView };
    var main = state.view === 'article' && state.current ? articleView() : state.view === 'sitepage' && state.current ? sitePageView() : state.view === 'memory' && state.current ? memoryView() : (views[state.view] || overviewView)();
    app.appendChild(h('div', { class: 'shell' }, [sidebar(), main]));
  }
  function boot() {
    return api('GET', 'me').then(function (r) {
      state.user = r.user; state.ai = r.ai; state.storage = r.storage; state.groups = r.site_groups; state.routes = r.routes; state.today = r.today; state.brands = r.brands; state.users = r.users;
      if (!state.brands.some(function (b) { return b.id === state.brand; })) state.brand = (state.brands.find(function (b) { return b.is_default; }) || state.brands[0]).id;
      render();
    }).catch(function () { state.user = null; render(); });
  }
  window.addEventListener('beforeunload', function (e) { if (state.current && state.current.dirty) { e.preventDefault(); e.returnValue = ''; } });
  boot();
})();
