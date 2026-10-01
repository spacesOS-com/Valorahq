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
          var cur = Number(f.cur.value), mo = Number(f.mo.value);
          var yrs = Number(f.yrs.value), retPct = Number(f.ret.value);
          if ([f.cur, f.mo, f.yrs, f.ret].some(function (field) { return field.value.trim() === ''; }) ||
              ![cur, mo, yrs, retPct].every(Number.isFinite) ||
              cur < 0 || mo < 0 || yrs < 0 || yrs > 100 || retPct <= -100 || retPct > 100 ||
              cur > Number.MAX_SAFE_INTEGER || mo > Number.MAX_SAFE_INTEGER) {
            out.textContent = 'Enter savings and contributions of $0 or more, 0-100 years, and an annual return above -100% and at most 100%.';
            return;
          }
          var n = Math.round(yrs * 12), r = retPct / 1200;
          var factor = Math.pow(1 + r, n);
          var fvLump = cur * factor;
          var fvContrib = r !== 0 ? mo * ((factor - 1) / r) : mo * n;
          var total = fvLump + fvContrib;
          out.textContent = '$' + Math.round(total).toLocaleString();
        """,
    },
    {
        "slug": "roth-ira-growth",
        "category": "Retirement",
        "title": "Roth IRA growth calculator",
        "summary": "Model how a Roth IRA balance and a steady annual contribution might grow at an assumed return.",
        "note": "Hypothetical growth only: the annual contribution entered here is NOT a permitted contribution amount, "
                "even if the calculator displays a result. The model assumes contributions at each year-end, a constant return, and annual compounding. "
                "The 2026 combined traditional-and-Roth IRA contribution reference is generally $7,500 ($8,600 at age 50+), "
                "subject to taxable compensation, income and filing status; a joint-filing spouse may qualify through the other spouse's compensation. "
                "Limits and eligibility can change during this projection. Check the IRS rules for each actual contribution year.",
        "fields": [
            {"id": "cur", "label": "Current Roth IRA balance ($)", "placeholder": "10000", "min": 0},
            {"id": "annual", "label": "Illustrative annual contribution ($)", "placeholder": "5000", "min": 0},
            {"id": "yrs", "label": "Years invested", "placeholder": "20", "min": 0, "max": 100},
            {"id": "ret", "label": "Assumed annual return (%)", "placeholder": "6", "min": -99.99, "max": 100},
        ],
        "result_label": "Illustrative Roth IRA balance",
        "js": """
          var cur = Number(f.cur.value), annual = Number(f.annual.value);
          var yrs = Number(f.yrs.value), retPct = Number(f.ret.value);
          if ([f.cur, f.annual, f.yrs, f.ret].some(function (field) { return field.value.trim() === ''; }) ||
              ![cur, annual, yrs, retPct].every(Number.isFinite) ||
              cur < 0 || annual < 0 || cur > Number.MAX_SAFE_INTEGER || annual > Number.MAX_SAFE_INTEGER ||
              !Number.isInteger(yrs) || yrs < 0 || yrs > 100 ||
              retPct <= -100 || retPct > 100) {
            out.textContent = 'Enter nonnegative balances and contributions, whole years from 0 to 100, and a return above -100% and at most 100%.';
            return;
          }
          var total = cur, r = retPct / 100;
          for (var year = 0; year < yrs; year++) total = total * (1 + r) + annual;
          out.textContent = '$' + Math.round(total).toLocaleString();
        """,
    },
    {
        "slug": "compound-interest",
        "category": "Investing",
        "title": "Compound interest calculator",
        "summary": "Estimate a starting balance plus monthly additions with a fixed annual rate and monthly compounding.",
        "note": "Illustrative nominal-rate model: balance compounds monthly at the annual rate divided by 12; contributions arrive at month-end. "
                "A quoted APY already includes compounding, so do not enter an APY as a nominal rate. "
                "Actual investment returns are not fixed; this omits fees, taxes and inflation. Educational estimate only.",
        "fields": [
            {"id": "cur", "label": "Starting balance ($)", "placeholder": "10000", "min": 0},
            {"id": "mo", "label": "Monthly addition ($)", "placeholder": "300", "min": 0},
            {"id": "yrs", "label": "Years", "placeholder": "10", "min": 0, "max": 100},
            {"id": "ret", "label": "Nominal annual rate (%)", "placeholder": "5", "min": -99.99, "max": 100},
        ],
        "result_label": "Estimated ending balance",
        "js": """
          var cur = Number(f.cur.value), mo = Number(f.mo.value);
          var yrs = Number(f.yrs.value), retPct = Number(f.ret.value);
          if ([f.cur, f.mo, f.yrs, f.ret].some(function (field) { return field.value.trim() === ''; }) ||
              ![cur, mo, yrs, retPct].every(Number.isFinite) ||
              cur < 0 || mo < 0 || yrs < 0 || yrs > 100 || retPct <= -100 || retPct > 100 ||
              cur > Number.MAX_SAFE_INTEGER || mo > Number.MAX_SAFE_INTEGER) {
            out.textContent = 'Enter nonnegative balances and additions, 0-100 years, and a nominal annual rate above -100% and at most 100%.';
            return;
          }
          var n = Math.round(yrs * 12), r = retPct / 1200, total = cur;
          for (var month = 0; month < n; month++) total = total * (1 + r) + mo;
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
            {"id": "amt", "label": "Amount to convert ($)", "placeholder": "50000", "min": 0},
            {"id": "rate", "label": "Assumed marginal tax rate (%)", "placeholder": "24", "min": 0, "max": 100},
        ],
        "result_label": "Estimated tax cost",
        "js": """
          var amt = Number(f.amt.value);
          var ratePct = Number(f.rate.value);
          if (f.amt.value.trim() === '' || f.rate.value.trim() === '' ||
              !Number.isFinite(amt) || !Number.isFinite(ratePct) ||
              amt < 0 || ratePct < 0 || ratePct > 100) {
            out.textContent = 'Enter an amount of $0 or more and a tax rate from 0% to 100%.';
            return;
          }
          var rate = ratePct / 100;
          var tax = amt * rate;
          out.textContent = '$' + Math.round(tax).toLocaleString() + ' estimated tax';
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
        "slug": "pslf-scenario-explorer",
        "category": "Banking",
        "title": "PSLF scenario explorer",
        "summary": "Compare two rough scenarios side by side - continuing toward PSLF versus paying the loan down - with every assumption visible. Illustrative only; not a forgiveness estimate.",
        "note": "Illustrative single-loan math: run it per loan, or use a weighted-average rate knowing that is itself an approximation. "
                "We do not compute income-driven payments - income, family size, plan rules and recertification all move them. "
                "Enter the monthly payment and the qualifying-payment count from your servicer. The 120 counted payments cannot be "
                "accelerated with extra payments, and qualifying months often do not run continuously (employment changes, "
                "non-qualifying plans, forbearance). PSLF eligibility - Direct Loans, full-time qualifying employer, qualifying "
                "repayment plan, 120 qualifying payments - is yours to verify with your servicer; annual employment certification "
                "is recommended. Sources: studentaid.gov/pslf and studentaid.gov/articles/5-tips-pslf-success/. Not advice.",
        "fields": [
            {"id": "balance", "label": "Current federal loan balance ($)", "placeholder": "200000"},
            {"id": "rate", "label": "Interest rate (%)", "placeholder": "6.5"},
            {"id": "payment", "label": "Monthly payment from your servicer ($)", "placeholder": "800"},
            {"id": "made", "label": "Qualifying payments made so far (0-120)", "placeholder": "36"},
            {"id": "extra", "label": "Optional extra per month for the payoff path ($)", "placeholder": "0"},
        ],
        "result_label": "Illustrative scenario comparison",
        "js": """
          var bal0 = parseFloat(f.balance.value) || 0;
          var r = (parseFloat(f.rate.value) || 0) / 100 / 12;
          var pay = parseFloat(f.payment.value) || 0;
          var made = parseInt(f.made.value, 10) || 0;
          made = Math.min(120, Math.max(0, made));
          var extra = parseFloat(f.extra.value) || 0;
          if (bal0 <= 0 || pay <= 0) { out.textContent = 'Enter a loan balance and monthly payment'; return; }
          var money = function (n) { return '$' + Math.round(n).toLocaleString('en-US'); };
          var rem = 120 - made;
          /* PSLF path: project the balance over the remaining counted payments */
          var bal = bal0, m = 0;
          for (m = 0; m < rem; m++) {
            var i1 = bal * r;
            bal = bal + i1 - pay;
            if (bal <= 0) { bal = 0; break; }
          }
          var pslf;
          if (bal <= 0) {
            pslf = 'PSLF path: the loan reaches zero within the remaining counted payments at this payment';
          } else {
            var grows = pay < bal0 * r;
            pslf = 'PSLF path: ' + rem + ' counted payments left, projected balance then ~' + money(bal) +
                   (grows ? ' (growing - payment below monthly interest)' : '');
          }
          /* Payoff path: months to zero at payment + extra, exact month-by-month */
          var p2 = pay + extra, po;
          if (r > 0 && p2 <= bal0 * r) {
            po = 'Payoff path: payment does not cover monthly interest - the balance never falls';
          } else {
            var bal2 = bal0, tot = 0, m2 = 0;
            while (bal2 > 0 && m2 < 1200) {
              var i2 = bal2 * r;
              var pmt = Math.min(p2, bal2 + i2);
              tot += pmt;
              bal2 = bal2 + i2 - pmt;
              m2++;
            }
            po = 'Payoff path: ' + m2 + ' months to zero, ~' + money(tot - bal0) + ' total interest' +
                 (extra > 0 ? ' at ' + money(p2) + '/mo' : '');
          }
          out.textContent = pslf + '. ' + po + '.';
        """,
        "related": "https://studentaid.gov/pslf",
    },
    {
        "slug": "qsbs-issue-spotter",
        "category": "Taxes",
        "eyebrow": "QSBS issue spotter",
        "noindex": True,
        "title": "QSBS issue spotter",
        "summary": "A rules-based screen that lists the qualified small business stock questions worth reviewing with your CPA. Its only output, on every path, is a list of review items - it never decides eligibility and never computes an exclusion.",
        "note": "This screen lists review items only. QSBS qualification is fact-specific across the corporation's history, "
                "the stock's issuance and transfers, the holder, and the applicable gain limits - including state-tax treatment, "
                "which differs. It cannot be determined by a questionnaire. Review the full picture with your CPA and tax counsel. "
                "Rules referenced: IRC Section 1202 as amended; source: thetaxadviser.com Section 1202 coverage. Not tax or legal advice.",
        "fields": [
            {"id": "ccorp", "label": "Is the corporation a C corporation?", "type": "select",
             "options": ["Unknown", "Yes", "No"]},
            {"id": "holder", "label": "Is the holder an individual (or an owner through a pass-through) rather than a corporation?", "type": "select",
             "options": ["Unknown", "Yes", "No"]},
            {"id": "issuance", "label": "Did you acquire the stock at original issuance, directly from the corporation?", "type": "select",
             "options": ["Unknown", "Yes", "No"]},
            {"id": "issued", "label": "Was the stock issued after July 4, 2025, and otherwise eligible?", "type": "select",
             "options": ["Unknown", "Issued after July 4, 2025", "Issued on or before July 4, 2025"]},
            {"id": "holding", "label": "Has the holding period for the potentially applicable tier been met?", "type": "select",
             "options": ["Unknown", "Yes", "No"]},
            {"id": "assets", "label": "Were the corporation's aggregate gross assets not exceeding the applicable ceiling immediately before AND immediately after your issuance?", "type": "select",
             "options": ["Unknown", "Yes", "No"]},
            {"id": "active", "label": "Did the corporation use at least 80% of its assets (by value) in the active conduct of a qualified trade or business during substantially all of your holding period?", "type": "select",
             "options": ["Unknown", "Yes", "No"]},
            {"id": "redemptions", "label": "Any redemptions by the corporation around your issuance, or prior transfers of the stock?", "type": "select",
             "options": ["Unknown", "Yes", "No"]},
        ],
        "result_label": "Review items for your CPA",
        "js": """
          var v = function (id) { return f[id].value; };
          var items = [];
          if (v('ccorp') !== 'Yes') {
            items.push('Entity type is a threshold condition under Sec. 1202 - confirm with your CPA whether the corporation is (and was) a C corporation for the relevant period.');
          }
          if (v('holder') !== 'Yes') {
            items.push('Holder type: Sec. 1202 applies to noncorporate holders. Confirm with your CPA that the holder is an individual (or an owner through a pass-through) rather than a corporation.');
          }
          if (v('issuance') !== 'Yes') {
            items.push('Acquisition history: original issuance directly from the corporation is a threshold condition - transfers, gifts, and rollovers each have their own rules. Review the full chain with your CPA.');
          }
          if (v('issued') === 'Issued after July 4, 2025') {
            items.push('Issuance date places the stock under the amended tiers (50% exclusion at 3 years, 75% at 4, 100% at 5, for stock issued after July 4, 2025 and otherwise eligible, gross-asset ceiling not exceeding $75M) - confirm with your CPA which tier, if any, applies.');
          } else if (v('issued') === 'Issued on or before July 4, 2025') {
            items.push('Earlier-issued stock falls under prior law: the exclusion tier depends on the acquisition date, with the gross-asset ceiling not exceeding $50M and per-issuer gain limits - confirm with your CPA which rules apply.');
          } else {
            items.push('Issuance date: confirm with your CPA when the stock was issued - the amended tiers (stock issued after July 4, 2025) and prior law carry different exclusion tiers and gross-asset ceilings.');
          }
          if (v('holding') !== 'Yes') {
            items.push('Holding period for the potentially applicable tier - confirm with your CPA.');
          }
          if (v('assets') !== 'Yes') {
            items.push('Aggregate gross assets at issuance (immediately before AND immediately after) relative to the applicable ceiling - this corporate history is usually unknown to the holder; confirm with your CPA and the corporation.');
          }
          if (v('active') !== 'Yes') {
            items.push('Active-business requirement: at least 80% of assets (by value) in the active conduct of a qualified trade or business during substantially all of your holding period - confirm with your CPA.');
          }
          if (v('redemptions') !== 'No') {
            items.push('Redemptions by the corporation around your issuance, or prior transfers of the stock, can taint otherwise qualified stock - review with your CPA.');
          }
          items.push('Per-issuer gain limits and state-tax treatment differ and are not screened here - review with your CPA and tax counsel.');
          var esc = function (s) { return s; };
          out.innerHTML = '<ul style="text-align:left; margin:0; padding-left:20px; font-size:1rem; line-height:1.55;">' +
            items.map(function (s) { return '<li style="margin-bottom:10px;">' + esc(s) + '</li>'; }).join('') + '</ul>';
        """,
        "related": "https://www.thetaxadviser.com/issues/2025/oct/section-1202-makeover/",
    },
    {
        "slug": "rsu-withholding-shortfall",
        "category": "Taxes",
        "title": "RSU withholding shortfall calculator",
        "summary": "Illustrative comparison of RSU vesting withheld at a flat supplemental-wage rate versus a higher marginal rate. A rough illustration only, not an estimate of your actual tax liability.",
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
                "can apply at higher incomes. Source: IRS Revenue Procedure 2025-32, published in Internal Revenue Bulletin 2025-44.",
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
          var status = f.status.value;
          var income = Number(f.income.value), gain = Number(f.gain.value);
          if (!brackets[status] || f.income.value.trim() === '' || f.gain.value.trim() === '' ||
              !Number.isFinite(income) || !Number.isFinite(gain) || income < 0 || gain < 0 ||
              income + gain > Number.MAX_SAFE_INTEGER) {
            out.textContent = 'Choose a filing status and enter nonnegative taxable income and long-term gain.';
            return;
          }
          var b = brackets[status];
          var start = income, end = income + gain, tax = 0, floor = 0;
          for (var i = 0; i < b.length; i++) {
            var cap = b[i][0], rate = b[i][1];
            var lo = Math.max(start, floor), hi = Math.min(end, cap);
            if (hi > lo) tax += (hi - lo) * rate;
            floor = cap;
          }
          var rate = gain > 0 ? (tax / gain * 100) : 0;
          out.textContent = '$' + Math.round(tax).toLocaleString() + ' (\u2248 ' + rate.toFixed(1) + '% blended rate)';
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
          var cur = Number(f.cur.value), mo = Number(f.mo.value);
          var yrs = Number(f.yrs.value), retPct = Number(f.ret.value);
          if ([f.cur, f.mo, f.yrs, f.ret].some(function (field) { return field.value.trim() === ''; }) ||
              ![cur, mo, yrs, retPct].every(Number.isFinite) ||
              cur < 0 || mo < 0 || yrs < 0 || yrs > 100 || retPct <= -100 || retPct > 100 ||
              cur > Number.MAX_SAFE_INTEGER || mo > Number.MAX_SAFE_INTEGER) {
            out.textContent = 'Enter starting amount and additions of $0 or more, 0-100 years, and an annual return above -100% and at most 100%.';
            return;
          }
          var n = Math.round(yrs * 12), r = retPct / 1200;
          var factor = Math.pow(1 + r, n);
          var fvLump = cur * factor;
          var fvContrib = r !== 0 ? mo * ((factor - 1) / r) : mo * n;
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
    {
        "slug": "paycheck-calculator",
        "category": "Taxes",
        "title": "Paycheck calculator",
        "summary": "Estimate your take-home pay after federal income tax and FICA (Social Security + Medicare).",
        "note": "Uses the IRS's 2026 federal tax brackets and standard deduction (Rev. Proc. 2025-32, irs.gov), "
                "and 2026 FICA: 6.2% Social Security up to the $184,500 wage base (SSA, announced Oct 2025) plus "
                "1.45% Medicare with no cap. Doesn't include state/local tax, pretax health premiums, or other "
                "withholdings — your actual paycheck will differ.",
        "fields": [
            {"id": "salary", "label": "Gross annual salary ($)", "placeholder": "85000"},
            {"id": "status", "label": "Filing status", "type": "select", "options": ["Single", "Married filing jointly"]},
            {"id": "pretax", "label": "Pretax 401(k) contribution (% of salary)", "placeholder": "6"},
        ],
        "result_label": "Estimated take-home pay",
        "js": """
          var salary = parseFloat(f.salary.value) || 0;
          var mfj = f.status.value.indexOf('Married') === 0;
          var pretaxPct = (parseFloat(f.pretax.value) || 0) / 100;
          var pretax = salary * pretaxPct;
          var stdDed = mfj ? 32200 : 16100;
          var taxable = Math.max(0, salary - pretax - stdDed);
          var brackets = mfj
            ? [[0,0.10],[24800,0.12],[100800,0.22],[211400,0.24],[403550,0.32],[512450,0.35],[768700,0.37]]
            : [[0,0.10],[12400,0.12],[50400,0.22],[105700,0.24],[201775,0.32],[256225,0.35],[640600,0.37]];
          var tax = 0;
          for (var i = 0; i < brackets.length; i++) {
            var lo = brackets[i][0], rate = brackets[i][1];
            var hi = (i + 1 < brackets.length) ? brackets[i + 1][0] : Infinity;
            if (taxable > lo) tax += (Math.min(taxable, hi) - lo) * rate;
          }
          var wageBase = 184500;
          var ss = Math.min(salary - pretax, wageBase) * 0.062;
          var medicare = (salary - pretax) * 0.0145;
          var net = salary - pretax - tax - ss - medicare;
          out.textContent = '$' + Math.round(net).toLocaleString() + '/yr ($' + Math.round(net / 26).toLocaleString() + ' per biweekly paycheck)';
        """,
    },
    {
        "slug": "income-tax-estimate",
        "category": "Taxes",
        "title": "Federal income tax calculator",
        "summary": "Estimate your federal income tax using the 2026 IRS tax brackets.",
        "note": "Uses the IRS's 2026 federal tax brackets and standard deduction (Rev. Proc. 2025-32, irs.gov). "
                "Federal tax only — doesn't include state/local income tax, credits, or above-the-line "
                "deductions beyond the standard deduction.",
        "fields": [
            {"id": "income", "label": "Gross annual income ($)", "placeholder": "95000"},
            {"id": "status", "label": "Filing status", "type": "select", "options": ["Single", "Married filing jointly"]},
        ],
        "result_label": "Estimated federal income tax",
        "js": """
          var income = parseFloat(f.income.value) || 0;
          var mfj = f.status.value.indexOf('Married') === 0;
          var stdDed = mfj ? 32200 : 16100;
          var taxable = Math.max(0, income - stdDed);
          var brackets = mfj
            ? [[0,0.10],[24800,0.12],[100800,0.22],[211400,0.24],[403550,0.32],[512450,0.35],[768700,0.37]]
            : [[0,0.10],[12400,0.12],[50400,0.22],[105700,0.24],[201775,0.32],[256225,0.35],[640600,0.37]];
          var tax = 0;
          for (var i = 0; i < brackets.length; i++) {
            var lo = brackets[i][0], rate = brackets[i][1];
            var hi = (i + 1 < brackets.length) ? brackets[i + 1][0] : Infinity;
            if (taxable > lo) tax += (Math.min(taxable, hi) - lo) * rate;
          }
          var effRate = income > 0 ? (tax / income * 100) : 0;
          out.textContent = '$' + Math.round(tax).toLocaleString() + ' (' + effRate.toFixed(1) + '% effective rate)';
        """,
    },
    {
        "slug": "tax-refund-estimate",
        "category": "Taxes",
        "title": "Tax refund calculator",
        "summary": "Compare what you've had withheld against your estimated tax bill to see a rough refund or amount due.",
        "note": "Uses the IRS's 2026 federal tax brackets and standard deduction (Rev. Proc. 2025-32, irs.gov). "
                "A rough estimate only — doesn't account for credits (child tax credit, etc.), other income, "
                "or itemized deductions.",
        "fields": [
            {"id": "income", "label": "Gross annual income ($)", "placeholder": "95000"},
            {"id": "status", "label": "Filing status", "type": "select", "options": ["Single", "Married filing jointly"]},
            {"id": "withheld", "label": "Federal tax withheld so far this year ($)", "placeholder": "12000"},
        ],
        "result_label": "Estimated refund (or amount due)",
        "js": """
          var income = parseFloat(f.income.value) || 0;
          var withheld = parseFloat(f.withheld.value) || 0;
          var mfj = f.status.value.indexOf('Married') === 0;
          var stdDed = mfj ? 32200 : 16100;
          var taxable = Math.max(0, income - stdDed);
          var brackets = mfj
            ? [[0,0.10],[24800,0.12],[100800,0.22],[211400,0.24],[403550,0.32],[512450,0.35],[768700,0.37]]
            : [[0,0.10],[12400,0.12],[50400,0.22],[105700,0.24],[201775,0.32],[256225,0.35],[640600,0.37]];
          var tax = 0;
          for (var i = 0; i < brackets.length; i++) {
            var lo = brackets[i][0], rate = brackets[i][1];
            var hi = (i + 1 < brackets.length) ? brackets[i + 1][0] : Infinity;
            if (taxable > lo) tax += (Math.min(taxable, hi) - lo) * rate;
          }
          var diff = withheld - tax;
          out.textContent = (diff >= 0 ? '$' + Math.round(diff).toLocaleString() + ' refund' : '$' + Math.round(-diff).toLocaleString() + ' owed') + ' (est. tax: $' + Math.round(tax).toLocaleString() + ')';
        """,
    },
    {
        "slug": "property-tax-estimate",
        "category": "Taxes",
        "title": "Property tax calculator",
        "summary": "Estimate your annual property tax bill from your home's value and your local effective tax rate.",
        "note": "Effective property tax rates vary widely by state and county (roughly 0.3% to over 2% of home "
                "value annually) — rather than guess at your specific location, enter your county assessor's "
                "published rate or last year's bill divided by your home's assessed value.",
        "fields": [
            {"id": "value", "label": "Home value ($)", "placeholder": "450000"},
            {"id": "rate", "label": "Your local effective property tax rate (%)", "placeholder": "1.1"},
        ],
        "result_label": "Estimated annual property tax",
        "js": """
          var value = parseFloat(f.value.value) || 0;
          var rate = (parseFloat(f.rate.value) || 0) / 100;
          var annual = value * rate;
          out.textContent = '$' + Math.round(annual).toLocaleString() + '/yr ($' + Math.round(annual / 12).toLocaleString() + '/mo)';
        """,
    },
    {
        "slug": "financial-advisor-value",
        "category": "Retirement",
        "title": "Financial advisor value calculator",
        "summary": "Explore a purely hypothetical return uplift and what that kind of difference could mean in dollars over time. An illustration only, not proof or a promise of advisor value.",
        "note": "Research such as Vanguard's “Advisor's Alpha” studies suggests professional guidance "
                "(rebalancing, tax-aware withdrawals, behavioral coaching) can add measurable value over time, but "
                "the amount varies enormously by household and isn't guaranteed — so this uses your own "
                "assumed added-value percentage rather than asserting a specific figure for your situation.",
        "fields": [
            {"id": "bal", "label": "Current portfolio value ($)", "placeholder": "500000"},
            {"id": "yrs", "label": "Years until retirement", "placeholder": "20"},
            {"id": "base", "label": "Assumed annual return on your own (%)", "placeholder": "6"},
            {"id": "added", "label": "Assumed added value from guidance (percentage points/yr)", "placeholder": "1.5"},
        ],
        "result_label": "Illustrative difference at retirement",
        "js": """
          var bal = parseFloat(f.bal.value) || 0;
          var yrs = parseFloat(f.yrs.value) || 0;
          var base = (parseFloat(f.base.value) || 0) / 100;
          var added = (parseFloat(f.added.value) || 0) / 100;
          var fvBase = bal * Math.pow(1 + base, yrs);
          var fvGuided = bal * Math.pow(1 + base + added, yrs);
          out.textContent = '$' + Math.round(fvGuided - fvBase).toLocaleString() + ' more (illustrative: $' + Math.round(fvBase).toLocaleString() + ' vs $' + Math.round(fvGuided).toLocaleString() + ')';
        """,
    },
    {
        "slug": "401k-growth",
        "category": "Retirement",
        "title": "401(k) growth calculator",
        "summary": "Project your 401(k) balance including your contributions and employer match.",
        "note": "Compound growth on your contributions plus employer match, at a constant assumed return. Doesn't "
                "account for the 2026 IRS contribution limit, fees, or changes in salary — see our 401(k) "
                "contribution limit calculator for this year's cap.",
        "fields": [
            {"id": "bal", "label": "Current 401(k) balance ($)", "placeholder": "60000"},
            {"id": "salary", "label": "Annual salary ($)", "placeholder": "90000"},
            {"id": "contrib", "label": "Your contribution (% of salary)", "placeholder": "8"},
            {"id": "match", "label": "Employer match (% of salary)", "placeholder": "4"},
            {"id": "yrs", "label": "Years until retirement", "placeholder": "25"},
            {"id": "ret", "label": "Assumed annual return (%)", "placeholder": "7"},
        ],
        "result_label": "Estimated balance at retirement",
        "js": """
          var bal = parseFloat(f.bal.value) || 0;
          var salary = parseFloat(f.salary.value) || 0;
          var contribPct = (parseFloat(f.contrib.value) || 0) / 100;
          var matchPct = (parseFloat(f.match.value) || 0) / 100;
          var yrs = parseFloat(f.yrs.value) || 0;
          var ret = (parseFloat(f.ret.value) || 0) / 100;
          var monthly = salary * (contribPct + matchPct) / 12;
          var n = yrs * 12, r = ret / 12;
          var fvLump = bal * Math.pow(1 + r, n);
          var fvContrib = r > 0 ? monthly * ((Math.pow(1 + r, n) - 1) / r) : monthly * n;
          out.textContent = '$' + Math.round(fvLump + fvContrib).toLocaleString();
        """,
    },
    {
        "slug": "asset-allocation-guide",
        "category": "Investing",
        "title": "Asset allocation calculator",
        "summary": "A common age-based rule of thumb for a starting stock/bond split, adjusted for your risk tolerance.",
        "note": "Based on the widely-cited “110 minus your age” heuristic for a starting stock allocation, "
                "adjusted ±10 percentage points for stated risk tolerance. This is a rough starting point, not "
                "personalized advice — your actual allocation should reflect your full financial picture, time "
                "horizon, and goals.",
        "fields": [
            {"id": "age", "label": "Your age", "placeholder": "40"},
            {"id": "risk", "label": "Risk tolerance", "type": "select", "options": ["Conservative", "Moderate", "Aggressive"]},
        ],
        "result_label": "Illustrative stock / bond split",
        "js": """
          var age = parseFloat(f.age.value) || 0;
          var adj = f.risk.value === 'Conservative' ? -10 : (f.risk.value === 'Aggressive' ? 10 : 0);
          var stock = Math.max(0, Math.min(100, (110 - age) + adj));
          out.textContent = Math.round(stock) + '% stocks / ' + Math.round(100 - stock) + '% bonds';
        """,
    },
    {
        "slug": "mortgage-calculator",
        "category": "Home & Mortgage",
        "title": "Mortgage calculator",
        "summary": "Estimate your monthly mortgage principal & interest payment.",
        "note": "Standard amortization formula on principal and interest only — doesn't include property tax, "
                "homeowners insurance, PMI, or HOA dues, which typically add several hundred dollars a month.",
        "fields": [
            {"id": "price", "label": "Home price ($)", "placeholder": "450000"},
            {"id": "down", "label": "Down payment ($)", "placeholder": "90000"},
            {"id": "rate", "label": "Interest rate (%)", "placeholder": "6.5"},
            {"id": "term", "label": "Loan term", "type": "select", "options": ["30 years", "15 years"]},
        ],
        "result_label": "Estimated monthly payment (P&I)",
        "js": """
          var price = parseFloat(f.price.value) || 0;
          var down = parseFloat(f.down.value) || 0;
          var principal = Math.max(0, price - down);
          var rate = (parseFloat(f.rate.value) || 0) / 100 / 12;
          var years = f.term.value.indexOf('15') === 0 ? 15 : 30;
          var n = years * 12;
          var pmt = rate > 0 ? principal * rate * Math.pow(1 + rate, n) / (Math.pow(1 + rate, n) - 1) : principal / n;
          out.textContent = '$' + Math.round(pmt).toLocaleString() + '/mo';
        """,
    },
    {
        "slug": "home-affordability",
        "category": "Home & Mortgage",
        "title": "Home affordability calculator",
        "summary": "Estimate how much home you can afford using a standard 36% debt-to-income guideline.",
        "note": "Uses the common 36% total-debt-to-income guideline lenders often use as a starting point, minus "
                "your existing monthly debts, to estimate a maximum monthly housing payment — then backs into "
                "a loan amount. Actual lending limits depend on your credit, the lender, and loan program.",
        "fields": [
            {"id": "income", "label": "Annual household income ($)", "placeholder": "120000"},
            {"id": "debt", "label": "Existing monthly debt payments ($)", "placeholder": "400"},
            {"id": "down", "label": "Down payment available ($)", "placeholder": "60000"},
            {"id": "rate", "label": "Interest rate (%)", "placeholder": "6.5"},
        ],
        "result_label": "Estimated affordable home price",
        "js": """
          var income = parseFloat(f.income.value) || 0;
          var debt = parseFloat(f.debt.value) || 0;
          var down = parseFloat(f.down.value) || 0;
          var rate = (parseFloat(f.rate.value) || 0) / 100 / 12;
          var maxMonthly = Math.max(0, income / 12 * 0.36 - debt);
          var n = 30 * 12;
          var loan = rate > 0 ? maxMonthly * (Math.pow(1 + rate, n) - 1) / (rate * Math.pow(1 + rate, n)) : maxMonthly * n;
          out.textContent = '$' + Math.round(loan + down).toLocaleString() + ' (loan: $' + Math.round(loan).toLocaleString() + ' + down: $' + Math.round(down).toLocaleString() + ')';
        """,
    },
    {
        "slug": "closing-costs-estimate",
        "category": "Home & Mortgage",
        "title": "Closing costs calculator",
        "summary": "Estimate total closing costs and cash needed at signing.",
        "note": "Closing costs typically run about 2–5% of the purchase price (title, lender fees, escrow, "
                "recording, etc.), varying by state and lender — adjust the rate below to a quote from your "
                "lender or title company once you have one.",
        "fields": [
            {"id": "price", "label": "Home purchase price ($)", "placeholder": "450000"},
            {"id": "down", "label": "Down payment ($)", "placeholder": "90000"},
            {"id": "rate", "label": "Estimated closing cost rate (%)", "placeholder": "3"},
        ],
        "result_label": "Estimated cash needed at signing",
        "js": """
          var price = parseFloat(f.price.value) || 0;
          var down = parseFloat(f.down.value) || 0;
          var rate = (parseFloat(f.rate.value) || 0) / 100;
          var closing = price * rate;
          out.textContent = '$' + Math.round(closing + down).toLocaleString() + ' (down: $' + Math.round(down).toLocaleString() + ' + closing costs: $' + Math.round(closing).toLocaleString() + ')';
        """,
    },
    {
        "slug": "refinance-savings",
        "category": "Home & Mortgage",
        "title": "Refinance calculator",
        "summary": "Compare your current mortgage payment to a refinanced one at a new rate and term.",
        "note": "Compares principal & interest only, using standard amortization — doesn't include refinance "
                "closing costs, which typically take a few years of monthly savings to recoup.",
        "fields": [
            {"id": "bal", "label": "Current loan balance ($)", "placeholder": "350000"},
            {"id": "curRate", "label": "Current interest rate (%)", "placeholder": "7.2"},
            {"id": "curTerm", "label": "Current remaining term (years)", "placeholder": "27"},
            {"id": "newRate", "label": "New interest rate (%)", "placeholder": "6.2"},
            {"id": "newTerm", "label": "New loan term (years)", "placeholder": "30"},
        ],
        "result_label": "Estimated monthly savings",
        "js": """
          var bal = parseFloat(f.bal.value) || 0;
          function pmt(p, r, n) { r = r / 100 / 12; return r > 0 ? p * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1) : p / n; }
          var curPmt = pmt(bal, parseFloat(f.curRate.value) || 0, (parseFloat(f.curTerm.value) || 0) * 12);
          var newPmt = pmt(bal, parseFloat(f.newRate.value) || 0, (parseFloat(f.newTerm.value) || 0) * 12);
          var diff = curPmt - newPmt;
          out.textContent = (diff >= 0 ? '$' + Math.round(diff).toLocaleString() + '/mo saved' : '$' + Math.round(-diff).toLocaleString() + '/mo more') + ' (new payment: $' + Math.round(newPmt).toLocaleString() + '/mo)';
        """,
    },
]

CALCULATOR_GUIDES = {
    "roth-ira-growth": '<div class="insights-article" style="margin-top:clamp(40px,6vw,72px);max-width:68ch;">\n<h2>What this Roth IRA estimate means</h2>\n<p>The result is a hypothetical ending balance, not a prediction, tax calculation, or check that you may contribute the amount entered. It grows your current balance once per year at your chosen return, then adds your hypothetical contribution at the end of that year. Use it to compare what happens when you change the years, contributions or return, not to decide what the IRS permits.</p>\n<h2>How we calculate it</h2>\n<p>For each whole year: new balance = old balance × (1 + assumed annual return) + hypothetical annual contribution. Contributions arrive at year-end. The same rate applies every year. A negative return above -100% is allowed, but the estimate never models the uneven sequence of real market returns.</p>\n<p><strong>Worked example:</strong> Start with $10,000, add a hypothetical $5,000 at each year-end, and assume 6% a year for 20 years. This model ends near $216,000. The $110,000 total put in ($10,000 starting balance + $100,000 later contributions) accounts for part of that amount; roughly $106,000 is modeled growth. Neither number is guaranteed.</p>\n<h2>What to check before contributing</h2>\n<ul>\n<li>The entered amount is hypothetical even if it exceeds the current annual IRA cap. This page does not reject over-limit inputs or authorize contributions.</li>\n<li>For tax year 2026, the combined traditional and Roth IRA limit is generally $7,500 ($8,600 for people age 50 or older), or taxable compensation if lower. If you file jointly, the spousal IRA rule may allow a contribution using your spouse\'s compensation, subject to the joint-return rules and each spouse\'s separate IRA.</li>\n<li>Roth IRA eligibility can phase out with modified adjusted gross income and filing status. Other IRA contributions use the same annual cap; future limits may differ over a projection of many years. Check the rules for the actual tax year and your own circumstances before contributing.</li>\n</ul>\n<p>This model leaves out fees, inflation, varying returns, taxes on conversions, and distribution rules. It does not tell you whether a withdrawal would be qualified. See the <a href="https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-ira-contribution-limits">IRS contribution limits and spousal IRA guidance</a> and the <a href="https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500">IRS 2026 limit announcement</a>. Ask a tax professional about eligibility and withdrawals.</p>\n<div class="faq"><h2 class="faq__title">Roth IRA growth questions</h2>\n<details class="faq__item"><summary>Does the calculator check my Roth IRA contribution eligibility?</summary><p>No. It models a hypothetical amount. Income phaseouts, compensation, filing status, other IRA contributions, and future-year rules are not calculated.</p></details>\n<details class="faq__item"><summary>Why does it add the contribution after growth?</summary><p>The example assumes each year\'s contribution arrives at year-end. Contributions made earlier may have more time to grow, so a different contribution schedule would produce another result.</p></details>\n<details class="faq__item"><summary>Is this the same as a Roth conversion calculator?</summary><p>No. A conversion moves money from an existing account and can create a tax bill. This estimate models a current Roth IRA balance plus hypothetical new annual contributions, without conversion taxes.</p></details>\n</div></div>',
    "compound-interest": '<div class="insights-article" style="margin-top:clamp(40px,6vw,72px);max-width:68ch;">\n<h2>What compound interest can show you</h2>\n<p>The result estimates how a starting balance and regular monthly additions could grow if the same nominal annual rate held for the entire period. It is an illustration of compounding, not a quoted bank yield or an investment forecast. Change one input at a time to see which assumption drives your estimate.</p>\n<h2>How this calculation works</h2>\n<p>Each month, the model multiplies the balance by (1 + nominal annual rate / 12), then adds the monthly deposit at month-end. It repeats for the rounded number of months in the period. At 0% interest, the result is simply your starting balance plus your monthly additions.</p>\n<p><strong>Worked example:</strong> Start with $10,000, add $300 at the end of each month for 10 years, and assume a 5% nominal annual rate compounded monthly. The model ends near $63,055. You put in $46,000 ($10,000 + 120 × $300); about $17,055 is modeled interest. Actual returns or rates may differ.</p>\n<h2>Nominal rate is not APY</h2>\n<p>Enter a <strong>nominal annual rate</strong>, which this calculator divides by 12 before monthly compounding. A bank\'s <strong>annual percentage yield (APY)</strong> already includes the effect of its compounding schedule. Entering that APY as the nominal rate would double-count some compounding. Check the account\'s rate disclosure and compounding terms when comparing real products. The <a href="https://www.consumerfinance.gov/rules-policy/regulations/1030/2">CFPB definitions</a> distinguish the stated interest rate from APY.</p>\n<p>This model omits fees, taxes, inflation, rate changes, and differences in deposit timing. For investments, returns can be negative and do not arrive evenly each month. A larger modeled ending balance is not a reason by itself to choose an account or investment; compare liquidity, risk, costs and the actual terms.</p>\n<div class="faq"><h2 class="faq__title">Compound interest questions</h2>\n<details class="faq__item"><summary>What happens if the annual rate is zero?</summary><p>The account does not grow from interest. The result is the starting balance plus the monthly additions for the modeled period.</p></details>\n<details class="faq__item"><summary>Are monthly deposits added before or after interest?</summary><p>After each month\'s modeled interest. Deposits made at the beginning of a month would have more time to earn interest.</p></details>\n<details class="faq__item"><summary>Can I enter a savings account APY?</summary><p>Not directly. This tool expects a nominal annual rate and compounds it monthly; APY already reflects compounding. Check the account\'s quoted rate and terms instead of treating the two as interchangeable.</p></details>\n</div></div>'
}
for calculator in CALCULATORS:
    if calculator["slug"] in CALCULATOR_GUIDES:
        calculator["guide_html"] = CALCULATOR_GUIDES[calculator["slug"]]

CATEGORIES = ["Retirement", "Taxes", "Social Security", "Equity Compensation", "Investing", "Banking", "Home & Mortgage"]


def _field_html(slug, f):
    if f.get("type") == "select":
        opts = "".join(f"<option>{escape(o)}</option>" for o in f["options"])
        return f"""
        <div class="field" data-field>
          <label for="{slug}-{f['id']}">{escape(f['label'])}</label>
          <select id="{slug}-{f['id']}" name="{f['id']}">{opts}</select>
        </div>"""
    ph = f.get("placeholder", "")
    bounds = "".join(f' {key}="{escape(str(f[key]))}"' for key in ("min", "max") if key in f)
    return f"""
        <div class="field" data-field>
          <label for="{slug}-{f['id']}">{escape(f['label'])}</label>
          <input id="{slug}-{f['id']}" name="{f['id']}" type="number" inputmode="decimal"{bounds} placeholder="{escape(ph)}" value="{escape(ph)}">
        </div>"""


def _calc_body(c):
    fields = "\n".join(_field_html(c["slug"], f) for f in c["fields"])
    related = (f'<p style="margin-top:14px;"><a href="{escape(c["related"])}">Read the related article &rarr;</a></p>'
               if c.get("related") else "")
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:680px;">
    <a href="/#insights" class="btn btn--outline" style="margin-bottom:32px;">&larr; Back</a>
    <p class="eyebrow reveal">{escape(c.get('eyebrow') or (c['category'] + ' calculator'))}</p>
    <h1 class="display display--lg reveal">{escape(c['title'])}</h1>
    <p class="reveal" style="margin-top:14px; color:var(--ink-soft); max-width:56ch;">{escape(c['summary'])}</p>

    <form id="calcForm" class="form" style="margin-top:36px; grid-template-columns:1fr 1fr;" onsubmit="return false;">
      {fields}
    </form>

    <div class="calc-result">
      <p class="calc-result__label">{escape(c['result_label'])}</p>
      <p class="calc-result__value" id="calcOut">&mdash;</p>
    </div>

    <p style="margin-top:24px; font-size:.82rem; color:var(--muted); max-width:60ch;">{escape(c['note'])}</p>
    {related}
    {c.get('guide_html', '')}
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


def _hub_body():
    sections = "\n".join(
        f"<section><h2>{escape(category)}</h2><p><a href=\"/calculators/{escape(_category_slug(category))}/\">All {escape(category.lower())} calculators &rarr;</a></p>"
        + '<div class="adv-blog__grid" style="margin-top:24px;">'
        + "\n".join(
            f'<a class="blogcard reveal" href="/calculators/{escape(c["slug"])}/">'
            f'<h3>{escape(c["title"])}</h3><p>{escape(c["summary"])}</p>'
            '<span class="blogcard__link">Open calculator &rarr;</span></a>'
            for c in CALCULATORS if c["category"] == category and not c.get("noindex")
        ) + "</div></section>" for category in CATEGORIES
    )
    return f"""
<section class="section section--paper" id="top">
  <div class="container">
    <p class="eyebrow reveal">Tools</p>
    <h1 class="display display--lg reveal">Financial calculators</h1>
    <p class="reveal" style="margin-top:14px; color:var(--ink-soft); max-width:56ch;">Explore simple estimates by topic. Results are educational, not personalized advice.</p>
    {sections}
  </div>
</section>
{contact_section()}
"""


def build_calculator_pages(write_fn):
    write_fn("/calculators/", page(
        head(f"Financial Calculators | {BRAND}",
             "Financial calculators for retirement, taxes, Social Security, equity compensation, investing, and banking.",
             path="/calculators/"),
        _hub_body(), with_gate=True))
    for c in CALCULATORS:
        schema = faq_schema([(f"How is the {c['title'].lower()} calculated?", c["note"])])
        html = page(
            head(f"{c['title']} | {BRAND}", c["summary"], path=f"/calculators/{c['slug']}/", schema=schema,
                 noindex=c.get("noindex", False)),
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
