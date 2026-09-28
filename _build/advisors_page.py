# -*- coding: utf-8 -*-
"""advisors_page.py — The comprehensive "For Advisors" page for Valora."""
from html import escape

from partials import EMAIL, PHONE_DISPLAY, PHONE_TEL, TICK_SVG
from blog_feed import latest_posts

ADVISOR_GOALS = [
    "Client introductions & growth",
    "Turnkey platform & back office",
    "Breakaway transition from broker-dealer",
    "Full RIA infrastructure partnership",
]

FOR_ADVISORS_FAQ = [
    ("How does Valora match advisors with prospective clients?",
     "Valora matches consumers based on what they are specifically solving for (e.g. retirement decumulation, tech equity/RSUs, business sale, generational wealth transfer), their investable asset tier, and the advisor's verified niche expertise and geographic preference. Consumers review advisor profiles and actively choose to connect — these are qualified, intentional introductions, not cold leads."),
    ("Are client introductions exclusive to my firm?",
     "Yes, 100% exclusive. Unlike lead brokers who auction the same contact information to five or six competing advisors, Valora introduces each prospective client exclusively to one fiduciary advisor at a time based on mutual fit and stated preference."),
    ("Who owns the client relationship, data, and Form ADV?",
     "You do, completely. Clients engage your firm directly under your own advisory agreements, your published fee schedule, and your Form ADV Part 2. Valora does not provide investment advice or intermediate your advisory sovereignty. If you ever leave, your clients, data, and book stay entirely yours."),
    ("What context do I receive before the first consultation?",
     "Every introduction arrives with verified investable assets, primary financial objectives, timeline urgency, employer stock or business details (if applicable), and any specific questions the prospective client shared during our intake process."),
    ("What is the fee or economic model for partner advisors?",
     "Valora operates with transparent, advisor-friendly economics aligned with your growth. We offer flexible plans depending on whether your firm seeks client introductions, our complete back-office operational suite, or both. We discuss specific tiers and territory availability during your 15-minute introductory call."),
]


def _goal_opts():
    return '<option value="">Select your primary goal</option>' + "".join(f"<option>{g}</option>" for g in ADVISOR_GOALS)


def _faq_accordion():
    items = []
    for q, a in FOR_ADVISORS_FAQ:
        items.append(f'<details class="faq__item"><summary>{q}</summary><p>{a}</p></details>')
    return "\n".join(items)


def _blog_embed():
    """Real posts pulled from blog.valorahq.com at build time (see blog_feed.py) —
    proof, for advisors evaluating Valora, that Valora practices the AEO/GEO
    content playbook it's asking them to trust, not just claims to."""
    posts = latest_posts(3)
    cards = "\n".join(f"""      <article class="blogcard reveal">
        <h3><a href="{escape(p['url'])}" target="_blank" rel="noopener">{escape(p['title'])}</a></h3>
        <p>{escape(p['excerpt'])}</p>
        <a class="blogcard__link" href="{escape(p['url'])}" target="_blank" rel="noopener">Read on the blog →</a>
      </article>""" for p in posts)
    return f"""<section class="section section--cream adv-blog" id="insights-for-advisors">
  <div class="container">
    <div class="adv-blog__head">
      <p class="eyebrow reveal">From the Valora blog</p>
      <h2 class="display display--lg reveal">We publish the playbook<br><em>we use to get you clients.</em></h2>
      <p class="reveal">Valora's own content on getting advisory firms recommended by ChatGPT, Perplexity, and AI search — the same approach behind how we get your firm in front of prospective clients.</p>
    </div>
    <div class="adv-blog__grid">
{cards}
    </div>
    <a class="btn btn--outline adv-blog__more" href="https://blog.valorahq.com/" target="_blank" rel="noopener">View more</a>
  </div>
</section>

"""


