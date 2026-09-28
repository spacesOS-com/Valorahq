# -*- coding: utf-8 -*-
"""Real, working /calculators/[slug]/ pages.

Each one is a simple, transparent formula computed client-side in the
visitor's browser (nothing sent to a server) — no black-box numbers, no
personalized advice. Every page states its formula in plain language and
carries the same "educational estimate, not advice" framing as the rest of
the site. Grouped into categories (Retirement, Taxes, ...) for the footer.
"""
from html import escape

from partials import page, head, BRAND, contact_section, faq_schema

CALCULATORS = [
    {
        "slug": "retirement-savings-growth",
        "category": "Retirement",
        "title": "Retirement savings growth calculator",
        "summary": "Estimate how a lump sum plus monthly contributions could grow over time, before inflation and fees.",
        "note": "Compound growth: (current savings, grown at your rate) + (monthly contributions, grown month by month). "
                "It doesn't account for inflation, fees, taxes, or changing returns — a real projection needs those.",
        "fields": [
            {"id": "cur", "label": "Current savings ($)", "placeholder": "50000"},
            {"id": "mo", "label": "Monthly contribution ($)", "placeholder": "500"},
            {"id": "yrs", "label": "Years until retirement", "placeholder": "25"},
            {"id": "ret", "label": "Assumed annual return (%)", "placeholder": "6"},
        ],
        "result_label": "Estimated future value",
        "js": """
          var cur = parseFloat(f.cur.value) || 0;
          var mo = parseFloat(f.mo.value) || 0;
          var yrs = parseFloat(f.yrs.value) || 0;
          var ret = (parseFloat(f.ret.value) || 0) / 100;
          var n = yrs * 12, r = ret / 12;
          var fvLump = cur * Math.pow(1 + r, n);
          var fvContrib = r > 0 ? mo * ((Math.pow(1 + r, n) - 1) / r) : mo * n;
          var total = fvLump + fvContrib;
          out.textContent = '$' + Math.round(total).toLocaleString();
        """,
    },
    {
        "slug": "safe-withdrawal-amount",
        "category": "Retirement",
        "title": "Withdrawal amount calculator",
        "summary": "Turn a withdrawal rate and portfolio value into a dollar amount — pair this with our article on what a realistic withdrawal rate looks like today.",
        "note": "This is arithmetic (portfolio × rate), not a recommendation of what your rate should be. "
                "See “What a realistic withdrawal rate looks like now” in our insights for the factors that "
                "actually move that number.",
        "fields": [
            {"id": "pv", "label": "Portfolio value ($)", "placeholder": "1000000"},
            {"id": "rate", "label": "Withdrawal rate (%)", "placeholder": "4"},
        ],
        "result_label": "Estimated annual / monthly withdrawal",
        "js": """
          var pv = parseFloat(f.pv.value) || 0;
          var rate = (parseFloat(f.rate.value) || 0) / 100;
          var annual = pv * rate;
          out.textContent = '$' + Math.round(annual).toLocaleString() + ' / yr  (\\u2248 $' + Math.round(annual/12).toLocaleString() + ' / mo)';
        """,
        "related": "/insights/realistic-withdrawal-rate-today/",
    },
    {
        "slug": "roth-conversion-tax-cost",
        "category": "Taxes",
        "title": "Roth conversion tax cost calculator",
        "summary": "A rough estimate of what converting a given amount would cost at a flat tax rate — pair this with our article on when a Roth conversion is worth it.",
        "note": "Real U.S. tax brackets are progressive, not flat — this uses one flat rate as a simplification. "
                "See “When a Roth conversion is worth the tax bill” in our insights, and talk to a CPA before "
                "converting, since bracket effects and Medicare premium thresholds can change the real cost.",
        "fields": [
            {"id": "amt", "label": "Amount to convert ($)", "placeholder": "50000"},
            {"id": "rate", "label": "Assumed marginal tax rate (%)", "placeholder": "24"},
        ],
        "result_label": "Estimated tax cost / net after tax",
        "js": """
          var amt = parseFloat(f.amt.value) || 0;
          var rate = (parseFloat(f.rate.value) || 0) / 100;
          var tax = amt * rate;
          out.textContent = '$' + Math.round(tax).toLocaleString() + ' tax  (\\u2248 $' + Math.round(amt - tax).toLocaleString() + ' net converted)';
        """,
        "related": "/insights/when-roth-conversion-worth-tax-bill/",
    },
    {
        "slug": "how-long-savings-will-last",
        "category": "Retirement",
        "title": "How long your savings will last",
        "summary": "Turn a portfolio, a fixed annual withdrawal, and an assumed return into an estimated number of years.",
        "note": "This assumes a constant annual withdrawal and a constant annual return — real markets and "
                "real spending both vary year to year, which is exactly what sequence-of-returns risk is about. "
                "See “What happens if the market drops right before you retire” in our insights.",
        "fields": [
            {"id": "sv", "label": "Current savings ($)", "placeholder": "1000000"},
            {"id": "w", "label": "Annual withdrawal ($)", "placeholder": "40000"},
            {"id": "ret", "label": "Assumed annual return (%)", "placeholder": "5"},
        ],
        "result_label": "Estimated years until depleted",
        "js": """
          var sv = parseFloat(f.sv.value) || 0;
          var w = parseFloat(f.w.value) || 0;
          var ret = (parseFloat(f.ret.value) || 0) / 100;
          if (w <= 0) { out.textContent = 'Enter an annual withdrawal amount'; return; }
          if (ret > 0 && sv * ret >= w) {
            out.textContent = 'Indefinitely \\u2014 withdrawals are covered by growth alone';
            return;
          }
          var years = ret === 0 ? sv / w : -Math.log(1 - (sv * ret) / w) / Math.log(1 + ret);
          out.textContent = (years > 0 ? years.toFixed(1) : '0') + ' years';
        """,
        "related": "/insights/market-drop-before-retirement/",
    },
    {
        "slug": "rsu-withholding-shortfall",
        "category": "Taxes",
        "title": "RSU withholding shortfall calculator",
        "summary": "Estimate the gap between the flat 22% most employers withhold on vested RSUs and what you actually owe at your marginal rate.",
        "note": "Most U.S. employers withhold RSU vesting income at the flat 22% federal supplemental-wage rate, "
                "regardless of your actual bracket. This compares that to your marginal rate as a rough estimate — "
                "your real liability depends on your full tax picture. See “Your RSUs are a bonus, not a lottery "
                "ticket” in our insights.",
        "fields": [
            {"id": "val", "label": "Value vesting ($)", "placeholder": "100000"},
            {"id": "rate", "label": "Your marginal tax rate (%)", "placeholder": "32"},
        ],
        "result_label": "Estimated withholding shortfall",
        "js": """
          var val = parseFloat(f.val.value) || 0;
          var rate = (parseFloat(f.rate.value) || 0) / 100;
          var withheld = val * 0.22;
          var owed = val * rate;
          var diff = owed - withheld;
          if (diff > 0) {
            out.textContent = '$' + Math.round(diff).toLocaleString() + ' short (22% withheld vs. your rate)';
          } else {
            out.textContent = 'No shortfall at this rate \\u2014 22% likely covers it';
          }
        """,
        "related": "/insights/rsus-bonus-not-lottery-ticket/",
    },
    {
        "slug": "401k-contribution-limit",
        "category": "Retirement",
        "title": "401(k) contribution limit calculator",
        "summary": "Check your 2026 401(k) employee deferral limit by age, and how much contribution room you have left.",
        "note": "2026 IRS limits: $24,500 base employee deferral; +$8,000 catch-up for age 50+; a $11,250 "
                "“super catch-up” for ages 60–63 (in place of the standard catch-up) under SECURE 2.0. "
                "If you earned over $150,000 in 2025, 2026 catch-up contributions must be made as Roth. "
                "Source: IRS, “401(k) limit increases to $24,500 for 2026.”",
        "fields": [
            {"id": "age", "label": "Your age", "placeholder": "45"},
            {"id": "planned", "label": "Planned contribution this year ($)", "placeholder": "20000"},
        ],
        "result_label": "Your 2026 limit and room left",
        "js": """
          var age = parseFloat(f.age.value) || 0;
          var planned = parseFloat(f.planned.value) || 0;
          var limit = 24500;
          if (age >= 60 && age <= 63) limit = 24500 + 11250;
          else if (age >= 50) limit = 24500 + 8000;
          var room = limit - planned;
          out.textContent = '$' + limit.toLocaleString() + ' limit \\u2014 ' +
            (room >= 0 ? '$' + Math.round(room).toLocaleString() + ' of room left' : '$' + Math.round(-room).toLocaleString() + ' over the limit');
        """,
    },
    {
        "slug": "rmd-estimate",
        "category": "Retirement",
        "title": "Required minimum distribution (RMD) calculator",
        "summary": "Estimate your required minimum distribution using the IRS Uniform Lifetime Table.",
        "note": "Uses the IRS Uniform Lifetime Table (Publication 590-B, Table III), in effect since 2022. "
                "RMDs generally start at age 73 (born 1951–1959) or 75 (born 1960 or later) under SECURE 2.0. "
                "This divides last December 31's balance by the divisor for your age — it doesn't apply to Roth "
                "IRAs (no RMDs) or account for the Joint Life table used when a spouse is the sole beneficiary and "
                "more than 10 years younger.",
        "fields": [
            {"id": "age", "label": "Your age this year", "placeholder": "75"},
            {"id": "bal", "label": "Account balance, Dec 31 last year ($)", "placeholder": "500000"},
        ],
        "result_label": "Estimated RMD this year",
        "js": """
          var table = {72:27.4,73:26.5,74:25.5,75:24.6,76:23.7,77:22.9,78:22.0,79:21.1,80:20.2,81:19.4,82:18.5,83:17.7,84:16.8,85:16.0,86:15.2,87:14.4,88:13.7,89:12.9,90:12.2,91:11.5,92:10.8,93:10.1,94:9.5,95:8.9,96:8.4,97:7.8,98:7.3,99:6.8,100:6.4};
          var age = Math.round(parseFloat(f.age.value) || 0);
          var bal = parseFloat(f.bal.value) || 0;
          if (age < 72) { out.textContent = 'RMDs don\\'t apply below age 72 (73 or 75 for most people \\u2014 see the note)'; return; }
          var div = table[age] || (age > 100 ? 2.0 : null);
          if (!div) { out.textContent = 'Age out of table range'; return; }
          out.textContent = '$' + Math.round(bal / div).toLocaleString() + ' (divisor: ' + div + ')';
        """,
    },
    {
        "slug": "capital-gains-tax-estimate",
        "category": "Taxes",
        "title": "Capital gains tax estimator",
        "summary": "Estimate federal long-term capital gains tax using the real 2026 income brackets — gains stack on top of your other taxable income.",
        "note": "2026 federal long-term capital gains brackets: Single — 0% to $49,450, 15% to $545,500, 20% "
                "above. Married filing jointly — 0% to $98,900, 15% to $613,700, 20% above. This is federal "
                "only — it doesn't include state capital gains tax or the 3.8% Net Investment Income Tax that "
                "can apply at higher incomes. Source: IRS 2026 inflation adjustments.",
        "fields": [
            {"id": "status", "label": "Filing status", "type": "select",
             "options": ["Single", "Married filing jointly"]},
            {"id": "income", "label": "Other taxable income ($)", "placeholder": "120000"},
            {"id": "gain", "label": "Long-term capital gain ($)", "placeholder": "50000"},
        ],
        "result_label": "Estimated federal tax on the gain",
        "js": """
          var brackets = {
            'Single': [[49450,0],[545500,.15],[Infinity,.20]],
            'Married filing jointly': [[98900,0],[613700,.15],[Infinity,.20]]
          };
          var status = f.status.value || 'Single';
          var income = parseFloat(f.income.value) || 0;
          var gain = parseFloat(f.gain.value) || 0;
          var b = brackets[status];
          var start = income, end = income + gain, tax = 0, floor = 0;
          for (var i = 0; i < b.length; i++) {
            var cap = b[i][0], rate = b[i][1];
            var lo = Math.max(start, floor), hi = Math.min(end, cap);
            if (hi > lo) tax += (hi - lo) * rate;
            floor = cap;
          }
          var rate = gain > 0 ? (tax / gain * 100) : 0;
          out.textContent = '$' + Math.round(tax).toLocaleString() + ' (\\u2248 ' + rate.toFixed(1) + '% blended rate)';
        """,
    },
    {
        "slug": "inflation-calculator",
        "category": "Investing",
        "title": "Inflation calculator",
        "summary": "See what a dollar amount today is worth in the future — or was worth in the past — at a given inflation rate.",
        "note": "Pure compounding: amount × (1 + rate)^years. The default 3% approximates the Federal "
                "Reserve's long-run inflation target and recent multi-decade U.S. averages — actual inflation "
                "varies significantly year to year.",
        "fields": [
            {"id": "amt", "label": "Amount ($)", "placeholder": "10000"},
            {"id": "yrs", "label": "Number of years", "placeholder": "20"},
            {"id": "rate", "label": "Assumed annual inflation (%)", "placeholder": "3"},
        ],
        "result_label": "Equivalent future purchasing power",
        "js": """
          var amt = parseFloat(f.amt.value) || 0;
          var yrs = parseFloat(f.yrs.value) || 0;
          var rate = (parseFloat(f.rate.value) || 0) / 100;
          var future = amt * Math.pow(1 + rate, yrs);
          out.textContent = '$' + Math.round(future).toLocaleString() + ' would have the same purchasing power as $' + Math.round(amt).toLocaleString() + ' today';
        """,
    },
    {
        "slug": "investment-future-value",
        "category": "Investing",
        "title": "Investment future value calculator",
        "summary": "Estimate the future value of a lump-sum investment plus optional monthly additions at a given return.",
        "note": "Standard compound growth math — the same formula behind our retirement savings calculator, "
                "framed for any investing goal, not just retirement. Doesn't account for taxes, fees, or "
                "variable returns.",
        "fields": [
            {"id": "cur", "label": "Starting amount ($)", "placeholder": "10000"},
            {"id": "mo", "label": "Monthly addition ($)", "placeholder": "300"},
            {"id": "yrs", "label": "Years invested", "placeholder": "10"},
            {"id": "ret", "label": "Assumed annual return (%)", "placeholder": "7"},
        ],
        "result_label": "Estimated future value",
        "js": """
          var cur = parseFloat(f.cur.value) || 0;
          var mo = parseFloat(f.mo.value) || 0;
          var yrs = parseFloat(f.yrs.value) || 0;
          var ret = (parseFloat(f.ret.value) || 0) / 100;
          var n = yrs * 12, r = ret / 12;
          var fvLump = cur * Math.pow(1 + r, n);
          var fvContrib = r > 0 ? mo * ((Math.pow(1 + r, n) - 1) / r) : mo * n;
          out.textContent = '$' + Math.round(fvLump + fvContrib).toLocaleString();
        """,
    },
    {
        "slug": "savings-cd-growth",
        "category": "Banking",
        "title": "Savings & CD growth calculator",
        "summary": "Estimate what a savings account or CD balance grows to at a fixed annual rate.",
        "note": "Standard compound interest, compounded monthly. A real CD or savings APY may compound daily "
                "or differently, and rates on savings accounts can change — CDs lock in a fixed rate for a term.",
        "fields": [
            {"id": "cur", "label": "Starting balance ($)", "placeholder": "10000"},
            {"id": "yrs", "label": "Term / years", "placeholder": "2"},
            {"id": "rate", "label": "Annual percentage yield (%)", "placeholder": "4.5"},
        ],
        "result_label": "Estimated ending balance",
        "js": """
          var cur = parseFloat(f.cur.value) || 0;
          var yrs = parseFloat(f.yrs.value) || 0;
          var rate = (parseFloat(f.rate.value) || 0) / 100;
          var n = yrs * 12, r = rate / 12;
          var total = cur * Math.pow(1 + r, n);
          out.textContent = '$' + Math.round(total).toLocaleString() + ' (\\u2248 $' + Math.round(total - cur).toLocaleString() + ' in interest)';
        """,
    },
    {
        "slug": "budget-50-30-20",
        "category": "Banking",
        "title": "50/30/20 budget calculator",
        "summary": "Split your take-home pay into needs, wants, and savings using the common 50/30/20 guideline.",
        "note": "The 50/30/20 split (50% needs, 30% wants, 20% savings/debt paydown) is a popular rule of thumb, "
                "not a rule — the right split depends on your cost of living, debt, and goals. This is "
                "arithmetic on the number you enter, nothing more.",
        "fields": [
            {"id": "inc", "label": "Monthly take-home pay ($)", "placeholder": "6000"},
        ],
        "result_label": "Needs / Wants / Savings",
        "js": """
          var inc = parseFloat(f.inc.value) || 0;
          out.textContent = '$' + Math.round(inc*0.5).toLocaleString() + ' needs \\u00b7 $' + Math.round(inc*0.3).toLocaleString() + ' wants \\u00b7 $' + Math.round(inc*0.2).toLocaleString() + ' savings';
        """,
    },
    {
        "slug": "social-security-breakeven",
        "category": "Social Security",
        "title": "Social Security claiming age break-even calculator",
        "summary": "See the age at which claiming later (70) overtakes claiming early (62) in total lifetime benefits.",
        "note": "Uses standard published SSA reduction/credit factors for a full retirement age of 67: claiming "
                "at 62 reduces the benefit to 70% of the full-retirement-age amount; delaying to 70 increases it "
                "to 124% (8% per year of delay). Ignores cost-of-living adjustments, taxes, spousal benefits, "
                "and the time value of money — all of which a full analysis should include.",
        "fields": [
            {"id": "fra", "label": "Estimated monthly benefit at full retirement age (67) ($)", "placeholder": "2400"},
        ],
        "result_label": "Break-even age (claiming 62 vs. 70)",
        "js": """
          var fra = parseFloat(f.fra.value) || 0;
          var b62 = fra * 0.70, b70 = fra * 1.24;
          var breakeven = null;
          for (var age = 70; age <= 100; age++) {
            var cum62 = b62 * 12 * (age - 62);
            var cum70 = b70 * 12 * (age - 70);
            if (cum70 > cum62) { breakeven = age; break; }
          }
          out.textContent = breakeven ? 'Age ' + breakeven + ' (monthly: $' + Math.round(b62).toLocaleString() + ' at 62 vs. $' + Math.round(b70).toLocaleString() + ' at 70)' : 'Beyond age 100';
        """,
    },
    {
        "slug": "delayed-retirement-credit",
        "category": "Social Security",
        "title": "Delayed retirement credit calculator",
        "summary": "See how much your Social Security benefit grows for each year you delay claiming past full retirement age.",
        "note": "Social Security adds an 8% delayed retirement credit for each full year you delay claiming past "
                "full retirement age, up to age 70 — a well-documented, stable SSA rule (not adjusted for "
                "inflation here).",
        "fields": [
            {"id": "fra", "label": "Monthly benefit at full retirement age ($)", "placeholder": "2400"},
            {"id": "delay", "label": "Years delayed past full retirement age (0–3)", "placeholder": "3"},
        ],
        "result_label": "Increased monthly benefit",
        "js": """
          var fra = parseFloat(f.fra.value) || 0;
          var delay = Math.min(3, Math.max(0, parseFloat(f.delay.value) || 0));
          var increased = fra * (1 + 0.08 * delay);
          out.textContent = '$' + Math.round(increased).toLocaleString() + '/mo (+' + (delay*8) + '%)';
        """,
    },
    {
        "slug": "iso-exercise-cost",
        "category": "Equity Compensation",
        "title": "ISO exercise cost & spread calculator",
        "summary": "Estimate the cash cost to exercise incentive stock options and the resulting spread (a common AMT trigger).",
        "note": "Exercise cost = shares \\u00d7 strike price. Spread = shares \\u00d7 (current FMV \\u2212 strike "
                "price) \\u2014 this spread is a preference item that can trigger the Alternative Minimum Tax even "
                "though you haven't sold the shares. This doesn't calculate AMT itself, which depends on your "
                "full tax picture.",
        "fields": [
            {"id": "shares", "label": "Number of options", "placeholder": "1000"},
            {"id": "strike", "label": "Strike price ($)", "placeholder": "5"},
            {"id": "fmv", "label": "Current fair market value ($)", "placeholder": "25"},
        ],
        "result_label": "Exercise cost / potential AMT spread",
        "js": """
          var shares = parseFloat(f.shares.value) || 0;
          var strike = parseFloat(f.strike.value) || 0;
          var fmv = parseFloat(f.fmv.value) || 0;
          var cost = shares * strike;
          var spread = Math.max(0, shares * (fmv - strike));
          out.textContent = '$' + Math.round(cost).toLocaleString() + ' to exercise, $' + Math.round(spread).toLocaleString() + ' spread (potential AMT income)';
        """,
        "related": "/insights/rsus-bonus-not-lottery-ticket/",
    },
    {
        "slug": "concentration-diversification-timeline",
        "category": "Equity Compensation",
        "title": "Concentrated stock diversification timeline",
        "summary": "Estimate how long it would take to diversify out of a concentrated position at a fixed dollar amount sold per year.",
        "note": "Simple arithmetic: (current position \\u2212 target position) \\u00f7 amount sold per year. "
                "Doesn't account for the stock's price changes, taxes on each sale, or blackout/trading windows "
                "\\u2014 a real diversification plan needs those.",
        "fields": [
            {"id": "cur", "label": "Current position value ($)", "placeholder": "500000"},
            {"id": "target", "label": "Target position value ($)", "placeholder": "50000"},
            {"id": "peryear", "label": "Amount sold per year ($)", "placeholder": "75000"},
        ],
        "result_label": "Estimated years to reach target",
        "js": """
          var cur = parseFloat(f.cur.value) || 0;
          var target = parseFloat(f.target.value) || 0;
          var peryear = parseFloat(f.peryear.value) || 0;
          if (peryear <= 0) { out.textContent = 'Enter an amount sold per year'; return; }
          var years = (cur - target) / peryear;
          out.textContent = years > 0 ? years.toFixed(1) + ' years' : 'Already at or below target';
        """,
    },
]

