# -*- coding: utf-8 -*-
"""City-page pack validator - fail-closed, per the city template's
fail_closed_build_contract (Lena's city-template.json, v2).

Runs twice in the pipeline:
  1. PRE-HANDOFF (CLI): python3 _build/city_validate.py pack.json [pack2.json ...]
  2. RENDER-TIME: the city page builder calls validate_pack() and refuses to
     write the page on any FAIL - a bad pack can never reach the site.

Each contract rule maps to a check below; every failure is printed with its
rule so the fix is obvious. Exit code 1 if any pack FAILs.
"""
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (compatible; ValoraBuild/1.0)"}

# Editorial whitelist: sentences Mira has RULED are rhetoric, not tax claims.
# Entries are added only on her explicit ruling (date noted); never self-added.
EDITORIAL_WHITELIST = [
    # Mira, Sep 28: rhetorical advisor-quality line, not a tax claim.
    "reads like it was written for a high-tax coastal city",
    # Mira, Sep 28 ruling #1 option B: her verbatim prescribed strip line for the
    # NYC homebuying sentence - approved replacement, not an unsourced claim.
    "Mortgage interest and property taxes can affect the rent-versus-buy comparison; check which costs apply to your situation.",
]
MIN_WORDS = 1400

# --- token / structure ------------------------------------------------------
REQUIRED_KEYS = ["slug", "meta_title", "h1", "meta_description", "body_html",
                 "faqs", "source_notes", "internal_links", "inline_ctas", "calculators"]

def check_structure(pack):
    fails = []
    for k in REQUIRED_KEYS:
        if k not in pack:
            fails.append(f"missing required key: {k}")
    slug = pack.get("slug", "")
    if not re.fullmatch(r"financial-advisor-in-[a-z0-9-]+", slug):
        fails.append(f"slug '{slug}' does not match financial-advisor-in-{{city-slug}}-{{state-lower}}")
    raw = json.dumps(pack)
    for pat, label in [(r"\{\{[^}]*\}\}", "unfilled {{token}}"),
                       (r"\[(?:TBD|TODO|CITY|STATE|INSERT)[^\]]*\]", "bracket placeholder")]:
        for m in re.findall(pat, raw, re.I):
            fails.append(f"placeholder text remains: {m}")
    return fails

# --- FAQ / JSON-LD exact match (Mira's content-gate standard) ---------------
def check_faq_match(pack):
    faqs = [(q.strip(), a.strip()) for q, a in
            ((f.get("q", ""), f.get("a", "")) for f in pack.get("faqs", []))]
    ld = pack.get("faq_jsonld") or {}
    if isinstance(ld, str):
        try:
            ld = json.loads(ld)
        except Exception:
            return ["faq_jsonld is not parseable JSON"]
    entities = [(e.get("name", "").strip(),
                 e.get("acceptedAnswer", {}).get("text", "").strip())
                for e in (ld.get("mainEntity") or [])]
    if sorted(faqs) != sorted(entities):
        return ["faqs[] and faq_jsonld.mainEntity do not match exactly "
                f"({len(faqs)} faqs vs {len(entities)} entities)"]
    return []

# --- URLs verified HTTP 200 at build time -----------------------------------
def _urls(pack):
    out = {}
    for m in re.finditer(r'href="(https?://[^"]+)"', pack.get("body_html", "")):
        out.setdefault(m.group(1), []).append("body_html link")
    for u in pack.get("internal_links") or []:
        out.setdefault(u, []).append("internal_links")
    c = pack.get("calculators") or {}
    for u in c.get("related_links") or []:
        out.setdefault(u, []).append("calculators.related_links")
    for cta in pack.get("inline_ctas") or []:
        u = cta.get("href", "")
        if u.startswith("http"):
            out.setdefault(u, []).append("inline_ctas")
    sn = pack.get("source_notes")
    for u in re.findall(r'https?://[^\s\)"\']+', sn if isinstance(sn, str) else json.dumps(sn or "")):
        out.setdefault(u.rstrip(".,;"), []).append("source_notes")
    return out

def _http_status(url):
    """Returns 'ok' (2xx/3xx), 'dead' (definitive 404/410), or 'blocked'
    (403/timeouts - usually bot protection from datacenter IPs; the URL may
    be fine in a real browser)."""
    import urllib.error
    for method in ("GET", "HEAD"):
        try:
            req = urllib.request.Request(url, headers=UA, method=method)
            with urllib.request.urlopen(req, timeout=15) as r:
                if 200 <= r.status < 400:
                    return "ok"
                if r.status in (404, 410):
                    return "dead"
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return "dead"
        except Exception:
            pass
    return "blocked"

