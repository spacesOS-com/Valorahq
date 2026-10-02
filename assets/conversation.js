/* Client-only concierge shell. The endpoint is set at deployment after Sam's
 * contract, never guessed here. No request is sent when the endpoint is unset. */
(function () {
  'use strict';
  var host = document.getElementById('valora-conversation');
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
  if (endpointURL.pathname !== '/api/valora/conversation') return;
  var config = window.ValoraConversationConfig;
  if (!config || config.approved !== true || typeof config.version !== 'string' || !Array.isArray(config.pages) || !Array.isArray(config.sourceURLs)) return;
  var pageContext = config.pages.find(function (p) { return p.path === path; });
  if (config.noticeApproved !== true || config.collectionApproved !== true || typeof config.scope !== 'string' || !config.scope.trim() || typeof config.privacyWarning !== 'string' || !config.privacyWarning.trim()) return;
  if (!pageContext) return; // Only surfaces with reviewed answers can enable chat.
  var activePageContext = pageContext;
  var stateToken = null;
  var sourceAllowlist = new Set(config.sourceURLs);
  var activeController = null;
  var generation = 0;
  var results = document.getElementById('concierge-results');
  var isHome = path === '/concierge/';
  var busy = false;
  var exchanges = 0;
  var failedLine = null;
  var wrap = document.createElement('section');
  wrap.id = 'valora-floating-conversation';
  wrap.className = 'valora-concierge valora-conversation-dock';
  if (path === '/') wrap.classList.add('on-root');
  wrap.setAttribute('aria-label', 'Valora conversation');
  wrap.classList.add('ph-no-capture'); wrap.setAttribute('data-ph-no-capture', 'true');
  var title = document.createElement('h2');
  title.textContent = 'Valora conversation'; title.tabIndex = -1;
  var chat = document.createElement('div');
  chat.className = 'valora-concierge__chat';
  chat.tabIndex = 0; chat.setAttribute('aria-label', 'Guide finder conversation, scroll to read resources');
  chat.setAttribute('role', 'log');
  chat.setAttribute('aria-live', 'polite');
  var form = document.createElement('form');
  form.className = 'valora-concierge__form';
  var input = document.createElement('input');
  input.classList.add('ph-no-capture'); input.setAttribute('autocomplete', 'off');
  input.type = 'text'; input.maxLength = 1000; input.required = true;
  input.setAttribute('aria-label', 'Chat with Valora about this page');
  input.placeholder = 'Chat with Valora...';
  var send = document.createElement('button');
  send.type = 'submit'; send.textContent = 'Ask';
  var status = document.createElement('p');
  status.className = 'valora-concierge__status'; status.setAttribute('role', 'status');
  function valoraIcon() {
    var original = document.querySelector('.logo svg');
    if (!original) return document.createTextNode('');
    var icon = original.cloneNode(true); icon.removeAttribute('id'); icon.setAttribute('aria-hidden', 'true'); icon.setAttribute('focusable', 'false'); return icon;
  }
  function sendIcon(button) { button.replaceChildren(); button.setAttribute('aria-label', 'Send question'); var arrow = document.createElement('span'); arrow.textContent = '↑'; arrow.setAttribute('aria-hidden', 'true'); button.appendChild(arrow); }
  send.textContent = 'Ask'; send.setAttribute('aria-label','Ask Valora');
  var brandMark = document.createElement('span'); brandMark.className = 'valora-conversation__avatar'; brandMark.appendChild(valoraIcon()); brandMark.setAttribute('aria-hidden', 'true');
  var composer = document.createElement('div'); composer.className = 'valora-conversation__composer'; composer.appendChild(input); composer.appendChild(send); composer.prepend(brandMark); form.appendChild(composer);
  wrap.appendChild(title);  wrap.appendChild(chat);
  var greeting = document.createElement('p');
  greeting.className = 'valora-concierge__greeting';
  // Short topic names for the greeting; falls back to the page title.
  var topics = {
    '/financial-advisor-for-business-owners/': 'financial planning for business owners',
    '/financial-advisor-for-physicians/': 'financial planning for physicians',
    '/financial-advisor-for-dentists/': 'financial planning for dentists',
    '/financial-advisor-for-tech-employees/': 'financial planning for tech employees',
    '/calculators/roth-ira-growth/': 'Roth IRA growth',
    '/calculators/rsu-withholding-shortfall/': 'RSU withholding',
    '/calculators/pslf-scenario-explorer/': 'Public Service Loan Forgiveness',
    '/calculators/retirement/': 'retirement planning',
    '/calculators/equity-compensation/': 'equity compensation',
    '/calculators/banking/': 'banking and savings',
    '/calculators/taxes/': 'taxes',
    '/calculators/investing/': 'investing'
  };
  greeting.textContent = "Looks like you're exploring " + (topics[path] || pageContext.title || 'Valora') + ', feel free to ask me any questions.';
  chat.appendChild(greeting);
  wrap.appendChild(form); wrap.appendChild(status);
  var faqPopup = document.createElement('div'); faqPopup.className = 'valora-conversation__faq valora-concierge__choices'; faqPopup.hidden = true;
  faqPopup.setAttribute('aria-label', 'Reviewed questions about this page');
  function refreshFAQs() { faqPopup.replaceChildren(); activePageContext.questions.slice(0, 3).forEach(function(label) { var b = document.createElement('button'); b.type = 'button'; b.textContent = label; b.addEventListener('click', function() { faqPopup.hidden = true; submitQuestion(label); }); faqPopup.appendChild(b); }); }
  refreshFAQs();
  form.before(faqPopup);
  // Suggestions: the page's three reviewed questions appear as bubbles above
  // the composer when the empty textbox is focused or clicked.
  function showSuggestions() { faqPopup.hidden = busy || input.value.trim().length > 0 || !faqPopup.childElementCount; }
  input.addEventListener('focus', function() { greeting.hidden = true; showSuggestions(); chat.querySelectorAll('.valora-conversation__initial-choices').forEach(function(g){g.hidden=true;}); });
  input.addEventListener('click', function() { greeting.hidden = true; showSuggestions(); });
  // Clicking away: suggestions go; the greeting returns only if nothing was started.
  document.addEventListener('pointerdown', function(e) { if (wrap.contains(e.target)) return; faqPopup.hidden = true; if (chat.hidden && !input.value.trim()) greeting.hidden = false; });
  input.addEventListener('input', showSuggestions);
  function showInitialChoices() {
    if (!pageContext || !Array.isArray(pageContext.questions)) return;
    var group = document.createElement('div'); group.className = 'valora-concierge__choices valora-conversation__initial-choices ph-no-capture'; group.hidden = true;
    pageContext.questions.slice(0, 3).forEach(function (label) {
      var b = document.createElement('button'); b.type = 'button'; b.textContent = label;
      b.addEventListener('click', function () { submitQuestion(label); }); group.appendChild(b);
    }); chat.appendChild(group);
  }
  function clearSession() {
    document.body.removeAttribute('data-valora-conversation-open');
    generation++; if (activeController) activeController.abort(); activeController = null;
    greeting.hidden = false; stateToken = null; exchanges = 0; failedLine = null; busy = false; activePageContext = pageContext; refreshFAQs(); faqPopup.hidden = true;
    wrap.classList.remove('is-side'); title.textContent = pageContext ? pageContext.title : 'Valora'; chat.replaceChildren(greeting); showInitialChoices();
    if (typeof dockInput !== 'undefined' && dockInput) dockInput.value = '';
    input.value = ''; input.disabled = false; send.disabled = false; status.textContent = '';
  }
  showInitialChoices();
  var collapsedDock = null;
  var toggle = null;
  // One floating composer across reviewed pages. No separate collapsed input.
  wrap.classList.add('is-open','valora-floating-v9'); document.body.appendChild(wrap); wrap.insertBefore(greeting,form);
  // Keep page content clear of the fixed dock: an inert spacer at the end of
  // the body grows with the dock, so every element can scroll fully above it.
  var spacer = document.createElement('div');
  spacer.className = 'valora-floating-v9-spacer';
  spacer.setAttribute('aria-hidden', 'true');
  document.body.appendChild(spacer);
  function syncSpacer() { spacer.style.height = Math.ceil(wrap.getBoundingClientRect().height + 24) + 'px'; }
  if (typeof ResizeObserver === 'function') new ResizeObserver(syncSpacer).observe(wrap);
  window.addEventListener('resize', syncSpacer);
  syncSpacer();
  // Virtual keyboard: pages should use interactive-widget=resizes-content so
  // the layout viewport shrinks. Fallback: when the visual viewport shrinks
  // without the layout viewport, lift the dock by the occluded strip.
  function syncKeyboard() {
    if (!window.visualViewport) return;
    var occluded = window.innerHeight - window.visualViewport.height - window.visualViewport.offsetTop;
    wrap.style.bottom = occluded > 120 ? Math.ceil(occluded) + 'px' : '';
  }
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', syncKeyboard);
    window.visualViewport.addEventListener('scroll', syncKeyboard);
  }
  title.hidden = true; chat.hidden = true; faqPopup.hidden = true;
  function closeConversation(){clearSession();wrap.insertBefore(greeting,form);chat.hidden=true;title.hidden=true;syncSpacer();input.focus({preventScroll:true});}
  form.addEventListener('submit',function(){if(input.value.trim()){greeting.hidden=true;chat.hidden=false;syncSpacer();}});
  document.addEventListener('keydown',function(event){if(event.key==='Escape'&&!chat.hidden)closeConversation();});
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
    items.slice(0, 2).forEach(function (item) {
      if (!item || typeof item.title !== 'string' || typeof item.url !== 'string') return;
      // Server catalog URLs may be root-relative or canonical absolute.
      // Never follow a different origin, credentials, or a normalized URL that
      // hides traversal, encodings, query strings or fragments.
      if (item.url.includes('\\') || item.url.startsWith('//')) return;
      var relative = item.url.startsWith('/');
      if (!relative && !item.url.startsWith('https://')) return;
      var url;
      try { url = new URL(item.url, location.origin); } catch (_) { return; }
      var approvedPath = kind === 'Calculators to explore' ? /^\/calculators\/[a-z0-9-]+\/$/.test(url.pathname) :
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
  function parseResponse(data) {
    if (!data || !['answer','choices','refusal','unsupported','reset'].includes(data.kind) || typeof data.message !== 'string' || data.message.length > 2000 || !Array.isArray(data.sources) || data.sources.length > 4 || !Array.isArray(data.resources) || data.resources.length > 4 || !Array.isArray(data.choices) || data.choices.length > 3 || !(data.stateToken === null || typeof data.stateToken === 'string' && data.stateToken.length <= 4096) || !data.context || data.context.packVersion !== config.version) throw new Error('Invalid response');
    data.sources.forEach(function (s) { if (!s || typeof s.label !== 'string' || !sourceAllowlist.has(s.url)) throw new Error('Invalid source'); });
    data.resources.forEach(function (r) { if (!r || !Array.isArray(config.resources) || !config.resources.some(function (allowed) { return allowed.id === r.id && allowed.url === r.url && allowed.title === r.title; }) || typeof r.title !== 'string' || typeof r.url !== 'string' || !/^\/(?:financial-advisor-for-(?:business-owners|physicians|tech-employees|dentists)|insights\/[a-z0-9-]+|calculators\/[a-z0-9-]+)\/$/.test(r.url)) throw new Error('Invalid resource'); });
    data.choices.forEach(function (c) { if (!c || typeof c.label !== 'string' || c.label.length > 250 || typeof c.optionId !== 'string' || !/^[a-z0-9][a-z0-9._-]{0,119}$/.test(c.optionId)) throw new Error('Invalid choice'); });
    return data;
  }
  function renderResponse(data) {
    if (data.kind === 'reset') { stateToken = null; chat.replaceChildren(greeting); }
    else if (data.stateToken !== null) stateToken = data.stateToken;
    var namedPage = config.pages.find(function (p) { return p.pageId === data.context.pageId; });
    if (namedPage) { title.textContent = namedPage.title; activePageContext = namedPage; refreshFAQs(); }
    line(data.message, 'valora-concierge__answer');
    var links = document.createElement('div');
    data.sources.concat(data.resources).forEach(function (item) {
      var row = document.createElement('p'), a = document.createElement('a');
      a.textContent = item.label || item.title; a.href = item.url; a.rel = 'noopener noreferrer'; row.appendChild(a); links.appendChild(row);
    }); chat.appendChild(links);
    var group = document.createElement('div'); group.className = 'valora-concierge__choices ph-no-capture';
    data.choices.forEach(function (choice) {
      var b = document.createElement('button'); b.type = 'button'; b.textContent = choice.label;
      b.addEventListener('click', function () {
        // Explicit reset clears state. Restart choices must be asked as reviewed labels.
        if (data.kind === 'reset') submitQuestion(choice.label);
        else submitTurn({optionId: choice.optionId}, choice.label);
      }); group.appendChild(b);
    }); chat.appendChild(group); chat.scrollTop = chat.scrollHeight;
  }
  function submitQuestion(value) { var question = value.trim(); if (question) return submitTurn({question: question}, question); }
  async function submitTurn(selection, label) {
    if (busy) return;
    greeting.hidden = true; faqPopup.hidden = true; busy = true; send.disabled = true; input.disabled = true;
    var originalInput = input.value, currentGeneration = generation;
    status.textContent = 'Finding resources...';
    var turnLine = line(label, 'valora-concierge__question');
    var controller = new AbortController(); activeController = controller;
    var timeout = setTimeout(function () { controller.abort(); }, 20000);
    try {
      var body = Object.assign({pagePath: location.pathname}, selection);
      if (stateToken) body.stateToken = stateToken;
      var response = await fetch(endpointURL.href, {method:'POST',mode:'cors',credentials:'omit',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal});
      if (!response.ok) {
        if (response.status === 429) { var retry = Number(response.headers.get('Retry-After')); if (Number.isFinite(retry) && retry > 0) status.textContent = 'Too many questions. Please wait ' + Math.min(Math.ceil(retry),3600) + ' seconds and try again.'; }
        throw new Error('Unavailable');
      }
      var data = parseResponse(await response.json()); if (generation !== currentGeneration) return;
      if (failedLine) { failedLine.remove(); failedLine = null; }
      chat.querySelectorAll('.valora-concierge__choices button').forEach(function (button) { button.disabled = true; });
      if (data.kind === 'refusal') turnLine.remove(); // Do not echo rejected personal/private input.
      renderResponse(data); input.value = ''; status.textContent = ''; exchanges++;
      // Conversation stays docked bottom-center, including after follow-ups.
    } catch (_) {
      if (generation !== currentGeneration) return;
      turnLine.remove(); input.value = selection.question || originalInput;
      if (failedLine) failedLine.remove(); failedLine = line(config.messages.unavailable, 'valora-concierge__answer');
      if (status.textContent === 'Finding resources...') status.textContent = '';
    } finally {
      clearTimeout(timeout);
      if (generation === currentGeneration) { activeController = null; busy = false; send.disabled = false; input.disabled = false; input.focus(); faqPopup.hidden = true; }
    }
  }
  form.addEventListener('submit', function (event) { event.preventDefault(); submitQuestion(input.value); });
  window.addEventListener('pagehide', clearSession);
})();
