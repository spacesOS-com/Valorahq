# -*- coding: utf-8 -*-
"""/concierge/ — a UI concept preview for a single-entry-point "front door":
one free-text question instead of a page-by-page funnel, that assembles
everything relevant (advisor matches, a calculator, an insight article) on
one screen instead of sending the visitor off to browse separate pages.

This is a static prototype, not a working product: the "conversation" and
the assembled results below are a scripted example, not live AI or real
matching logic. It exists to demonstrate the interaction model before any
decision is made to build the real thing (an actual LLM integration, real
matching logic, and real product/compliance thinking about an AI making
advisor recommendations in a financial-services context). The advisors
shown are real ADVISORS entries and the calculator/insight links are real,
existing pages — only the client's message is a scripted example, framed
the same way the existing "Michael Chen" portal mockup already is.
"""
from html import escape

from partials import page, head, BRAND, contact_section
from advisor_pages import ADVISORS
from calculator_pages import CALCULATORS
from insights_pages import ARTICLES

_CALC_SLUG = "retirement-savings-growth"
_ARTICLE_SLUG = "realistic-withdrawal-rate-today"

# Illustrative match: the 3 of the 4 real advisors tagged for retirement income
_MATCH_SLUGS = ["james-conole", "kevin-lum", "even-better-retirement"]


def _match_card(a):
    tags = "".join(f"<li>{escape(t)}</li>" for t in a["tags"])
    return f"""<a class="acard reveal" href="/advisors/{a['slug']}/">
        <div class="acard__top">
          <img src="{escape(a['photo'])}" alt="" width="52" height="52" loading="lazy">
          <div><h3>{escape(a['name'])}</h3><p>{escape(a['firm'])}</p></div>
        </div>
        <p class="acard__quote">{escape(a['quote'])}</p>
        <ul class="acard__tags">{tags}</ul>
      </a>"""


