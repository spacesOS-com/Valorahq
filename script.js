/* =========================================================
   Valora — interaction + animation layer
   Vanilla JS, no dependencies.
   ========================================================= */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $  = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------------------------------------------------------
     1. Page load curtain
     --------------------------------------------------------- */
  function curtain() {
    if (reduced) return;
    var el = document.createElement('div');
    el.className = 'curtain';
    el.innerHTML = '<span class="curtain__word">Valora</span>';
    document.body.appendChild(el);
    document.documentElement.style.overflow = 'hidden';

    window.setTimeout(function () {
      el.classList.add('is-gone');
      document.documentElement.style.overflow = '';
      window.setTimeout(function () { el.remove(); }, 1200);
    }, 1100);
  }

  /* ---------------------------------------------------------
     2. Split headlines into animatable lines (keeps inline tags)
     --------------------------------------------------------- */
  function splitByBr(node) {
    var lines = [document.createDocumentFragment()];

    Array.prototype.forEach.call(node.childNodes, function (child) {
      if (child.nodeName === 'BR') { lines.push(document.createDocumentFragment()); return; }

      if (child.nodeType === 1 && child.querySelector('br')) {
        var parts = splitByBr(child);
        parts.forEach(function (frag, i) {
          var shell = child.cloneNode(false);
          shell.appendChild(frag);
          if (i > 0) lines.push(document.createDocumentFragment());
          lines[lines.length - 1].appendChild(shell);
        });
        return;
      }
      lines[lines.length - 1].appendChild(child.cloneNode(true));
    });
    return lines;
  }

  function prepareHeadlines() {
    $$('.display, .hero__title').forEach(function (h) {
      if (!h.querySelector('br')) return;

      var lines = splitByBr(h).filter(function (f) {
        return (f.textContent || '').trim().length > 0;
      });
      if (lines.length < 2) return;

      h.innerHTML = '';
      lines.forEach(function (frag, i) {
        var wrap  = document.createElement('span');
        var inner = document.createElement('span');
        wrap.className = 'line-wrap';
        inner.className = 'line-inner';
        inner.style.setProperty('--d', (i * 0.09).toFixed(2) + 's');
        inner.appendChild(frag);
        wrap.appendChild(inner);
        h.appendChild(wrap);
      });
      h.classList.add('line-reveal');
    });
  }

  /* ---------------------------------------------------------
     3. Reveal on scroll (with per-container stagger)
     --------------------------------------------------------- */
  function reveals() {
    var targets = $$('.reveal, .line-reveal, .diagram, .mock');

    // stagger siblings inside grids/lists
    ['.statement__cols', '.steps', '.mosaic', '.blist', '.insights__grid', '.post-list', '.brand__mocks', '.match__grid', '.feat', '.adv-ticks']
      .forEach(function (sel) {
        $$(sel).forEach(function (group) {
          $$(':scope > *', group).forEach(function (child, i) {
            child.style.setProperty('--d', (i * 0.08).toFixed(2) + 's');
          });
        });
      });

    if (!('IntersectionObserver' in window) || reduced) {
      targets.forEach(function (t) { t.classList.add('is-in'); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        // reveal when entering, or when it was skipped past during a fast scroll
        var passed = !e.isIntersecting && e.boundingClientRect.top < 0;
        if (!e.isIntersecting && !passed) return;
        e.target.classList.add('is-in');
        io.unobserve(e.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

    targets.forEach(function (t) { io.observe(t); });

    // Backstop: a very fast scroll (or an anchor jump) can move an element from
    // below the viewport to above it between observer samples, so no entry ever
    // fires and the content would stay invisible. Sweep the remainder on scroll.
    var pending = targets.slice();
    var queued = false;

    function sweep() {
      var limit = window.innerHeight * 0.92;
      pending = pending.filter(function (el) {
        if (el.classList.contains('is-in')) return false;
        if (el.getBoundingClientRect().top > limit) return true;
        el.classList.add('is-in');
        io.unobserve(el);
        return false;
      });
      queued = false;
      if (!pending.length) {
        window.removeEventListener('scroll', onScroll);
        window.removeEventListener('resize', sweep);
      }
    }

    function onScroll() {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(sweep);
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', sweep);
  }

  /* ---------------------------------------------------------
     4. Header: shrink, auto-hide, scroll progress
     --------------------------------------------------------- */
  function header() {
    var head = $('#siteHeader');
    var bar  = document.createElement('div');
    bar.className = 'scroll-progress';
    head.appendChild(bar);

    var last = 0;
    var toTop = $('#toTop');
    var ctaFloat = $('#ctaFloat');

    function onScroll() {
      var y   = window.scrollY || document.documentElement.scrollTop;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      var p   = max > 0 ? y / max : 0;

      bar.style.transform = 'scaleX(' + p.toFixed(4) + ')';
      head.classList.toggle('is-stuck', y > 20);

      // hide on scroll down, reveal on scroll up (not while menu is open)
      if (!$('#primaryNav').classList.contains('is-open')) {
        head.classList.toggle('is-hidden', y > last && y > 320);
      }
      last = y;

      toTop.classList.toggle('is-on', y > 700);
      toTop.style.setProperty('--p', (p * 100).toFixed(1));

      if (ctaFloat) ctaFloat.classList.toggle('is-on', y > 420);
    }

    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    // dock the floating CTA while its own target section is on screen
    if (ctaFloat && document.getElementById('contact')) {
      new IntersectionObserver(function (entries) {
        ctaFloat.classList.toggle('is-docked', entries[0].isIntersecting);
      }, { rootMargin: '-35% 0px' }).observe(document.getElementById('contact'));
    }
  }

  /* ---------------------------------------------------------
     5. Mobile navigation
     --------------------------------------------------------- */
  function nav() {
    var btn = $('#navToggle');
    var menu = $('#primaryNav');
    if (!btn) return;

    function close() {
      closeDropdowns();
      menu.classList.remove('is-open');
      btn.classList.remove('is-open');
      btn.setAttribute('aria-expanded', 'false');
      btn.setAttribute('aria-label', 'Open menu');
    }

    btn.addEventListener('click', function () {
      var open = menu.classList.toggle('is-open');
      btn.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', String(open));
      btn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      if (open) $('#siteHeader').classList.remove('is-hidden');
    });

    var dropdowns = $$('.nav-menu__toggle', menu);
    function closeDropdowns(except) {
      dropdowns.forEach(function (toggle) {
        if (toggle === except) return;
        toggle.setAttribute('aria-expanded', 'false');
        var panel = document.getElementById(toggle.getAttribute('aria-controls'));
        if (panel) panel.hidden = true;
      });
    }
    dropdowns.forEach(function (toggle) {
      toggle.addEventListener('click', function () {
        var panel = document.getElementById(toggle.getAttribute('aria-controls'));
        var opening = toggle.getAttribute('aria-expanded') !== 'true';
        closeDropdowns(toggle);
        toggle.setAttribute('aria-expanded', String(opening));
        panel.hidden = !opening;
      });
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.nav-menu')) closeDropdowns();
    });
    menu.addEventListener('focusout', function (e) {
      if (!e.relatedTarget || !menu.contains(e.relatedTarget)) closeDropdowns();
    });
    $$('#primaryNav a').forEach(function (a) { a.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    window.addEventListener('resize', function () { if (window.innerWidth > 900) close(); });
  }

  /* ---------------------------------------------------------
     6. Parallax (hero image, chapter image, mosaic drift)
     --------------------------------------------------------- */
  function parallax() {
    if (reduced) return;

    var items = [
      { el: $('.chapter > img'),   speed: 0.12, scale: 1.14 },
      { el: $('.life__media img'), speed: 0.06, scale: 1.10 },
      { el: $('.mos--e img'),      speed: 0.05, scale: 1.08 }
    ].filter(function (i) { return !!i.el; });

    if (!items.length) return;
    var ticking = false;

    // let the load-in settle before parallax takes over a transform
    window.setTimeout(function () {
      items.forEach(function (i) { i.hold = false; });
    }, 2700);

    function run() {
      var vh = window.innerHeight;
      items.forEach(function (item) {
        if (item.hold) return;
        var host = item.el.closest('section') || item.el.parentElement;
        var r = host.getBoundingClientRect();
        if (r.bottom < -200 || r.top > vh + 200) return;
        var mid = r.top + r.height / 2 - vh / 2;
        var shift = (-mid * item.speed).toFixed(2);
        item.el.style.transform = 'translate3d(0,' + shift + 'px,0) scale(' + item.scale + ')';
      });
      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(run);
    }, { passive: true });

    window.addEventListener('resize', run);
    run();
  }

  /* ---------------------------------------------------------
     7. Animated stat counters
     --------------------------------------------------------- */
  function counters() {
    var nums = $$('.stat__num[data-count]');
    if (!nums.length) return;

    function format(n, el) {
      var dec = parseInt(el.dataset.decimals || '0', 10);
      var v = dec ? n.toFixed(dec) : Math.round(n);
      var out = v >= 1000 ? v.toLocaleString('en-US') : String(v);
      return (el.dataset.prefix || '') + out + (el.dataset.suffix || '');
    }

    function run(el) {
      var target = parseFloat(el.dataset.count);
      if (reduced) { el.textContent = format(target, el); return; }

      var dur = 1600, t0 = performance.now();
      el.classList.add('is-counting');

      (function step(now) {
        var p = Math.min((now - t0) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = format(target * eased, el);
        if (p < 1) requestAnimationFrame(step);
        else el.classList.remove('is-counting');
      })(t0);
    }

    if (!('IntersectionObserver' in window)) { nums.forEach(run); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        run(e.target);
        io.unobserve(e.target);
      });
    }, { threshold: 0.4 });
    nums.forEach(function (n) { io.observe(n); });
  }

  /* ---------------------------------------------------------
     8. Accordion
     --------------------------------------------------------- */
  function accordion() {
    var root = $('#accordion');
    if (!root) return;
    var items = $$('.acc__item', root);

    function setHeight(item, open) {
      var panel = $('.acc__panel', item);
      panel.style.height = open ? panel.scrollHeight + 'px' : '0px';
    }

    items.forEach(function (item) {
      setHeight(item, item.classList.contains('is-open'));

      $('.acc__head', item).addEventListener('click', function () {
        var willOpen = !item.classList.contains('is-open');

        items.forEach(function (other) {
          other.classList.remove('is-open');
          $('.acc__head', other).setAttribute('aria-expanded', 'false');
          setHeight(other, false);
        });

        if (willOpen) {
          item.classList.add('is-open');
          $('.acc__head', item).setAttribute('aria-expanded', 'true');
          setHeight(item, true);
        }
      });
    });

    window.addEventListener('resize', function () {
      items.forEach(function (i) { setHeight(i, i.classList.contains('is-open')); });
    });
  }

  /* ---------------------------------------------------------
     9. Advisor filter + search
     --------------------------------------------------------- */
  function advisors() {
    var grid = $('#advisorGrid');
    if (!grid) return;

    var cards = $$('.acard', grid);
    var chips = $$('.chip');
    var input = $('#advisorSearch');
    var empty = $('#matchEmpty');
    var filter = 'all';

    function apply() {
      var q = input ? (input.value || '').trim().toLowerCase() : '';
      var shown = 0;

      cards.forEach(function (card, i) {
        var tags = card.dataset.tags || '';
        var hay  = ((card.dataset.name || '') + ' ' + tags + ' ' + card.textContent).toLowerCase();
        var ok   = (filter === 'all' || tags.indexOf(filter) > -1) && (!q || hay.indexOf(q) > -1);

        card.classList.toggle('is-hidden', !ok);
        if (ok) {
          shown++;
          // restart the entry animation
          card.style.animation = 'none';
          void card.offsetWidth;
          card.style.animation = '';
          card.style.animationDelay = (i * 0.06).toFixed(2) + 's';
        }
      });

      empty.hidden = shown > 0;
    }

    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        chips.forEach(function (c) {
          c.classList.remove('is-active');
          c.setAttribute('aria-selected', 'false');
        });
        chip.classList.add('is-active');
        chip.setAttribute('aria-selected', 'true');
        filter = chip.dataset.filter;
        apply();
      });
    });

    if (input) {
      var t;
      input.addEventListener('input', function () {
        clearTimeout(t);
        t = setTimeout(apply, 140);
      });
    }
  }

  /* ---------------------------------------------------------
     10. Services switcher (click + keyboard + autoplay)
     --------------------------------------------------------- */
  function services() {
    var list = $('#serviceList');
    if (!list) return;

    var btns   = $$('.slist__btn', list);
    var panels = $$('.spanel');
    var timer;
    var idle = true;

    function show(id) {
      btns.forEach(function (b) { b.classList.toggle('is-active', b.dataset.service === id); });
      panels.forEach(function (p) { p.classList.toggle('is-active', p.dataset.panel === id); });
    }

    btns.forEach(function (b) {
      b.addEventListener('click', function () { idle = false; show(b.dataset.service); });
      b.addEventListener('mouseenter', function () { if (idle) show(b.dataset.service); });
      b.addEventListener('focus', function () { show(b.dataset.service); });
    });

    // gentle autoplay until the visitor interacts
    if (reduced) return;
    var i = 0;
    timer = setInterval(function () {
      if (!idle) { clearInterval(timer); return; }
      i = (i + 1) % btns.length;
      show(btns[i].dataset.service);
    }, 4200);

    list.addEventListener('pointerdown', function () { idle = false; });
  }

  /* ---------------------------------------------------------
     11. Magnetic buttons
     --------------------------------------------------------- */
  function magnetic() {
    if (reduced || !window.matchMedia('(pointer:fine)').matches) return;

    $$('.btn').forEach(function (btn) {
      btn.classList.add('btn--magnetic');

      btn.addEventListener('mousemove', function (e) {
        var r = btn.getBoundingClientRect();
        var x = (e.clientX - r.left - r.width / 2) * 0.22;
        var y = (e.clientY - r.top - r.height / 2) * 0.32;
        btn.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
      });

      btn.addEventListener('mouseleave', function () { btn.style.transform = ''; });
    });
  }

  /* ---------------------------------------------------------
     12. Lead forms (hero card, page form, modal, advisor forms)
     Any <form data-lead="Client|Advisor"> is handled here;
     field wrappers marked [data-field] get .has-error.
     --------------------------------------------------------- */
  var SHEET_ENDPOINT = 'https://script.google.com/macros/s/AKfycbx4mCwhZBQS-0W-UAybBeIJm67scGp4cpwAR_19l4g-FSa-XacfhNyOAPT0W0CEd0uc/exec';
  var LEAD_FAIL = 'Sorry — we could not send that. Please email barot@valorahq.com.';

  var LEAD_MSGS = {
    name:     'Please enter your name.',
    email:    'Please enter a valid email.',
    phone:    'Please enter a valid phone number.',
    goal:     'Pick the closest match.',
    assets:   'Pick the closest range.',
    situation: 'Pick the closest match.',
    location: 'Please enter your city and state.'
  };

  function setLeadError(f, name, msg) {
    var slot = $('[data-err="' + name + '"]', f);
    var el   = f.elements[name];
    if (el && el.length !== undefined) el = el[0]; // RadioNodeList (grouped checkboxes/radios) -> first
    var wrap = el && el.closest ? el.closest('[data-field]') : null;
    if (slot) slot.textContent = msg || '';
    if (wrap) wrap.classList.toggle('has-error', !!msg);
  }

  function fieldError(el) {
    var v = (el.value || '').trim();
    if (el.type === 'email') return !/^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(v);
    if (el.type === 'tel')   return v.replace(/\D/g, '').length < 7;
    return v.length < (el.name === 'name' ? 2 : 1);
  }

  function validateLead(f) {
    var firstBad = null;
    $$('input[required], select[required], textarea[required]', f).forEach(function (el) {
      var bad = fieldError(el);
      setLeadError(f, el.name, bad ? (LEAD_MSGS[el.name] || 'Required.') : '');
      if (bad && !firstBad) firstBad = el;
    });
    if (firstBad) firstBad.focus();
    return !firstBad;
  }

  function collectLead(f) {
    var v = {};
    Array.prototype.forEach.call(f.elements, function (el) {
      if (!el.name || el.disabled || /^(submit|button)$/.test(el.type)) return;
      if (el.type === 'checkbox') {
        if (el.checked) v[el.name] = (v[el.name] ? v[el.name] + ', ' : '') + el.value;
        return;
      }
      if (el.type === 'radio' && !el.checked) return;
      var val = (el.value || '').trim();
      if (val) v[el.name] = val;
    });
    // optional extras (advisor firm / AUM) go into the note column
    var extra = $$('[data-extra]', f).map(function (el) {
      var val = (el.value || '').trim();
      return val ? el.dataset.extra + ': ' + val : '';
    }).filter(Boolean);
    if (extra.length) v.note = extra.join(' · ') + (v.note ? '\n' + v.note : '');
    if (f.dataset.lead === 'Advisor' && v.goal) v.goal = 'Advisor · ' + v.goal;
    return v;
  }

  function sendLead(v) {
    if (!/^https:\/\//.test(SHEET_ENDPOINT)) {
      return Promise.resolve({ status: 'success', skipped: true });
    }
    return fetch(SHEET_ENDPOINT, { method: 'POST', body: new URLSearchParams(v) })
      .then(function (r) { return r.json().catch(function () { return { status: 'success' }; }); });
  }

  function leadForm(f) {
    var submit = $('button[type="submit"]', f);
    var label  = submit ? submit.textContent : '';
    var host   = f.closest('.hcard, .gate');
    var fine   = host ? $('.hcard__fine, .gate__fine', host) : null;
    var fineText = fine ? fine.textContent : '';

    // clear a field's error as soon as the visitor edits it
    ['input', 'change'].forEach(function (ev) {
      f.addEventListener(ev, function (e) { if (e.target.name) setLeadError(f, e.target.name, ''); });
    });

    function showFail() {
      if (submit) { submit.disabled = false; submit.textContent = label; }
      if (fine) { fine.textContent = LEAD_FAIL; fine.classList.add('is-error'); return; }
      var ok = $('.form__success', f);
      if (ok) { ok.hidden = false; ok.textContent = LEAD_FAIL; }
    }

    function showDone(v) {
      var first = v.name ? v.name.split(' ')[0] : '';
      if (submit) { submit.disabled = false; submit.textContent = label; }

      var done = f.dataset.done ? $(f.dataset.done) : null;
      if (done) {
        f.hidden = true;
        done.hidden = false;
        if (host) host.classList.add('is-done');
        var t = $('[data-done-title]', done);
        if (t && first) t.textContent = 'Thank you, ' + first + '.';
        return;
      }

      var ok = $('.form__success', f);
      var tpl = f.dataset.success || 'Thank you, {name}.';
      f.reset();
      if (ok) {
        ok.hidden = false;
        ok.textContent = tpl.replace('{name}', first);
        ok.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'center' });
      }
    }

    f.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!validateLead(f)) return;

      var v = collectLead(f);
      if (submit) { submit.disabled = true; submit.textContent = 'Sending…'; }
      if (fine) { fine.textContent = fineText; fine.classList.remove('is-error'); }

      sendLead(v)
        .then(function (res) {
          if (res && res.status === 'error') { showFail(); return; }
          showDone(v);
        })
        .catch(showFail);
    });
  }

  /* ---------------------------------------------------------
     12b. /find-your-advisor/ — copy inbound UTM params into the
     hidden data-extra "Source" field, so collectLead folds the
     origin campaign/page into the CRM note + email alert.
     --------------------------------------------------------- */
  function fyaSource() {
    var src = $('#fyaSource');
    if (!src) return;
    var q = new URLSearchParams(window.location.search);
    var parts = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content']
      .map(function (k) { return q.get(k); })
      .filter(Boolean);
    if (parts.length) src.value = parts.join(' / ');
  }

  /* ---------------------------------------------------------
     12a. Multi-step forms (.form--steps, e.g. the full contact form)
     Steps are plain fields in the DOM — required attrs still work with
     JS off, this just shows one .form__step at a time and re-validates
     the current step's required fields before advancing.
     --------------------------------------------------------- */
  function stepForm(f) {
    var steps = $$('.form__step', f);
    if (steps.length < 2) return;
    var idx = 0;

    // Measure the tallest step once at load and lock the form to that
    // height, so switching steps doesn't resize the card/popup around it.
    var maxH = 0;
    steps.forEach(function (s, si) {
      steps.forEach(function (s2, si2) { s2.hidden = si2 !== si; });
      maxH = Math.max(maxH, f.getBoundingClientRect().height);
    });
    if (maxH) f.style.minHeight = maxH + 'px';

    function show(i, scroll) {
      idx = Math.max(0, Math.min(i, steps.length - 1));
      steps.forEach(function (s, si) { s.hidden = si !== idx; });
      var first = $('input, select, textarea', steps[idx]);
      if (first) first.focus({ preventScroll: true });
      if (scroll) f.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'center' });
    }

    $$('[data-step-next]', f).forEach(function (btn) {
      btn.addEventListener('click', function () {
        var step = btn.closest('.form__step');
        var ok = true;
        $$('input[required], select[required], textarea[required]', step).forEach(function (el) {
          var bad = fieldError(el);
          setLeadError(f, el.name, bad ? (LEAD_MSGS[el.name] || 'Required.') : '');
          if (bad && ok) { el.focus(); ok = false; }
        });
        if (ok) show(idx + 1, true);
      });
    });

    $$('[data-step-back]', f).forEach(function (btn) {
      btn.addEventListener('click', function () { show(idx - 1, true); });
    });

    show(0, false);
  }

  function leadForms() {
    $$('form[data-lead]').forEach(leadForm);
    $$('form.form--steps').forEach(stepForm);
    prefillLocation();
  }

  /* ---------------------------------------------------------
     12b. Pre-fill "Where are you located?" from the visitor's IP.
     Pure convenience — best-effort, silent on failure, never blocks
     the field or the form. The visitor can always overwrite it.
     --------------------------------------------------------- */
  function prefillLocation() {
    var fields = $$('input[name="location"]').filter(function (el) { return !el.value; });
    if (!fields.length) return;
    fetch('https://ipapi.co/json/')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.city || d.error) return;
        var loc = d.region_code ? d.city + ', ' + d.region_code : d.city;
        fields.forEach(function (el) { if (!el.value) el.value = loc; });
      })
      .catch(function () { /* offline, blocked, or rate-limited — field just stays blank */ });
  }

  /* ---------------------------------------------------------
     12b. Rotating word ("…make you feel empowered.")
     --------------------------------------------------------- */
  function rotator() {
    $$('[data-rotate]').forEach(function (el) {
      var words = el.dataset.rotate.split('|');
      if (words.length < 2 || reduced) return;
      var i = 0;
      setInterval(function () {
        el.classList.add('is-out');
        setTimeout(function () {
          i = (i + 1) % words.length;
          el.textContent = words[i];
          el.classList.remove('is-out');
        }, 380);
      }, 2600);
    });
  }

  /* ---------------------------------------------------------
     13. Active nav link while scrolling
     --------------------------------------------------------- */
  function activeLink() {
    var sections = $$('main section[id]');
    var links = {};
    // nav links are absolute ("/#approach"); only same-page anchors take part
    $$('.nav__list a').forEach(function (a) {
      if (a.hash && a.pathname === window.location.pathname) links[a.hash] = a;
    });
    if (!sections.length || !('IntersectionObserver' in window)) return;

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var a = links['#' + e.target.id];
        if (!a) return;
        if (e.isIntersecting) {
          Object.keys(links).forEach(function (k) { links[k].style.color = ''; });
          a.style.color = 'var(--green)';
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });

    sections.forEach(function (s) { io.observe(s); });
  }

  /* ---------------------------------------------------------
     14. Misc: image fallback, back to top, year
     --------------------------------------------------------- */
  function misc() {
    $$('img').forEach(function (img) {
      img.addEventListener('error', function () {
        img.classList.add('img-fallback');
        img.removeAttribute('src');
      });
    });

    var top = $('#toTop');
    if (top) {
      top.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });
      });
    }

    var year = $('#year');
    if (year) year.textContent = new Date().getFullYear();

    var hero = $('.hero');
    if (hero) requestAnimationFrame(function () { hero.classList.add('is-ready'); });
  }

  /* ---------------------------------------------------------
     15. Opening modal (open / close; the form itself is a lead form)
     --------------------------------------------------------- */
  function gate() {
    var g = $('#gate');
    if (!g) return;
    /* inside a calculator embed iframe, never auto-open or mark seen */
    var EMBED = new URLSearchParams(location.search).get('embed') === '1';

    var f = $('#gateForm', g);
    var closing;

    function open() {
      g.hidden = false;
      document.body.classList.add('gate-open');
      requestAnimationFrame(function () {
        g.classList.add('is-open');
        var first = f ? $('input, select', f) : null;
        if (first && window.innerWidth > 620) {
          setTimeout(function () { first.focus({ preventScroll: true }); }, 620);
        }
      });
      document.addEventListener('keydown', onKey);
    }

    function close() {
      if (closing) return;
      closing = true;
      g.classList.remove('is-open');
      document.removeEventListener('keydown', onKey);
      document.body.classList.remove('gate-open');
      setTimeout(function () { g.hidden = true; }, reduced ? 0 : 600);
    }

    function onKey(e) {
      if (e.key === 'Escape') close();
    }

    $$('[data-gate-close]', g).forEach(function (el) {
      el.addEventListener('click', close);
      /* iOS Safari can swallow the synthesized click on backdrop-filtered
         overlays; close on touchend too (close() is idempotent). */
      el.addEventListener('touchend', function (e) { e.preventDefault(); close(); });
    });

    /* Tap anywhere outside the panel closes (scrim or container padding). */
    g.addEventListener('pointerdown', function (e) {
      if (!e.target.closest('.gate__panel')) close();
    });

    /* "Talk to an advisor" / header CTAs open the popup instead of navigating
       (blog popup behavior: a[href="#advisor-contact"] interception). */
    document.addEventListener('click', function (e) {
      var t = e.target.closest && e.target.closest('[data-gate-open]');
      if (t) {
        e.preventDefault();
        open();
      }
    });

    /* Auto-open once per visitor (localStorage), matching the blog popup:
       fire when the visitor scrolls halfway, or after 22s, whichever first. */
    var SEEN_KEY = 'vz_gate_seen_v1';
    function hasSeen() { try { return !!localStorage.getItem(SEEN_KEY); } catch (e) { return true; } }
    function markSeen() { try { localStorage.setItem(SEEN_KEY, '1'); } catch (e) {} }
    if (!EMBED && !hasSeen()) {
      var fired = false;
      function fire() {
        if (fired) return;
        fired = true;
        markSeen();
        open();
      }
      var timer = setTimeout(fire, reduced ? 4000 : 22000);
      function onScroll() {
        var h = document.documentElement;
        var max = h.scrollHeight - h.clientHeight;
        if (max > 0 && h.scrollTop / max >= 0.5) {
          clearTimeout(timer);
          window.removeEventListener('scroll', onScroll);
          fire();
        }
      }
      window.addEventListener('scroll', onScroll, { passive: true });
    }
  }

  /* ---------------------------------------------------------
     16. Advisor Growth & ROI Calculator (advisors.html)
     --------------------------------------------------------- */
  function advisorRoiCalc() {
    var root = $('#advisorCalc');
    if (!root) return;

    var sMatches   = $('#calcMatches', root);
    var sAum       = $('#calcAum', root);
    var sCloseRate = $('#calcCloseRate', root);
    var sFee       = $('#calcFee', root);

    var vMatches   = $('#valMatches', root);
    var vAum       = $('#valAum', root);
    var vCloseRate = $('#valCloseRate', root);
    var vFee       = $('#valFee', root);

    var oAum       = $('#resAum', root);
    var oRevenue   = $('#resRevenue', root);
    var oEquity    = $('#resEquity', root);

    function fmtMoney(n) {
      if (n >= 1e9) return '$' + (n / 1e9).toFixed(2) + 'B';
      if (n >= 1e6) return '$' + (n / 1e6).toFixed(2) + 'M';
      if (n >= 1e3) return '$' + Math.round(n / 1e3).toLocaleString('en-US') + 'K';
      return '$' + Math.round(n).toLocaleString('en-US');
    }

    function update() {
      var matches   = parseInt(sMatches.value, 10);
      var aum       = parseFloat(sAum.value);
      var closeRate = parseFloat(sCloseRate.value) / 100;
      var fee       = parseFloat(sFee.value) / 100;

      vMatches.textContent   = matches + ' / mo';
      vAum.textContent       = fmtMoney(aum);
      vCloseRate.textContent = (closeRate * 100).toFixed(0) + '%';
      vFee.textContent       = (fee * 100).toFixed(2) + '%';

      var annualClients = matches * 12 * closeRate;
      var annualNewAum  = annualClients * aum;
      var annualRev     = annualNewAum * fee;
      var enterpriseVal = annualRev * 2.8;

      oAum.innerHTML     = fmtMoney(annualNewAum);
      oRevenue.innerHTML = '$' + Math.round(annualRev).toLocaleString('en-US') + ' <em>/ yr</em>';
      oEquity.innerHTML  = fmtMoney(enterpriseVal);
    }

    [sMatches, sAum, sCloseRate, sFee].forEach(function (slider) {
      if (slider) slider.addEventListener('input', update);
    });

    update();
  }

  /* ---------------------------------------------------------
     16b. Calculator embed mode: ?embed=1 strips chrome inside the
     iframe and posts height to the parent; parent pages resize
     their calculator iframes on message.
     --------------------------------------------------------- */
  function calcEmbed() {
    if (new URLSearchParams(location.search).get('embed') === '1') {
      document.body.classList.add('embed-mode');
      var post = function () {
        try { parent.postMessage({ vzCalcEmbedHeight: document.documentElement.scrollHeight }, location.origin); } catch (e) {}
      };
      window.addEventListener('load', function () { post(); setTimeout(post, 600); });
      document.addEventListener('input', function () { setTimeout(post, 80); });
    }
    window.addEventListener('message', function (e) {
      if (e.origin !== location.origin) return;
      var h = e.data && e.data.vzCalcEmbedHeight;
      if (!h) return;
      $$('iframe[data-calc-embed]').forEach(function (ifr) {
        if (ifr.contentWindow === e.source) {
          ifr.style.height = Math.min(h + 24, 2400) + 'px';
        }
      });
    });
  }

  /* ---------------------------------------------------------
     17. Advisor Pipeline Simulator (advisors.html)
     --------------------------------------------------------- */
  function advisorPipeline() {
    var box = $('#advisorPipeline');
    if (!box) return;

    var chips = $$('.pipe-chip', box);
    var rows  = $$('.pipe__row', box);

    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        chips.forEach(function (c) { c.classList.remove('is-active'); });
        chip.classList.add('is-active');
        var cat = chip.dataset.cat || 'all';

        rows.forEach(function (row) {
          var match = (cat === 'all') || (row.dataset.cat === cat);
          row.style.display = match ? 'flex' : 'none';
        });
      });
    });
  }

  /* ---------------------------------------------------------
     boot
     --------------------------------------------------------- */
  function init() {
    curtain();
    prepareHeadlines();
    reveals();
    header();
    nav();
    parallax();
    counters();
    accordion();
    advisors();
    services();
    magnetic();
    leadForms();
    fyaSource();
    rotator();
    gate();
    activeLink();
    calcEmbed();
    misc();
    advisorRoiCalc();
    advisorPipeline();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