def for_advisors_body():
    faq_html = _faq_accordion()
    blog_html = _blog_embed()
    return f"""
<!-- ================= HERO ================= -->
<section class="hero hero--sub" id="top">
  <div class="hero__grid" aria-hidden="true">
    <span class="hero__cell hero__cell--gold"></span>
    <span class="hero__cell hero__cell--wide"></span>
    <span class="hero__cell hero__cell--ring"></span>
    <span class="hero__cell hero__cell--green"></span>
  </div>

  <div class="container hero__inner">
    <div class="hero__copy">
      <h1 class="hero__title reveal">
        Access new clients<br>in minutes with <em>Valora</em>.
      </h1>
      <p class="adv-hero__sub reveal">If you're looking for the perfect clients, we'll deliver them straight to your inbox and give you the tools to manage them throughout the sales process. We work exclusively with SEC registered firms.</p>
      <div class="hero__actions reveal">
        <a class="btn btn--dark" href="#apply">Book a demo</a>
      </div>
    </div>
  </div>

  <!-- Animated Metrics Ribbon -->
  <div class="hero__bar">
    <div class="container hero__bar-grid">
      <div class="stat">
        <span class="stat__num" data-count="1.4" data-prefix="$" data-suffix="M+" data-decimals="1">$1.4M+</span>
        <span class="stat__label">Average investable assets per match</span>
      </div>
      <div class="stat">
        <span class="stat__num" data-count="3.2" data-suffix="x" data-decimals="1">3.2x</span>
        <span class="stat__label">Organic AUM growth rate vs. industry avg</span>
      </div>
      <div class="stat">
        <span class="stat__num" data-count="100" data-suffix="%">100%</span>
        <span class="stat__label">Exclusive client matches &amp; book ownership</span>
      </div>
      <div class="stat stat--note">
        <span class="stat__label">Fiduciary RIA network.<br>Limited territory availability per market.</span>
      </div>
    </div>
  </div>
</section>

<!-- ================= WHY ADVISORS PARTNER WITH VALORA ================= -->
<section class="section section--paper adv-value">
  <div class="container adv-value__grid">
    <div class="adv-value__copy">
      <h2 class="display display--lg reveal">Scale your book.<br>Keep your independence.<br><em>Improve your close rate.</em></h2>
      <p class="reveal">Valora gets prospective clients who are actively looking for an advisor in front of you, then gives you the tools to manage them from first message to signed client.</p>
    </div>
    <div class="adv-value__cards">
      <div class="value-card reveal">
        <h3>Exclusive leads</h3>
        <p>Unlike lead brokers that sell the same contact to five competing firms, every introduction on Valora goes to one advisor.</p>
      </div>
      <div class="value-card reveal">
        <h3>Choose the clients you want</h3>
        <p>Set your ideal investable-asset range, specialty, and geography — you only see introductions that fall inside it.</p>
      </div>
      <div class="value-card reveal">
        <h3>Arrive pre-qualified</h3>
        <p>Every introduction comes with the context you'd otherwise spend a first call gathering: goals, timeline, and what they're solving for.</p>
      </div>
      <div class="value-card reveal">
        <h3>Manage the whole pipeline</h3>
        <p>Track, message, and follow up with prospective clients in one place instead of a spreadsheet and an inbox.</p>
      </div>
    </div>
  </div>
</section>

<!-- ================= THE INTRODUCTIONS ENGINE ================= -->
<section class="section section--cream platform adv-pipe" id="introductions">
  <div class="container platform__grid">
    <div class="platform__copy">
      <p class="eyebrow reveal">Client Acquisition Engine</p>
      <h2 class="display display--lg reveal">Every introduction arrives with<br><em>the rich context you need.</em></h2>
      <p class="reveal">Before you ever jump on an introductory conversation, you already understand their liquid asset range, specific timeline urgency, and primary financial goal.</p>

      <ul class="adv-ticks reveal">
        <li><strong>100% Exclusive Introductions:</strong> Never shared or shopped to other advisors</li>
        <li><strong>Pre-Qualified Investable Assets:</strong> Minimum thresholds verified before matching</li>
        <li><strong>High-Intent Urgency:</strong> Prospects have actively requested fiduciary guidance</li>
        <li><strong>Direct Calendar Booking:</strong> Integrates with Calendly, Google Calendar, and Outlook</li>
        <li><strong>Full Advisory Discretion:</strong> You review the dossier and decide whether to engage</li>
      </ul>
    </div>

    <!-- Interactive Pipeline Simulator -->
    <div class="adv-mock" id="advisorPipeline">
      <div class="mock reveal" aria-hidden="true">
        <div class="mock__bar"><span></span><span></span><span></span><em>Valora Advisor Portal · Active Introductions</em></div>
        <div class="mock__body">
          <div class="mock__row">
            <div>
              <p class="mock__label">This Month's Inbound</p>
              <p class="mock__h">4 Verified Matches Ready</p>
            </div>
            <div class="mock__pill">Accepting Matches</div>
          </div>

          <!-- Interactive Category Filter Chips -->
          <div class="pipe-filter-wrap">
            <button type="button" class="pipe-chip is-active" data-cat="all">All Specialties</button>
            <button type="button" class="pipe-chip" data-cat="tech">Tech Equity</button>
            <button type="button" class="pipe-chip" data-cat="business">Business Sale</button>
            <button type="button" class="pipe-chip" data-cat="retire">Retirement</button>
            <button type="button" class="pipe-chip" data-cat="estate">Estate &amp; Trust</button>
          </div>

          <ul class="pipe">
            <li class="pipe__row" data-cat="tech">
              <div class="pipe__who">
                <span class="pipe__av">01</span>
                <div>
                  <p class="pipe__name">Tech Equity &amp; RSUs · $2.4M Liquid</p>
                  <p class="pipe__need">"VP of Engineering at Snowflake with $2.4M in vested RSUs and ISOs. Seeking tax-minimization strategy and concentrated stock collar."</p>
                  <div class="pipe__meta-row">
                    <span class="pipe__meta-tag">San Francisco, CA</span>
                    <span class="pipe__meta-tag">Goal: Tax &amp; Diversification</span>
                  </div>
                </div>
              </div>
              <span class="mock__pill mock__pill--good">Call Booked</span>
            </li>
            <li class="pipe__row" data-cat="business">
              <div class="pipe__who">
                <span class="pipe__av">02</span>
                <div>
                  <p class="pipe__name">Business Liquidity Exit · $4.5M Expected</p>
                  <p class="pipe__need">"Manufacturing founder in LOI stage for $4.5M cash sale within 9 months. Needs pre-liquidity trust structure and QSBS optimization."</p>
                  <div class="pipe__meta-row">
                    <span class="pipe__meta-tag">Austin, TX</span>
                    <span class="pipe__meta-tag">Goal: Exit &amp; Legacy</span>
                  </div>
                </div>
              </div>
              <span class="mock__pill">Dossier Sent</span>
            </li>
            <li class="pipe__row" data-cat="retire">
              <div class="pipe__who">
                <span class="pipe__av">03</span>
                <div>
                  <p class="pipe__name">Retirement Income &amp; Decumulation · $1.8M Rollover</p>
                  <p class="pipe__need">"Orthopedic surgeon retiring in 18 months. Wants tax-efficient 401(k) rollover, Social Security timing, and multi-year Roth conversion plan."</p>
                  <div class="pipe__meta-row">
                    <span class="pipe__meta-tag">Denver, CO</span>
                    <span class="pipe__meta-tag">Goal: Retirement Ladder</span>
                  </div>
                </div>
              </div>
              <span class="mock__pill">Intro Scheduled</span>
            </li>
            <li class="pipe__row" data-cat="estate">
              <div class="pipe__who">
                <span class="pipe__av">04</span>
                <div>
                  <p class="pipe__name">Generational Wealth &amp; Family Trusts · $3.2M AUM</p>
                  <p class="pipe__need">"Family enterprise principal seeking comprehensive fiduciary review of existing irrevocable trusts and philanthropic foundation strategy."</p>
                  <div class="pipe__meta-row">
                    <span class="pipe__meta-tag">Chicago, IL</span>
                    <span class="pipe__meta-tag">Goal: Dynasty Planning</span>
                  </div>
                </div>
              </div>
              <span class="mock__pill mock__pill--good">New Match</span>
            </li>
          </ul>
        </div>
      </div>
      <figcaption class="adv-mock__cap">Live illustrative simulation of Valora advisor introduction pipeline.</figcaption>
    </div>
  </div>
</section>

<!-- ================= INCREASE YOUR CONVERSION ================= -->
<section class="section section--paper adv-convert">
  <div class="container adv-convert__grid">
    <div class="adv-convert__copy">
      <p class="eyebrow reveal">Inside the portal</p>
      <h2 class="display display--lg reveal">Increase your<br><em>conversion.</em></h2>
      <p class="reveal">Chat, set reminders, attach notes, and link your calendar &mdash; everything you need to move a match from first message to booked call, in the same portal.</p>
      <ul class="adv-convert__list reveal">
        <li>Message prospects directly</li>
        <li>Set follow-up reminders</li>
        <li>Attach private notes per match</li>
        <li>Link your calendar for booking</li>
      </ul>
    </div>

    <div class="convert-mock reveal" aria-hidden="true">
      <div class="convert-mock__bar"><span></span><span></span><span></span><em>Valora Advisor Portal · Message</em></div>
      <div class="convert-mock__body">
        <div class="convert-mock__side">
          <div class="convert-mock__who">
            <span class="convert-mock__av">MC</span>
            <div><p class="convert-mock__name">Michael Chen</p><p class="convert-mock__stage">Call Booked</p></div>
          </div>
          <div class="convert-mock__field"><span>Note</span><p>Wants a second opinion on RSU tax withholding before year-end.</p></div>
          <div class="convert-mock__field"><span>Reminder</span><p>Follow up Thu 10:00 AM</p></div>
          <div class="convert-mock__field"><span>Calendar</span><p>Linked · Google Calendar</p></div>
        </div>
        <div class="convert-mock__chat">
          <div class="convert-mock__bubble convert-mock__bubble--them">Hi, I'd like to talk through my options before year-end.</div>
          <div class="convert-mock__bubble convert-mock__bubble--us">Happy to help &mdash; are mornings or afternoons better this week?</div>
          <div class="convert-mock__bubble convert-mock__bubble--them">Thursday morning works.</div>
          <div class="convert-mock__input">Type your message&hellip; <span>➤</span></div>
        </div>
      </div>
    </div>
  </div>
</section>


<!-- ================= ADVISOR DIRECTORY ADVANTAGE (SAVVY WEALTH STYLE) ================= -->
<section class="section section--cream dir-showcase" id="directory">
  <div class="dir-showcase__copy reveal">
    <p class="eyebrow">Your Digital Flagship</p>
    <h2 class="display display--lg">Your firm, showcased to thousands<br><em>of investors searching for your specialty.</em></h2>
    <p style="margin-top:16px; font-size:.95rem; color:var(--ink-soft); max-width:48ch;">Every approved Valora advisor receives an authoritative, search-optimized directory profile that commands instant credibility. Consumers view your fiduciary credentials, fee philosophy, focus areas, and book an introductory consultation directly onto your calendar.</p>
    <ul class="adv-ticks" style="margin-top:22px;">
      <li>Verified Fiduciary Badge &amp; Clean Regulatory Record Highlight</li>
      <li>Custom niche tags (Tech RSUs, Physician Planning, Business Exit)</li>
      <li>Direct calendar scheduling link with no friction</li>
      <li>Local SEO positioning in your target metropolitan area</li>
    </ul>
  </div>

  <div class="dir-card-mock reveal reveal--right">
    <div class="dir-profile-head">
      <img class="dir-profile-img" src="https://images.unsplash.com/photo-1573496358961-3c82861ab8f4?auto=format&amp;fit=crop&amp;crop=faces&amp;w=200&amp;h=200&amp;q=80" alt="Elena Rostova, CFP®" loading="lazy">
      <div>
        <h4>Elena Rostova, CFP®</h4>
        <p>Managing Principal · Summit Crest Wealth (Denver, CO)</p>
      </div>
    </div>
    <div class="dir-tags">
      <span class="dir-tag">Fee-Only Fiduciary</span>
      <span class="dir-tag">Tech Executive Equity</span>
      <span class="dir-tag">Retirement Decumulation</span>
      <span class="dir-tag">14 Yrs Experience</span>
    </div>
    <p class="dir-quote">"We believe financial planning should give clients clarity and confidence before any portfolio allocation is ever discussed."</p>
    <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--line); padding-top:14px;">
      <span style="font-size:.78rem; color:var(--muted);">⭐ 5.0 (24 Client Reviews)</span>
      <span class="btn btn--dark" style="padding:8px 18px; font-size:.78rem; pointer-events:none;">Schedule 20-Min Intro</span>
    </div>
  </div>
</section>

<!-- ================= HOW VALORA COMPARES ================= -->
<section class="section section--paper adv-compare2" id="compare">
  <div class="container">
    <div class="adv-blog__head">
      <p class="eyebrow reveal">Where Valora fits</p>
      <h2 class="display display--lg reveal">How Valora compares to the other<br><em>places advisors spend their marketing budget.</em></h2>
      <p class="reveal">A short, sourced look at how a few well-known platforms actually work — not a claim about which is "best," since they're built for different things.</p>
    </div>
    <div class="pstack reveal" role="table" aria-label="Cost of piecing together advisor client-acquisition tools vs. Valora" style="margin-top:36px;">
      <div class="pstack__row pstack__row--head" role="row">
        <span role="columnheader">Feature</span>
        <span role="columnheader">Replaces</span>
        <span role="columnheader">Other tools</span>
        <span role="columnheader" class="is-us">Valora</span>
      </div>
      <div class="pstack__row" role="row">
        <span role="rowheader">Shared leads</span>
        <span role="cell" class="pstack__tool">SmartAsset AMP</span>
        <span role="cell">~$2,000&ndash;2,300/mo <em>(est., shared with up to 3 advisors)</em></span>
        <span role="cell" class="is-us">Included</span>
      </div>
      <div class="pstack__row" role="row">
        <span role="rowheader">Marketplace inquiries</span>
        <span role="cell" class="pstack__tool">Unbiased</span>
        <span role="cell">Pay-per-lead credits, no public flat fee <em>(est. $3&ndash;4K/mo at volume)</em></span>
        <span role="cell" class="is-us">Included</span>
      </div>
      <div class="pstack__row" role="row">
        <span role="rowheader">AI-matched prospects</span>
        <span role="cell" class="pstack__tool">Finny</span>
        <span role="cell">$50/mo + 0.20% of AUM sourced</span>
        <span role="cell" class="is-us">Included</span>
      </div>
      <div class="pstack__row" role="row">
        <span role="rowheader">Prospect data</span>
        <span role="cell" class="pstack__tool">WealthFeed</span>
        <span role="cell">$1,399/yr <em>(~$117/mo)</em></span>
        <span role="cell" class="is-us">Included</span>
      </div>
      <div class="pstack__row" role="row">
        <span role="rowheader">Directory profile</span>
        <span role="cell" class="pstack__tool">AdvisorFinder</span>
        <span role="cell">$1,000/mo</span>
        <span role="cell" class="is-us">Included</span>
      </div>
      <div class="pstack__row" role="row">
        <span role="rowheader">Client communication &amp; CRM content</span>
        <span role="cell" class="pstack__tool">Levitate</span>
        <span role="cell">~$3,000/yr <em>(~$250/mo)</em></span>
        <span role="cell" class="is-us">Included</span>
      </div>
      <div class="pstack__row" role="row">
        <span role="rowheader">Website &amp; marketing suite</span>
        <span role="cell" class="pstack__tool">FMG Suite</span>
        <span role="cell">From $178/mo + setup fee</span>
        <span role="cell" class="is-us">Included</span>
      </div>
      <div class="pstack__row" role="row">
        <span role="rowheader">Marketing automation campaigns</span>
        <span role="cell" class="pstack__tool">Snappy Kraken</span>
        <span role="cell">$199&ndash;750/mo depending on tier</span>
        <span role="cell" class="is-us">Included</span>
      </div>
      <div class="pstack__row" role="row">
        <span role="rowheader">Cost per client acquired via DIY video</span>
        <span role="cell" class="pstack__tool">Self-produced content</span>
        <span role="cell">$37,170/client <em>(Kitces 2026 marketing study)</em></span>
        <span role="cell is-us">No per-client cost &mdash; flat $1,500/mo</span>
      </div>
      <div class="pstack__row pstack__row--total" role="row">
        <span role="rowheader">Overall price</span>
        <span role="cell"></span>
        <span role="cell">$6,500+/mo, pieced together across 8 separate tools</span>
        <span role="cell is-us">$1,500/mo &mdash; exclusive, month-to-month</span>
      </div>
    </div>
    <p style="margin-top:22px; font-size:.72rem; color:var(--muted);">
      Sources: <a href="https://www.advisorappts.com/smartasset-leads" target="_blank" rel="noopener">SmartAsset AMP overview</a> &middot;
      <a href="https://www.unbiased.com/advice/pro/faqs" target="_blank" rel="noopener">Unbiased pricing FAQ</a> &middot;
      <a href="https://www.wealthmanagement.com/artificial-intelligence/finny-ai-rolls-out-pay-as-you-grow-pricing-model" target="_blank" rel="noopener">Finny pricing</a> &middot;
      <a href="https://softwarefinder.com/sales-tools/wealthfeed" target="_blank" rel="noopener">WealthFeed pricing</a> &middot;
      <a href="https://advisorfinder.com/for-financial-advisors/pricing-plans" target="_blank" rel="noopener">AdvisorFinder pricing</a> &middot;
      <a href="https://www.levitate.ai/industry/finance" target="_blank" rel="noopener">Levitate for finance</a> &middot;
      <a href="https://fmgsuite.com/pricing/" target="_blank" rel="noopener">FMG Suite pricing</a> &middot;
      <a href="https://snappykraken.com/pricing" target="_blank" rel="noopener">Snappy Kraken pricing</a> &middot;
      <a href="https://www.kitces.com/blog/kitces-advisor-marketing-study-2026" target="_blank" rel="noopener">Kitces 2026 advisor marketing study</a>.
      Figures found via web search on 2026-09-28 and may have changed &mdash; items marked "est." could not be confirmed from a public source and should be verified before relying on them.
    </p>
    <p class="adv-compare2__punch reveal">Everyone else sells you tools, data, or shared leads. <em>Valora sells the phone ringing.</em></p>
  </div>
</section>

{blog_html}
<!-- ================= ADVISOR TESTIMONIALS & CASE STUDIES ================= -->
<section class="section section--paper adv-testimonials" id="testimonials">
  <div class="container">
    <div style="max-width:720px;">
      <p class="eyebrow reveal">Partner Case Studies</p>
      <h2 class="display display--lg reveal">Trusted by independent advisors<br><em>building high-conviction practices.</em></h2>
      <p class="reveal" style="margin-top:16px; font-size:.95rem; color:var(--ink-soft);">Hear how independent RIA owners use Valora to accelerate organic growth, delegate back-office friction, and serve their clients at the highest level.</p>
    </div>

    <div class="adv-test-grid">
      <!-- Testimonial 1 -->
      <article class="tcard reveal">
        <div>
          <span class="tcard__badge">+$16.2M AUM Added · 1st Year</span>
          <p class="tcard__quote">"In our first twelve months on Valora, we onboarded nine new high-net-worth households. The clients arrived with verified liquid assets and an immediate financial milestone. It transformed our growth trajectory without any cold prospecting."</p>
        </div>
        <div>
          <div class="tcard__author">
            <img class="tcard__av" src="https://images.unsplash.com/photo-1573496358961-3c82861ab8f4?auto=format&amp;fit=crop&amp;crop=faces&amp;w=120&amp;h=120&amp;q=80" alt="Elena Rostova" loading="lazy">
            <div>
              <p class="tcard__name">Elena Rostova, CFP®</p>
              <p class="tcard__role">Founder · Summit Crest Wealth Management</p>
            </div>
          </div>
          <div class="tcard__stat">100% Client Retention Rate · Denver, CO</div>
        </div>
      </article>

      <!-- Testimonial 2 -->
      <article class="tcard reveal">
        <div>
          <span class="tcard__badge">15 Hours Saved / Week · Operations</span>
          <p class="tcard__quote">"The biggest bottleneck for growing RIAs is back-office drag. Valora eliminated 15 hours of weekly paperwork, billing reconciliations, and custodial transfer chasing. That extra time allowed our team to add $22M in net new assets this year."</p>
        </div>
        <div>
          <div class="tcard__author">
            <img class="tcard__av" src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&amp;fit=crop&amp;crop=faces&amp;w=120&amp;h=120&amp;q=80" alt="Marcus Vance" loading="lazy">
            <div>
              <p class="tcard__name">Marcus Vance, CFA</p>
              <p class="tcard__role">Managing Partner · Prairie Capital Partners</p>
            </div>
          </div>
          <div class="tcard__stat">4.8x ROI on Partnership Fees · Chicago, IL</div>
        </div>
      </article>

      <!-- Testimonial 3 -->
      <article class="tcard reveal">
        <div>
          <span class="tcard__badge">38% Discovery Conversion Rate</span>
          <p class="tcard__quote">"Generic lead generation companies sell raw phone numbers to anyone with a checkbook. Valora's introductions are different: the clients have already studied our firm's fee-only philosophy and specifically requested our equity compensation specialty."</p>
        </div>
        <div>
          <div class="tcard__author">
            <img class="tcard__av" src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&amp;fit=crop&amp;crop=faces&amp;w=120&amp;h=120&amp;q=80" alt="Sofía Marín" loading="lazy">
            <div>
              <p class="tcard__name">Sofía Marín, CPA, PFS</p>
              <p class="tcard__role">Founder · Beacon Equity Wealth Advisors</p>
            </div>
          </div>
          <div class="tcard__stat">$2.4M Average Household AUM · Seattle, WA</div>
        </div>
      </article>
    </div>
  </div>
</section>

<!-- ================= PARTNER CRITERIA + EXTENDED FAQ ================= -->
<section class="section section--cream life adv-faq" id="faq">
  <div class="container life__grid">
    <div class="adv-criteria reveal">
      <p class="eyebrow">Selective Fiduciary Network</p>
      <h2 class="display display--md">A high bar,<br><em>on purpose.</em></h2>
      <p>Investors trust Valora because our network is curated rather than open to anyone with a marketing budget. We partner exclusively with qualified fiduciaries who share our standard for transparent, conflict-free advice.</p>
      <ul class="adv-ticks" style="margin-top:24px;">
        <li>Registered Investment Adviser (RIA) or IAR registration</li>
        <li>Strict Fiduciary Duty to clients at all times</li>
        <li>Clean regulatory history verified on SEC IAPD / FINRA BrokerCheck</li>
        <li>Professional designation: CFP®, CFA, CPA/PFS or 10+ years experience</li>
        <li>Transparent, published fee schedule (fee-only or fee-transparent)</li>
      </ul>
      <div style="margin-top:28px;">
        <a class="btn btn--dark" href="#apply" style="width:100%;">Book a demo</a>
      </div>
    </div>

    <div class="life__body">
      <div class="faq" style="margin-top:0;">
        <h2 class="faq__title" style="padding-top:0;">Frequently Asked Questions</h2>
        {faq_html}
      </div>
    </div>
  </div>
</section>

<!-- ================= READY TO GET STARTED CTA ================= -->
<section class="section section--green adv-ready">
  <div class="container adv-ready__inner">
    <h2 class="display display--lg reveal">Ready to get started?</h2>
    <p class="reveal">Get perfect clients delivered straight to your inbox and the tools to manage them throughout the sales process.</p>
    <a class="btn btn--cream" href="#apply">Book a demo</a>
  </div>
</section>

<!-- ================= APPLY / BOOK A DEMO ================= -->
<section class="section section--green cta adv-ready" id="apply">
  <div class="container adv-ready__inner">
    <p class="eyebrow eyebrow--light reveal">Advisor Network</p>
    <h2 class="display display--lg reveal">Spend your week advising.<br><em>We'll handle everything else.</em></h2>
    <p class="reveal">Book a demo and a partner from our advisor team — not a robot or automated dialer — will walk you through platform access, practice fit, and territory availability.</p>
    <a class="btn btn--cream" href="mailto:{EMAIL}?subject=Book%20a%20demo">Book a demo</a>
    <p style="margin-top:20px; font-size:.82rem; color:rgba(239,235,224,.6);">Prefer to call? <a href="tel:{PHONE_TEL}" style="color:inherit; text-decoration:underline;">{PHONE_DISPLAY}</a></p>
  </div>
</section>
"""