def _concierge_body():
    matches = [a for a in ADVISORS if a["slug"] in _MATCH_SLUGS]
    cards = "\n".join(_match_card(a) for a in matches)
    calc = next(c for c in CALCULATORS if c["slug"] == _CALC_SLUG)
    article = next(a for a in ARTICLES if a["slug"] == _ARTICLE_SLUG)
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:760px;">
    <p class="eyebrow reveal">Concept preview &mdash; not a live feature</p>
    <h1 class="display display--lg reveal">One question in.<br><em>Everything relevant, at once.</em></h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:56ch;">
      Today, finding an advisor, a relevant calculator, and relevant reading means visiting three
      separate pages. This concept collapses that into one: describe the situation once, in the
      floating bar at the bottom of the screen, and the site assembles what's relevant &mdash; on
      this screen, not across a click-through funnel. Everything below is scripted for this
      preview, not live.
    </p>

    <p class="reveal" style="margin-top:32px; color:var(--ink-soft); font-size:.82rem; max-width:56ch;">
      It starts as the compact floating bar. Ask a second question and it moves itself into the
      side panel, which has room to keep scrolling &mdash; a bottom bar doesn't. You can also force
      either layout below, to compare them directly.
    </p>
    <div class="concierge-layout-toggle reveal" style="margin-top:14px;">
      <button type="button" class="btn btn--outline is-active" data-layout-btn="bottom">Floating bar</button>
      <button type="button" class="btn btn--outline" data-layout-btn="side">Side panel</button>
    </div>

    <p class="reveal" style="margin-top:20px; font-size:.86rem; color:var(--gold);" id="concierge-hint">&darr; Try it &mdash; hit "Ask" twice to see it move to the side panel on its own.</p>

    <div id="concierge-results" hidden>
      <p class="eyebrow reveal" style="margin-top:12px;">Advisors who focus on this</p>
      <div class="match__grid reveal" style="margin-top:16px;">
        {cards}
      </div>

      <p class="eyebrow reveal" style="margin-top:36px;">A calculator that fits</p>
      <div class="concierge-inline-card reveal" style="margin-top:16px;">
        <h4>{escape(calc['title'])}</h4>
        <p>{escape(calc['summary'])}</p>
        <div style="margin-top:12px; display:flex; gap:10px;">
          <button type="button" class="btn btn--outline concierge-calc-trigger">Try it here</button>
          <a class="btn btn--outline" href="/calculators/{calc['slug']}/">Open full page</a>
        </div>
      </div>
      <div id="concierge-calc-embed" class="concierge-embed" hidden>
        <iframe src="/calculators/{calc['slug']}/" title="{escape(calc['title'])}" loading="lazy"></iframe>
        <p class="concierge-embed__note">This is the real, working calculator &mdash; pulled up inline instead of sending you to a separate page.</p>
      </div>

      <p class="eyebrow reveal" style="margin-top:36px;">Worth reading</p>
      <a class="concierge-inline-card reveal" href="/insights/{article['slug']}/" style="margin-top:16px;">
        <h4>{escape(article['title'])}</h4>
        <p>{escape(article['summary'])}</p>
      </a>

      <p class="eyebrow reveal" style="margin-top:36px;">Or talk to one of them directly</p>
      <button type="button" class="btn btn--dark reveal concierge-talk-trigger" style="margin-top:16px;">Talk to an advisor</button>
    </div>

    <p class="eyebrow reveal" style="margin-top:48px;">The same bar, aware of wherever you are</p>
    <p class="reveal" style="margin-top:12px; color:var(--ink-soft); max-width:56ch;">
      The floating bar isn't one generic box &mdash; whatever page it's on would load that page's own
      content into the conversation as context (this calculator's fields and result, this
      article's actual claims, this advisor's real profile), so it can answer specifically about
      what's already on screen, not generic advice.
    </p>
    <div class="concierge-variants reveal" style="margin-top:20px;">
      <div class="concierge-variant">
        <span class="concierge-variant__tag">On a calculator page</span>
        <p>&ldquo;Ask about this calculator&rdquo; &mdash; e.g. <em>&ldquo;What if I retire 3 years earlier?&rdquo;</em></p>
      </div>
      <div class="concierge-variant">
        <span class="concierge-variant__tag">On an insight article</span>
        <p>&ldquo;Ask about this article&rdquo; &mdash; e.g. <em>&ldquo;Does this apply if I have a pension too?&rdquo;</em></p>
      </div>
      <div class="concierge-variant">
        <span class="concierge-variant__tag">On an advisor's profile</span>
        <p>&ldquo;Ask James Conole a question&rdquo; &mdash; e.g. <em>&ldquo;Do you work with clients outside Texas?&rdquo;</em></p>
        <div class="concierge-variant__preview">
          <img src="/images/advisors/advisor-1.jpg" alt="James Conole, CFP&reg;" width="34" height="34">
          <span>Chat with James Conole&hellip;</span>
        </div>
      </div>
    </div>

    <div class="dir-note" style="margin-top:36px; margin-bottom:100px;">
      This is a design concept, not a working product. The floating entry bar, its topic tag, the
      chat response, and the act of assembling these specific results are all scripted for this one
      example &mdash; a real version needs an actual conversational AI integration and real matching
      logic across advisors, calculators, and articles, not something this preview does today.
    </div>
  </div>
</section>

<div class="concierge-float" id="concierge-float-bottom">
  <div class="concierge-float__greeting" id="concierge-greeting">
    Looks like you're exploring retirement planning &mdash; feel free to ask me any questions.
  </div>
  <div class="concierge-float__panel" id="concierge-panel-bottom" hidden></div>
  <div class="concierge-float__bar">
    <span class="concierge-float__avatar" aria-hidden="true">
      <svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="15" stroke="currentColor" stroke-width="1.4"/><path d="M6 20.5c4-9 6.5-9 10 0s6 9 10 0" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
    </span>
    <input type="text" id="concierge-input-bottom" placeholder="Chat with Valora&hellip;">
    <button type="button" class="concierge-float__chip concierge-talk-trigger">Talk to an advisor</button>
    <button type="button" class="btn btn--dark concierge-float__submit" id="concierge-send-bottom">Ask</button>
  </div>
</div>

<button type="button" class="concierge-side-launcher" id="concierge-side-launcher" hidden>Ask Valora</button>
<div class="concierge-side-panel" id="concierge-side-panel">
  <div class="concierge-side-panel__head">
    <div class="concierge-side-panel__who">
      <div><strong>Valora Concierge</strong><span>Concept preview &mdash; not live AI</span></div>
    </div>
    <div class="concierge-side-panel__head-actions">
      <button type="button" class="concierge-side-panel__minimize" id="concierge-side-minimize" aria-label="Minimize">&minus;</button>
      <button type="button" class="concierge-side-panel__close" id="concierge-side-close" aria-label="Close">&times;</button>
    </div>
  </div>

  <div class="concierge-side-panel__chat" id="concierge-panel-side">
    <div class="convert-mock__bubble convert-mock__bubble--us">Hi &mdash; tell me what's going on financially, and I'll point you to advisors and tools that fit.</div>
  </div>

  <div class="concierge-side-panel__suggestions" id="concierge-side-suggestions">
    <p>Ask me things like:</p>
    <button type="button" class="concierge-side-panel__chip">How do I find the right advisor for a business sale?</button>
    <button type="button" class="concierge-side-panel__chip">I have RSUs vesting this year &mdash; who handles that?</button>
    <button type="button" class="concierge-side-panel__chip">I'm 58, planning to retire in about 7 years, and I want a clear income plan for when I stop working.</button>
  </div>

  <div class="concierge-side-panel__actions">
    <button type="button" class="btn btn--outline concierge-talk-trigger">Talk to an advisor</button>
  </div>

  <div class="concierge-side-panel__field">
    <input type="text" id="concierge-input-side" placeholder="Ask Valora a question">
    <button type="button" class="concierge-side-panel__send" id="concierge-send-side" aria-label="Send">&rarr;</button>
  </div>