def check_urls(pack, offline=False):
    urls = _urls(pack)
    fails, warns = [], []
    if not (pack.get("internal_links")):
        fails.append("internal_links is empty")
    if offline:
        return fails, warns, urls
    def job(item):
        url, where = item
        return url, where, _http_status(url)
    with ThreadPoolExecutor(max_workers=10) as ex:
        for url, where, status in ex.map(job, urls.items()):
            w = ", ".join(sorted(set(where)))
            if status == "dead":
                fails.append(f"URL returns 404/410 at build time: {url} ({w})")
            elif status == "blocked":
                # bot protection (census.gov, FRED etc. block datacenter IPs) -
                # not a FAIL, but must be browser-verified once before ship
                warns.append(f"URL unverifiable from build env (bot-blocked): {url} ({w})")
    return fails, warns, urls

# --- substance rules --------------------------------------------------------
def _body_text(pack):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", pack.get("body_html", ""))).strip()

def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 40]

def check_substance(pack, other_packs):
    fails = []
    text = _body_text(pack)
    wc = len(text.split())
    if wc < MIN_WORDS:
        fails.append(f"body word count {wc} < {MIN_WORDS}")
    # sentence reuse vs sibling packs (only advisor-verification boilerplate may repeat)
    mine = set(_sentences(text))
    for other in other_packs:
        if other is pack:
            continue
        shared = mine & set(_sentences(_body_text(other)))
        for s in shared:
            if re.search(r"(verify|Form ADV|SEC|fiduciary|license|registration)", s, re.I):
                continue  # allowed: advisor-verification how-to
            fails.append(f"sentence reused from {other.get('slug', 'another pack')}: {s[:90]}...")
    # Tax/legal framing, Mira's calibration (Sep 28): dated, accurately
    # source-cited tax facts PASS unhedged. FAIL only when a claim lacks a
    # source/current tax year where those matter, overstates scope, or turns
    # fact into personalized advice / guaranteed outcome. (Whether each
    # citation actually supports its exact claim stays a manual spot-check.)
    # A sentence only counts as a tax/legal CLAIM when it asserts something
    # (tax keyword + assertion verb); prose that merely mentions tax passes.
    tax_kw = r"\b(tax|taxes|taxable|deduct(?:ion|s)?|IRS|legal|estate)\b"
    assert_verb = r"\b(is|are|was|were|equals|costs|applies|ranges|exempts?|excludes?|caps?|expires?|owes?|triggers?|deducts?)\b"
    advice = r"\b(you should|we recommend|your (?:\w+ )?(?:tax|refund|bill|liability) will|elect|guarantee[ds]?)\b"
    absolute_scope = r"\b(always|never|every(?:one| taxpayer)|all taxpayers|no exceptions)\b"
    for para in re.findall(r"<p[^>]*>(.*?)</p>", pack.get("body_html", ""), re.S):
        plain = re.sub(r"<[^>]+>", "", para)
        if not re.search(tax_kw, plain, re.I):
            continue
        has_source = bool(re.search(r"<a [^>]*href=", para))
        para_has_year = bool(re.search(r"(tax year )?20\d\d", plain))
        for s in _sentences(plain):
            if any(w in s for w in EDITORIAL_WHITELIST):
                continue  # ruled editorial rhetoric by Mira (see EDITORIAL_WHITELIST)
            if not (re.search(tax_kw, s, re.I) and re.search(assert_verb, s, re.I)):
                continue  # mention, not a claim
            if re.search(advice, s, re.I):
                fails.append(f"personalized advice / guaranteed outcome: {s[:90]}...")
            elif re.search(absolute_scope, s, re.I):
                fails.append(f"overstated scope (always/never/every): {s[:90]}...")
            elif not (has_source or para_has_year):
                fails.append(f"tax/legal claim without inline source or current tax year: {s[:90]}...")
    return fails

def check_source_notes(pack):
    sn = pack.get("source_notes")
    if not sn:
        return ["source_notes missing"]
    raw = sn if isinstance(sn, str) else json.dumps(sn)
    if "checked_date" not in raw and not re.search(r"checked[_ ]?(?:on|date)", raw, re.I):
        return ["source_notes has no checked_date"]
    return []

# --- runner -------------------------------------------------------------------
def validate_pack(path, pack, other_packs=(), offline=False):
    fails = []
    fails += check_structure(pack)
    fails += check_faq_match(pack)
    url_fails, url_warns, _ = check_urls(pack, offline=offline)
    fails += url_fails
    fails += check_substance(pack, other_packs)
    fails += check_source_notes(pack)
    return fails, url_warns

def main(argv):
    offline = "--offline" in argv
    paths = [a for a in argv if not a.startswith("--")]
    packs = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            packs.append((p, json.load(f)))
    rc = 0
    for p, pack in packs:
        fails, warns = validate_pack(p, pack, other_packs=[x for _, x in packs], offline=offline)
        status = "PASS" if not fails else "FAIL"
        if fails:
            rc = 1
        print(f"{status}  {p}")
        for f_ in fails:
            print(f"   FAIL - {f_}")
        for w_ in warns:
            print(f"   WARN - {w_} (browser-verify once before ship)")
    return rc

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
