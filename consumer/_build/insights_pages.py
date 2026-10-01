# -*- coding: utf-8 -*-
"""Real /insights/[slug]/ articles.

Byline: Bhavya Barot — the same real, accountable name already publishing
financial-education content at blog.valorahq.com (a live Ghost blog, not a
placeholder). Every article here is general education, not personalized
advice: no specific numeric recommendations, consistent with the site's own
footer disclaimer that Valora provides financial education and does not
provide investment, tax, legal, or financial advice. Each ends by pointing
the reader to talk with an advisor about their own situation.
"""
from html import escape

from partials import page, head, BRAND, SITE_URL, contact_section, EMAIL, article_schema

AUTHOR = "Bhavya Barot"
PUBLISHED = "2026-09-28"

ARTICLES = [
    {
        "slug": "realistic-withdrawal-rate-today",
        "category": "Retirement income",
        "read": "6 min read",
        "image": "https://images.unsplash.com/photo-1554224154-26032ffc0d07?auto=format&fit=crop&w=1600&q=80",
        "title": "What a realistic withdrawal rate looks like now",
        "summary": "The 4% rule is a 1990s starting point, not a guarantee. Here's what actually moves the number for a given retirement.",
        "body": [
            "The “4% rule” comes from a 1994 study by financial planner William Bengen, who "
            "tested historical U.S. market returns to find a withdrawal rate a 30-year retirement "
            "portfolio could survive. It's a useful starting heuristic, not a rule in the sense of a "
            "guarantee — it was built on one country's historical returns over one set of decades, "
            "and nothing requires the future to look like that.",
            "A handful of things move the number for any specific retirement, and they push in "
            "different directions:",
            "<ul><li><strong>Time horizon.</strong> A 30-year retirement supports a lower withdrawal "
            "rate than a 15-year one. Retiring earlier, or simply living longer than average, means "
            "the money has to last longer.</li>"
            "<li><strong>Portfolio mix.</strong> Bengen's original work assumed a 50/50 stock-and-bond "
            "split. A more conservative or more aggressive mix changes both the safe withdrawal rate "
            "and how much the balance swings year to year.</li>"
            "<li><strong>Spending flexibility.</strong> A retiree who can cut discretionary spending "
            "in a down market — skip the big trip, delay the renovation — can often sustain a "
            "higher starting rate than someone with fixed, inflexible expenses.</li>"
            "<li><strong>Sequence-of-returns risk.</strong> Two retirees with identical average returns "
            "over 30 years can end up in very different places if one retires into a market downturn "
            "and the other doesn't. The order returns arrive in matters as much as the average.</li>"
            "<li><strong>Other income.</strong> Social Security, a pension, or rental income reduces how "
            "much a portfolio needs to cover on its own, which changes what withdrawal rate from "
            "savings actually means for that household.</li></ul>",
            "None of this produces a single correct percentage — it's why “what's a safe "
            "withdrawal rate” is really several smaller questions about a specific household's "
            "time horizon, portfolio, flexibility, and other income. That's a conversation worth having "
            "with a fiduciary advisor who can model it against your actual numbers, not a generic rule "
            "of thumb.",
        ],
    },
    {
        "slug": "family-conversation-before-retirement",
        "category": "Family",
        "read": "5 min read",
        "image": "https://images.unsplash.com/photo-1758691031787-90867cb6fb2c?auto=format&fit=crop&w=1600&q=80",
        "title": "The conversation every family should have before retirement",
        "summary": "The hardest part of retirement planning usually isn't the math. It's the conversation nobody's scheduled yet.",
        "body": [
            "Most retirement planning focuses on numbers: how much is saved, what it can generate, "
            "when to claim Social Security. Just as much depends on conversations that never get "
            "explicitly scheduled — and tend to happen at the worst possible time, during a health "
            "crisis or after a death, instead of calmly in advance.",
            "A few worth having early, on purpose:",
            "<ul><li><strong>What does “retirement” actually look like day to day?</strong> "
            "Spouses sometimes discover they pictured very different things — relocating vs. staying "
            "put, traveling constantly vs. settling into routine — only after one of them has already "
            "made plans around it.</li>"
            "<li><strong>Who has access to what?</strong> Account logins, safe deposit box locations, "
            "where the estate documents are physically kept — the people who'd need this information "
            "in an emergency should have it before the emergency, not after.</li>"
            "<li><strong>What are the wishes around aging and long-term care?</strong> Where someone "
            "would want to live if they needed help, and who they'd want making decisions if they "
            "couldn't — this is far easier to say out loud calmly than to guess at later.</li>"
            "<li><strong>What do adult children expect, and what do parents intend?</strong> Assumptions "
            "on both sides about inheritance, a family business, or a home are a common source of "
            "conflict specifically because they were never said out loud.</li></ul>",
            "None of these conversations require having everything figured out first. They just require "
            "having them before circumstances force the issue. Many advisors are used to helping "
            "facilitate exactly this kind of family conversation, not just running the numbers.",
        ],
    },
    {
        "slug": "when-roth-conversion-worth-tax-bill",
        "category": "Taxes",
        "read": "6 min read",
        "image": None,
        "title": "When a Roth conversion is worth the tax bill",
        "summary": "A Roth conversion means paying tax now, on purpose, to avoid a possibly larger tax bill later. Whether that trade is worth it depends entirely on the specifics.",
        "body": [
            "A Roth conversion moves money from a traditional (pre-tax) retirement account into a Roth "
            "account, and the amount converted is taxed as ordinary income in the year of the "
            "conversion. In exchange, that money — and everything it earns afterward — can "
            "generally be withdrawn tax-free in retirement. It's a trade: a known tax cost today for "
            "the possibility of a lower total tax bill over time.",
            "Whether that trade makes sense depends on specifics, not a general rule. A few situations "
            "where advisors commonly discuss it:",
            "<ul><li><strong>A low-income year.</strong> Between jobs, in early retirement before "
            "Social Security starts, or any year with unusually low taxable income, converting can mean "
            "paying tax at a lower bracket than usual.</li>"
            "<li><strong>Before Required Minimum Distributions start.</strong> Traditional accounts "
            "eventually force taxable withdrawals whether the money is needed or not. Converting some "
            "of the balance earlier can reduce those forced future withdrawals.</li>"
            "<li><strong>Leaving money to heirs.</strong> Since the SECURE Act generally requires most "
            "non-spouse heirs to empty an inherited retirement account within 10 years, a Roth balance "
            "can mean that decade of withdrawals is tax-free for them instead of taxable.</li>"
            "<li><strong>Expecting tax rates to rise — for you or in general.</strong> If future "
            "rates are likely to be higher than the rate paid on the conversion, paying tax now can come "
            "out ahead. This is a genuine unknown, not something anyone can predict with confidence.</li></ul>",
            "The conversion itself is also a decision with real, immediate costs — the tax bill is "
            "due for the year of the conversion, ideally paid from money outside the retirement account, "
            "and converting too much in one year can push income into a higher bracket or trigger other "
            "effects (like higher Medicare premiums) than intended. This is genuinely a case-by-case "
            "calculation, and it's worth running by both a financial advisor and a CPA before acting on it.",
        ],
    },
    {
        "slug": "rsus-bonus-not-lottery-ticket",
        "category": "Equity comp",
        "read": "5 min read",
        "image": None,
        "title": "Your RSUs are a bonus, not a lottery ticket",
        "summary": "Restricted stock units are taxed like a cash bonus, not like a windfall — and treating them that way changes what you do next.",
        "body": [
            "Restricted stock units (RSUs) are shares a company grants an employee that convert to "
            "actual stock over time, usually on a vesting schedule. When shares vest, their value on "
            "that date is taxed as ordinary income — the same category as salary — whether or "
            "not the shares are sold.",
            "A few practical consequences follow from that:",
            "<ul><li><strong>Default withholding often falls short.</strong> Many employers withhold "
            "a flat 22% federal rate on vested RSUs, which is lower than the marginal rate many "
            "employees actually owe once salary is added in. That gap shows up as a tax bill at filing "
            "time if it isn't planned for.</li>"
            "<li><strong>Vesting is a paycheck, not a jackpot.</strong> Because RSU income is taxed the "
            "same way a cash bonus would be, a useful mental model is to treat vested shares as "
            "already-taxed compensation that happens to be sitting in stock — not as a separate "
            "windfall to speculate with.</li>"
            "<li><strong>Concentration is a real, quantifiable risk.</strong> An employee holding a "
            "large position in their own employer's stock is exposed to that single company's fortunes "
            "twice over: through their paycheck and through their portfolio. Diversifying out of vested "
            "shares over time is a standard way advisors address this, distinct from any view on "
            "whether the stock itself is a good investment.</li></ul>",
            "None of this is a reason to avoid equity compensation — it's real compensation, and "
            "often a meaningful part of total pay. It's a reason to plan for the tax bill in advance and "
            "decide deliberately what to do with vested shares, rather than by default. An advisor who "
            "works with equity compensation regularly can help model the actual tax exposure against a "
            "specific vesting schedule.",
        ],
    },
    {
        "slug": "market-drop-before-retirement",
        "category": "Markets",
        "read": "5 min read",
        "image": None,
        "title": "What happens if the market drops right before you retire",
        "summary": "Two retirees with identical average returns over 30 years can end up in very different places, depending only on the order those returns arrive in.",
        "body": [
            "This is called sequence-of-returns risk, and it's one of the more counterintuitive facts "
            "in retirement planning: the average return a portfolio earns over a retirement matters "
            "less than the order those returns show up in — specifically, what happens in the "
            "first few years after someone starts withdrawing money.",
            "The reason is mechanical. Someone who is still adding money to a portfolio benefits from a "
            "downturn early on — they're buying more shares at lower prices. Someone who has started "
            "withdrawing money does the opposite: selling shares in a downturn to fund living expenses "
            "locks in losses and leaves fewer shares left to recover when the market eventually does. A "
            "downturn in year one or two of retirement can do lasting damage that the identical downturn "
            "in year twenty would not.",
            "A few approaches advisors commonly discuss to manage this, without eliminating the risk "
            "entirely:",
            "<ul><li><strong>A cash or short-term bond buffer.</strong> Holding one to a few years of "
            "expenses in something that doesn't fluctuate with the stock market means a downturn doesn't "
            "force selling stock at a low point — spending can come from the buffer instead while "
            "the portfolio recovers.</li>"
            "<li><strong>Flexible spending.</strong> Retirees who can reduce discretionary spending in a "
            "down year — rather than withdrawing a fixed amount regardless of market conditions "
            "— reduce how much damage a bad sequence can do.</li>"
            "<li><strong>Adjusting the glide path into retirement.</strong> Some advisors reduce equity "
            "exposure in the years immediately before and after retirement specifically to reduce this "
            "risk, then increase it again later.</li></ul>",
            "There's no way to know in advance whether a downturn will happen to land in the first years "
            "of a specific retirement — that's the nature of the risk. What's controllable is having "
            "a plan for that scenario in place before it happens, which is a core part of what a "
            "retirement income plan is for.",
        ],
    },
    {
        "slug": "beneficiary-forms-override-will",
        "category": "Estate",
        "read": "4 min read",
        "image": None,
        "title": "Beneficiary forms quietly override your will",
        "summary": "For many retirement accounts, life insurance, and bank accounts, the beneficiary form usually decides who gets the money, not the will. Spouse-consent rules, community-property laws, and plan terms can override the form.",
        "body": [
            "A will governs the distribution of assets that go through probate. Many common assets, "
            "though, pass directly to whoever is named on a beneficiary designation form, regardless of "
            "what a will says — including 401(k)s and IRAs, life insurance policies, and any account "
            "set up as “payable on death” or “transfer on death.”",
            "This creates a specific, well-documented failure mode: someone updates their will — "
            "after a divorce, a remarriage, a new child — but never goes back and updates the "
            "beneficiary forms on their retirement accounts or life insurance, which were filled out "
            "years earlier and quietly still name an ex-spouse, or don't include a child born since. "
            "When the account holder dies, the beneficiary form wins, not the more recently updated "
            "will.",
            "A few points worth knowing generally, with the caveat that specifics vary by state and "
            "account type and this isn't a substitute for an estate attorney's review:",
            "<ul><li><strong>Beneficiary designations should be checked after every major life event</strong> "
            "— marriage, divorce, a new child or grandchild, a death in the family — not just "
            "when the will itself is updated.</li>"
            "<li><strong>Naming a specific person is usually clearer than naming an estate.</strong> "
            "“My estate” as a beneficiary generally sends the asset through probate anyway, "
            "which is often exactly what a beneficiary designation is meant to avoid.</li>"
            "<li><strong>Contingent beneficiaries matter too.</strong> If a primary beneficiary has "
            "already died and no contingent beneficiary is named, the asset can end up in probate by "
            "default.</li></ul>",
            "This is a genuinely easy thing to get right — most account providers let you review "
            "and update beneficiaries in a few minutes online — and a genuinely common thing to get "
            "wrong simply by never revisiting it. It's worth checking every few years, or after any of "
            "the life events above, and worth reviewing with an estate attorney or advisor as part of a "
            "broader estate plan.",
        ],
    },
]


