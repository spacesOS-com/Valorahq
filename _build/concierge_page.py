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
      <a class="concierge-inline-card reveal" href="/calculators/{calc['slug']}/" style="margin-top:16px;">
        <h4>{escape(calc['title'])}</h4>
        <p>{escape(calc['summary'])}</p>
      </a>

      <p class="eyebrow reveal" style="margin-top:36px;">Worth reading</p>
      <a class="concierge-inline-card reveal" href="/insights/{article['slug']}/" style="margin-top:16px;">
        <h4>{escape(article['title'])}</h4>
        <p>{escape(article['summary'])}</p>
      </a>
    </div>

    <p class="eyebrow reveal" style="margin-top:48px;">The same bar, aware of wherever you are</p>
    <p class="reveal" style="margin-top:12px; color:var(--ink-soft); max-width:56ch;">
      The floating bar isn't one generic box &mdash; its topic tag and placeholder would change to
      match whatever page it's on, so the question you ask is already in context.
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
    Looks like you're exploring retirement planning &mdash; want me to point you to a fitting advisor?
  </div>
  <div class="concierge-float__panel" id="concierge-panel-bottom" hidden></div>
  <div class="concierge-float__bar">
    <span class="concierge-float__avatar" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.4"/><path d="M7.5 12.5l3 3 6-6.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </span>
    <input type="text" id="concierge-input-bottom" placeholder="Chat with Valora&hellip;">
    <button type="button" class="concierge-float__chip" data-fill="Show me advisors who fit my situation">See my matches</button>
    <button type="button" class="concierge-float__chip" data-fill="I'd rather talk to a person directly">Talk to an advisor</button>
    <button type="button" class="concierge-float__mic" id="concierge-voice-toggle" aria-label="Voice input (concept only, not functional)" title="Concept only &mdash; not functional">
      <svg viewBox="0 0 24 24" fill="none"><path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z" stroke="currentColor" stroke-width="1.5"/><path d="M6 11a6 6 0 0 0 12 0M12 19v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
    </button>
    <button type="button" class="btn btn--dark concierge-float__submit" id="concierge-send-bottom">Ask</button>
  </div>
</div>

<button type="button" class="concierge-side-launcher" id="concierge-side-launcher" hidden>Ask Valora</button>
<div class="concierge-side-panel" id="concierge-side-panel">
  <div class="concierge-side-panel__head">
    <div class="concierge-side-panel__who">
      <span class="concierge-side-panel__mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.4"/><path d="M7.5 12.5l3 3 6-6.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </span>
      <div><strong>Valora Concierge</strong><span>Concept preview &mdash; not live AI</span></div>
    </div>
    <button type="button" class="concierge-side-panel__close" id="concierge-side-close" aria-label="Close">&times;</button>
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
    <a class="btn btn--outline" href="/find-your-advisor/">See my matches</a>
    <a class="btn btn--outline" href="/#contact" data-gate-open>Talk to a person</a>
  </div>

  <div class="concierge-side-panel__field">
    <input type="text" id="concierge-input-side" placeholder="Ask Valora a question">
    <button type="button" class="concierge-side-panel__send" id="concierge-send-side" aria-label="Send">&rarr;</button>
  </div>
  <p class="concierge-side-panel__fine">A design concept &mdash; nothing you type here is sent anywhere or recorded.</p>
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

  launcher.addEventListener('click', function () {{ sidePanel.classList.add('is-open'); }});
  closeBtn.addEventListener('click', function () {{ sidePanel.classList.remove('is-open'); }});
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
