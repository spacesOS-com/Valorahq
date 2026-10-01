/* Client-only concierge shell. The endpoint is set at deployment after Sam's
 * contract, never guessed here. No request is sent when the endpoint is unset. */
(function () {
  'use strict';
  var host = document.getElementById('valora-concierge');
  if (!host) return;
  var path = location.pathname;
  // The entry point is available on every public site page. The backend
  // resolves pagePath against its reviewed snapshot; unknown paths are generic.
  if (!/^\/(?:[a-z0-9&-]+\/)*$/.test(path) || path.startsWith('/admin/') || new URLSearchParams(location.search).get('embed') === '1') return;
  // Deliberate release gate. Set only after backend, eligibility and QA gates.
  var endpoint = host.getAttribute('data-endpoint');
  if (!endpoint) return;
  var endpointURL;
  try { endpointURL = new URL(endpoint); } catch (_) { return; }
  var dev = location.hostname === 'localhost' && endpointURL.hostname === 'localhost' && endpointURL.protocol === 'http:';
  if (!dev && (endpointURL.protocol !== 'https:' || endpointURL.hostname !== 'api.valorahq.com')) return;
  if (endpointURL.username || endpointURL.password || endpointURL.search || endpointURL.hash) return;
  if (endpointURL.pathname !== '/api/valora/concierge') return;
  var results = document.getElementById('concierge-results');
  var isHome = path === '/concierge/';
  var history = [];
  var busy = false;
  var exchanges = 0;
  var failedLine = null;
  var wrap = document.createElement('section');
  wrap.className = 'valora-concierge';
  if (path === '/') wrap.classList.add('on-root');
  wrap.setAttribute('aria-label', 'Valora conversation');
  var title = document.createElement('h2');
  title.textContent = 'Valora';
  var note = document.createElement('p');
  note.className = 'valora-concierge__note';
  note.textContent = 'This conversation uses AI. I can explain general topics and help you explore the site, but I cannot give personal financial, tax, or legal advice or book an appointment.';
  var chat = document.createElement('div');
  chat.className = 'valora-concierge__chat';
  chat.setAttribute('role', 'log');
  chat.setAttribute('aria-live', 'polite');
  var form = document.createElement('form');
  form.className = 'valora-concierge__form';
  var input = document.createElement('input');
  input.type = 'text'; input.maxLength = 1000; input.required = true;
  input.setAttribute('aria-label', 'Ask Valora a question');
  input.placeholder = isHome ? 'What topic or guide are you looking for?' : 'What would you like to know about this page?';
  var send = document.createElement('button');
  send.type = 'submit'; send.textContent = 'Ask';
  var intake = document.createElement('a');
  intake.href = '/find-your-advisor/'; intake.textContent = 'Want a person to review your request? Send it to us';
  var status = document.createElement('p');
  status.className = 'valora-concierge__status'; status.setAttribute('role', 'status');
  form.appendChild(input); form.appendChild(send);
  wrap.appendChild(title); wrap.appendChild(note); wrap.appendChild(chat);
  var greeting = document.createElement('p');
  greeting.className = 'valora-concierge__greeting';
  greeting.textContent = isHome ?
    "Hi, I'm Valora. Ask about a general financial topic or find a guide on this site." :
    "Hi, I'm Valora. Ask about this page or find a related guide.";
  chat.appendChild(greeting);
  var privacyNotice = document.createElement('p');
  privacyNotice.className = 'valora-concierge__note';
  privacyNotice.textContent = 'Do not enter account numbers, passwords, Social Security numbers or other sensitive personal or financial information. ';
  var privacyLink = document.createElement('a'); privacyLink.href = '/privacy/'; privacyLink.textContent = 'Privacy Policy';
  privacyNotice.appendChild(privacyLink);
  wrap.appendChild(privacyNotice); wrap.appendChild(form); wrap.appendChild(status); wrap.appendChild(intake);
  var toggle = null;
  if (isHome && results) {
    var pageHeading = document.querySelector('.concierge-home h1');
    if (pageHeading) pageHeading.textContent = 'Talk with Valora.';
    var intro = document.querySelector('.concierge-home h1 + p');
    if (intro) intro.textContent = 'Tell me what you are trying to figure out. I can explain general topics and help you explore Valora, but I cannot give personal financial, tax, or legal advice.';
    results.appendChild(wrap);
    // Show AI/scope/privacy notices and first input together before any send.

  }
  else {
    toggle = document.createElement('button');
    toggle.type = 'button'; toggle.className = 'valora-concierge__toggle';
    if (path === '/') toggle.classList.add('on-root');
    toggle.textContent = 'Ask Valora'; toggle.setAttribute('aria-expanded', 'false');
    toggle.addEventListener('click', function () {
      var open = !wrap.classList.contains('is-open');
      wrap.classList.toggle('is-open', open); toggle.setAttribute('aria-expanded', String(open));
      if (open) input.focus();
    });
    document.body.appendChild(toggle); document.body.appendChild(wrap);
  }
  host.hidden = false;

  function line(text, css) {
    var p = document.createElement('p'); p.className = css; p.textContent = text;
    chat.appendChild(p); chat.scrollTop = chat.scrollHeight; return p;
  }
  function resources(items, kind) {
    if (!Array.isArray(items) || !items.length) return;
    var section = document.createElement('section');
    var heading = document.createElement('h3'); heading.textContent = kind; section.appendChild(heading);
    var list = document.createElement('ul');
    items.slice(0, kind === 'Advisor profiles to review' ? 3 : 2).forEach(function (item) {
      if (!item || typeof item.title !== 'string' || typeof item.url !== 'string') return;
      // Server catalog URLs may be root-relative or canonical absolute.
      // Never follow a different origin, credentials, or a normalized URL that
      // hides traversal, encodings, query strings or fragments.
      if (item.url.includes('\\') || item.url.startsWith('//')) return;
      var relative = item.url.startsWith('/');
      if (!relative && !item.url.startsWith('https://')) return;
      var url;
      try { url = new URL(item.url, location.origin); } catch (_) { return; }
      var approvedPath = kind === 'Advisor profiles to review' ? /^\/advisors\/[a-z0-9-]+\/$/.test(url.pathname) :
        kind === 'Calculators to explore' ? /^\/calculators\/[a-z0-9-]+\/$/.test(url.pathname) :
        (/^\/insights\/[a-z0-9-]+\/$/.test(url.pathname) ||
         /^\/financial-advisor-for-(business-owners|physicians|tech-employees|dentists)\/$/.test(url.pathname));
      if ((url.origin !== location.origin && url.origin !== 'https://www.valorahq.com') || url.username || url.password ||
          url.search || url.hash ||
          item.url !== (relative ? url.pathname : url.href) || !approvedPath) return;
      var li = document.createElement('li'); var a = document.createElement('a');
      a.href = url.pathname; a.textContent = item.title.slice(0, 120); li.appendChild(a); list.appendChild(li);
    });
    section.appendChild(list); chat.appendChild(section);
  }
  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    var question = input.value.trim(); if (!question || busy) return;
    busy = true; send.disabled = true; input.disabled = true;
    status.textContent = 'Thinking...';
    var lastQuestion = document.createElement('p'); lastQuestion.className = 'valora-concierge__question';
    lastQuestion.textContent = question; chat.appendChild(lastQuestion); chat.scrollTop = chat.scrollHeight;
    var controller = new AbortController();
    var timeout = setTimeout(function () { controller.abort(); }, 20000);
    try {
      var response = await fetch(endpointURL.href, {
        method: 'POST', mode: 'cors', credentials: 'omit',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question, pagePath: location.pathname, history: history.slice(-4) }),
        signal: controller.signal
      });
      if (!response.ok) {
        if (response.status === 429) {
          var retry = Number(response.headers.get('Retry-After'));
          if (Number.isFinite(retry) && retry > 0) {
            status.textContent = 'Too many questions. Please wait ' + Math.min(Math.ceil(retry), 3600) + ' seconds and try again.';
          }
        }
        throw new Error('Service unavailable');
      }
      var data = await response.json();
      if (!data || typeof data.answer !== 'string' || !data.answer.trim()) throw new Error('Empty answer');
      if (failedLine) { failedLine.remove(); failedLine = null; }
      line(data.answer.slice(0, 2000), 'valora-concierge__answer');
      // Advisor-profile display is held while the public directory is disabled.
      resources(data.calculators, 'Calculators to explore');
      resources(data.articles, 'Guides and articles');
      history.push({ question: question, answer: data.answer.slice(0, 500) });
      exchanges++;
      if (toggle && exchanges >= 2 && !wrap.classList.contains('is-side')) {
        wrap.classList.add('is-side');
        toggle.textContent = 'Ask Valora';
      }
      if (history.length > 4) history = history.slice(-4);
      input.value = '';
      status.textContent = data.followUp ? String(data.followUp).slice(0, 200) : '';
    } catch (_) {
      lastQuestion.remove();
      input.value = question;
      if (failedLine) failedLine.remove();
      failedLine = line('I can’t answer right now. Your question is still here. Try again, or send us a request for a person to review.', 'valora-concierge__answer');
      if (!status.textContent || status.textContent === 'Thinking...') status.textContent = 'I’m unavailable right now.';
    } finally {
      clearTimeout(timeout); busy = false; send.disabled = false; input.disabled = false; input.focus();
    }
  });
})();