def _article_body(a):
    paras = "\n".join(f"      <p>{p}</p>" for p in a["body"])
    img = f'<img src="{escape(a["image"])}" alt="" style="width:100%; border-radius:6px; margin-bottom:32px;">' if a["image"] else ""
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:700px;">
    <a href="/#insights" class="btn btn--outline" style="margin-bottom:32px;">&larr; All insights</a>
    <p class="post__meta">{escape(a['category'])} &middot; {escape(a['read'])}</p>
    <h1 class="display display--lg" style="margin-top:8px;">{escape(a['title'])}</h1>
    <p style="margin:16px 0 32px; color:var(--muted); font-size:.86rem;">By {escape(AUTHOR)} &middot; {PUBLISHED}</p>
    {img}
    <div class="insights-article">
{paras}
    </div>
  </div>
</section>

{contact_section()}
"""


def build_insights_pages(write_fn):
    for a in ARTICLES:
        url = f"{SITE_URL}/insights/{a['slug']}/"
        schema = article_schema(
            headline=a["title"],
            description=a["summary"],
            url=url,
            date_published=PUBLISHED,
            author_name=AUTHOR,
            image=a["image"],
        )
        html = page(
            head(f"{a['title']} | {BRAND} Insights",
                 a["summary"],
                 path=f"/insights/{a['slug']}/",
                 schema=schema),
            _article_body(a),
            with_gate=True,
        )
        write_fn(f"/insights/{a['slug']}/", html)