CATEGORIES = ["Retirement", "Taxes", "Social Security", "Equity Compensation", "Investing", "Banking"]


def _field_html(slug, f):
    if f.get("type") == "select":
        opts = "".join(f"<option>{escape(o)}</option>" for o in f["options"])
        return f"""
        <div class="field" data-field>
          <label for="{slug}-{f['id']}">{escape(f['label'])}</label>
          <select id="{slug}-{f['id']}" name="{f['id']}">{opts}</select>
        </div>"""
    ph = f.get("placeholder", "")
    return f"""
        <div class="field" data-field>
          <label for="{slug}-{f['id']}">{escape(f['label'])}</label>
          <input id="{slug}-{f['id']}" name="{f['id']}" type="number" inputmode="decimal" placeholder="{escape(ph)}" value="{escape(ph)}">
        </div>"""


def _calc_body(c):
    fields = "\n".join(_field_html(c["slug"], f) for f in c["fields"])
    related = (f'<p style="margin-top:14px;"><a href="{escape(c["related"])}">Read the related article &rarr;</a></p>'
               if c.get("related") else "")
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:680px;">
    <a href="/#insights" class="btn btn--outline" style="margin-bottom:32px;">&larr; Back</a>
    <p class="eyebrow reveal">{escape(c['category'])} calculator</p>
    <h1 class="display display--lg reveal">{escape(c['title'])}</h1>
    <p class="reveal" style="margin-top:14px; color:var(--ink-soft); max-width:56ch;">{escape(c['summary'])}</p>

    <form id="calcForm" class="form" style="margin-top:36px; grid-template-columns:1fr 1fr;" onsubmit="return false;">
      {fields}
    </form>

    <div class="calc-result">
      <p class="calc-result__label">{escape(c['result_label'])}</p>
      <p class="calc-result__value" id="calcOut">&mdash;</p>
    </div>

    <p style="margin-top:24px; font-size:.82rem; color:var(--muted); max-width:60ch;">{c['note']}</p>
    {related}
  </div>