</div>

<script>
(function () {{
  var results = document.getElementById('concierge-results');
  var hint = document.getElementById('concierge-hint');
  var sent = false;

  function reveal() {{
    if (sent) return;
    sent = true;
    results.hidden = false;
    if (hint) hint.hidden = true;
    results.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }}

  function wire(suffix, onExpand, onAsk) {{
    var input = document.getElementById('concierge-input-' + suffix);
    var send = document.getElementById('concierge-send-' + suffix);
    var panel = document.getElementById('concierge-panel-' + suffix);
    var sendLabel = send.textContent;

    function bubble(text, who) {{
      var d = document.createElement('div');
      d.className = 'convert-mock__bubble convert-mock__bubble--' + who;
      d.textContent = text;
      panel.appendChild(d);
      panel.scrollTop = panel.scrollHeight;
    }}

    function ask(text) {{
      var val = (text || input.value || '').trim();
      if (!val) return;
      panel.hidden = false;
      if (onExpand) onExpand();
      input.value = val;
      bubble(val, 'them');
      input.disabled = true;
      send.textContent = '\\u2026';
      if (onAsk) onAsk();
      setTimeout(function () {{
        bubble("Got it \\u2014 retirement income planning, roughly a 7-year runway. Here's what's relevant:", 'us');
        send.textContent = sendLabel;
        input.disabled = false;
        input.value = '';
        reveal();
      }}, 700);
    }}

    send.addEventListener('click', function () {{ ask(); }});
    input.addEventListener('keydown', function (e) {{ if (e.key === 'Enter') ask(); }});
    return ask;
  }}

  // layout elements (declared first so the auto-migration below can use them)
  var bottomWidget = document.getElementById('concierge-float-bottom');
  var bottomPanel = document.getElementById('concierge-panel-bottom');
  var launcher = document.getElementById('concierge-side-launcher');
  var sidePanel = document.getElementById('concierge-side-panel');
  var sideChat = document.getElementById('concierge-panel-side');
  var closeBtn = document.getElementById('concierge-side-close');
  var buttons = document.querySelectorAll('[data-layout-btn]');
  var suggestions = document.getElementById('concierge-side-suggestions');
  var autoMode = true; // true until the visitor manually picks a layout

  function setActiveButton(mode) {{
    buttons.forEach(function (b) {{ b.classList.toggle('is-active', b.getAttribute('data-layout-btn') === mode); }});
  }}

  function migrateToSide() {{
    // conversation got longer than one exchange — move it into the side panel,
    // which has more room to keep scrolling than a bottom bar does
    while (bottomPanel.firstChild) {{ sideChat.appendChild(bottomPanel.firstChild); }}
    bottomWidget.style.display = 'none';
    launcher.hidden = true;
    sidePanel.classList.add('is-open');
    if (suggestions) suggestions.hidden = true;
    if (autoMode) setActiveButton('side');
  }}

  var greeting = document.getElementById('concierge-greeting');
  var bottomExchanges = 0;
  var askBottom = wire('bottom', function () {{
    bottomWidget.classList.add('is-expanded');
    if (greeting) greeting.hidden = true;
  }}, function () {{
    bottomExchanges++;
    if (bottomExchanges === 2) setTimeout(migrateToSide, 900);
  }});
  document.getElementById('concierge-input-bottom').addEventListener('focus', function () {{ if (greeting) greeting.hidden = true; }});
  document.querySelectorAll('#concierge-float-bottom .concierge-float__chip').forEach(function (chip) {{
    chip.addEventListener('click', function () {{ askBottom(chip.getAttribute('data-fill')); }});
  }});

  var askSide = wire('side', null, function () {{ if (suggestions) suggestions.hidden = true; }});
  document.querySelectorAll('.concierge-side-panel__chip').forEach(function (chip) {{
    chip.addEventListener('click', function () {{ askSide(chip.textContent); }});
  }});

  // manual layout toggle
  buttons.forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      autoMode = false;
      setActiveButton(btn.getAttribute('data-layout-btn'));
      var mode = btn.getAttribute('data-layout-btn');
      sidePanel.classList.remove('is-open');
      if (mode === 'side') {{
        bottomWidget.style.display = 'none';
        launcher.hidden = false;
      }} else {{
        bottomWidget.style.display = '';
        launcher.hidden = true;
      }}
    }});
  }});

  function collapseSide() {{
    sidePanel.classList.remove('is-open');
    launcher.hidden = false;
  }}
  launcher.addEventListener('click', function () {{ sidePanel.classList.add('is-open'); }});
  closeBtn.addEventListener('click', collapseSide);
  var minimizeSide = document.getElementById('concierge-side-minimize');
  if (minimizeSide) minimizeSide.addEventListener('click', collapseSide);

  // "try it here" — pull the real, working calculator inline instead of linking out
  var calcEmbed = document.getElementById('concierge-calc-embed');
  document.querySelectorAll('.concierge-calc-trigger').forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      calcEmbed.hidden = false;
      calcEmbed.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }});
  }});

  // "talk to an advisor" — sample calendar appears as a message in whichever
  // chat panel is currently active, not as a separate block on the page
  function calendarBubble() {{
    var d = document.createElement('div');
    d.className = 'convert-mock__bubble convert-mock__bubble--us concierge-calendar';
    d.innerHTML =
      '<p class="eyebrow">Sample availability &mdash; not a real booking</p>' +
      '<h4>Book a call with James Conole, CFP&reg;</h4>' +
      '<div class="concierge-calendar__grid">' +
        '<div class="concierge-calendar__day"><span>Tue, Oct 6</span>' +
          '<button type="button" class="concierge-calendar__slot">10:00 AM</button>' +
          '<button type="button" class="concierge-calendar__slot">2:30 PM</button></div>' +
        '<div class="concierge-calendar__day"><span>Wed, Oct 7</span>' +
          '<button type="button" class="concierge-calendar__slot">9:15 AM</button>' +
          '<button type="button" class="concierge-calendar__slot">4:00 PM</button></div>' +
        '<div class="concierge-calendar__day"><span>Thu, Oct 8</span>' +
          '<button type="button" class="concierge-calendar__slot">11:00 AM</button>' +
          '<button type="button" class="concierge-calendar__slot">1:00 PM</button></div>' +
      '</div>' +
      '<p class="concierge-calendar__confirm" hidden></p>';
    return d;
  }}

  function activeChatPanel() {{
    if (sidePanel.classList.contains('is-open')) return sideChat;
    bottomWidget.classList.add('is-expanded');
    if (greeting) greeting.hidden = true;
    if (minimizeBottom) minimizeBottom.hidden = false;
    bottomPanel.hidden = false;
    return bottomPanel;
  }}

  document.querySelectorAll('.concierge-talk-trigger').forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      results.hidden = false;
      var panel = activeChatPanel();
      var card = calendarBubble();
      panel.appendChild(card);
      panel.scrollTop = panel.scrollHeight;
      card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    }});
  }});

  // event delegation — calendar slots are added dynamically, so listen on body
  document.body.addEventListener('click', function (e) {{
    var slot = e.target.closest('.concierge-calendar__slot');
    if (!slot) return;
    var card = slot.closest('.concierge-calendar');
    card.querySelectorAll('.concierge-calendar__slot').forEach(function (s) {{ s.classList.remove('is-selected'); }});
    slot.classList.add('is-selected');
    var day = slot.closest('.concierge-calendar__day').querySelector('span').textContent;
    var confirmMsg = card.querySelector('.concierge-calendar__confirm');
    confirmMsg.hidden = false;
    confirmMsg.textContent = 'Selected ' + day + ' at ' + slot.textContent + ' \\u2014 sample only, nothing is actually booked in this preview.';
  }});
}})();
</script>

{contact_section()}
"""


def build_concierge_page(write_fn):
    html = page(
        head(f"AI Concierge Concept | {BRAND}",
             "A UI concept preview for an AI chat concierge that recommends advisors based on a natural conversation.",
             path="/concierge/",
             noindex=True),
        _concierge_body(),
    )
    write_fn("/concierge/", html)