</section>

<script>
(function () {{
  var f = document.getElementById('calcForm');
  var out = document.getElementById('calcOut');
  function calc() {{
    {c['js']}
  }}
  f.addEventListener('input', calc);
  calc();
}})();
</script>

{contact_section()}
"""


def _category_slug(category):
    return category.lower().replace(" ", "-")


def _category_body(category, calcs):
    cards = "\n".join(f"""      <a class="blogcard reveal" href="/calculators/{escape(c['slug'])}/">
        <h3>{escape(c['title'])}</h3>
        <p>{escape(c['summary'])}</p>
        <span class="blogcard__link">Open calculator &rarr;</span>
      </a>""" for c in calcs)
    return f"""
<section class="section section--paper" id="top">
  <div class="container">
    <a href="/#insights" class="btn btn--outline" style="margin-bottom:32px;">&larr; Back</a>
    <p class="eyebrow reveal">Calculators</p>
    <h1 class="display display--lg reveal">{escape(category)} calculators</h1>
    <p class="reveal" style="margin-top:14px; color:var(--ink-soft); max-width:56ch;">Simple, transparent estimates — computed in your browser, nothing sent to a server. Educational, not personalized advice.</p>
    <div class="adv-blog__grid" style="margin-top:36px;">
{cards}
    </div>
  </div>
</section>

{contact_section()}
"""


def build_calculator_pages(write_fn):
    for c in CALCULATORS:
        schema = faq_schema([(f"How is the {c['title'].lower()} calculated?", c["note"])])
        html = page(
            head(f"{c['title']} | {BRAND}", c["summary"], path=f"/calculators/{c['slug']}/", schema=schema),
            _calc_body(c),
            with_gate=True,
        )
        write_fn(f"/calculators/{c['slug']}/", html)

    for category in CATEGORIES:
        slug = _category_slug(category)
        calcs = [c for c in CALCULATORS if c["category"] == category]
        html = page(
            head(f"{category} Calculators | {BRAND}",
                 f"Free {category.lower()} calculators from Valora — simple, transparent estimates.",
                 path=f"/calculators/{slug}/"),
            _category_body(category, calcs),
            with_gate=True,
        )
        write_fn(f"/calculators/{slug}/", html)
