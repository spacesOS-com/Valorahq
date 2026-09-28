# -*- coding: utf-8 -*-
"""/find-your-advisor/ — the standalone consumer intake flow.

Routing decision (Sep 28, relayed by main): consumer page CTAs point HERE,
not to #contact. This page is the standalone version of the gate's stepped
match flow, with the founder's field spec: profession/niche, investable-assets
range, city, biggest question, then name/email capture.

Submissions ride the same Apps Script lead pipeline as every other lead form
(Google Sheet CRM row + email alert) through script.js's generic
[data-lead="Client"] handler — no new backend.

Pipeline notes:
- Founder decision (Sep 28, final): step 4 collects name + phone + email —
  matching the Apps Script validator, which requires all three.
- Trackability: CTAs link here with utm params; script.js (fyaSource) copies
  them into the hidden data-extra "Source" field, and collectLead folds
  data-extra fields into the note/message column — so every CRM row and
  email alert carries its origin page.
"""
from html import escape

from partials import page, head, ASSET_OPTIONS, SITUATION_OPTIONS

PROFESSION_OPTIONS = ["Physician", "Tech employee"] + SITUATION_OPTIONS


def _select(uid, name, label, options, wrap="field field--full"):
    opts = '<option value="">Select one</option>' + "".join(f"<option>{escape(o)}</option>" for o in options)
    return f"""<div class="{wrap}" data-field>
          <label for="{uid}{name}">{escape(label)}</label>
          <select id="{uid}{name}" name="{name}" required>{opts}</select>
          <small class="err" data-err="{name}"></small>
        </div>"""


def intake_form():
    return f"""<form class="form form--steps reveal" id="fyaForm" data-lead="Client" data-success="Thank you, {{name}} — we'll follow up within two business days with advisors who may fit what you're looking for." novalidate>
      <input type="hidden" id="fyaSource" data-extra="Source" value="">
      <div class="form__step" data-step>
        <p class="field field--full form__stepnum">Step 1 of 4</p>
        {_select("fy", "situation", "What best describes you?", PROFESSION_OPTIONS)}
        <div class="field field--full form__nav">
          <button class="btn btn--cream" type="button" data-step-next>Continue</button>
        </div>
      </div>
      <div class="form__step" data-step hidden>
        <p class="field field--full form__stepnum">Step 2 of 4</p>
        {_select("fy", "assets", "Approximately how much do you have in investable assets?", ASSET_OPTIONS)}
        <div class="field field--full" data-field>
          <label for="fylocation">Which city are you in?</label>
          <input id="fylocation" name="location" type="text" required placeholder="City, State" autocomplete="address-level2">
          <small class="err" data-err="location"></small>
        </div>
        <div class="field field--full form__nav">
          <button class="btn btn--outline" type="button" data-step-back>Back</button>
          <button class="btn btn--cream" type="button" data-step-next>Continue</button>
        </div>
      </div>
      <div class="form__step" data-step hidden>
        <p class="field field--full form__stepnum">Step 3 of 4</p>
        <div class="field field--full" data-field>
          <label for="fyquestion">What's your biggest money question right now?</label>
          <textarea id="fyquestion" name="question" rows="4" required placeholder="A sentence is plenty." data-extra="Biggest question"></textarea>
          <small class="err" data-err="question"></small>
        </div>
        <div class="field field--full form__nav">
          <button class="btn btn--outline" type="button" data-step-back>Back</button>
          <button class="btn btn--cream" type="button" data-step-next>Continue</button>
        </div>
      </div>
      <div class="form__step" data-step hidden>
        <p class="field field--full form__stepnum">Step 4 of 4 — where should advisors reach you?</p>
        <div class="field" data-field>
          <label for="fyname">Full name</label>
          <input id="fyname" name="name" type="text" required placeholder="Jordan Reyes" autocomplete="name">
          <small class="err" data-err="name"></small>
        </div>
        <div class="field" data-field>
          <label for="fyemail">Email</label>
          <input id="fyemail" name="email" type="email" required placeholder="jordan@email.com" autocomplete="email">
          <small class="err" data-err="email"></small>
        </div>
        <div class="field" data-field>
          <label for="fyphone">Phone number</label>
          <input id="fyphone" name="phone" type="tel" required placeholder="(415) 555-0100" autocomplete="tel" inputmode="tel">
          <small class="err" data-err="phone"></small>
        </div>
        <div class="field field--full form__foot">
          <button class="btn btn--outline" type="button" data-step-back>Back</button>
          <button class="btn btn--cream" type="submit">Find my advisor</button>
          <p class="form__fine"></p>
        </div>
      </div>
      <p class="form__success" role="status" hidden></p>
    </form>"""


def intake_body():
    return f"""
<section class="section section--paper" id="top">
  <div class="container" style="max-width:900px;">
    <p class="eyebrow reveal">Free · No obligation</p>
    <h1 class="display display--lg reveal">Find your advisor.</h1>
    <p class="reveal" style="margin-top:16px; color:var(--ink-soft); max-width:56ch;">Answer four quick questions and we'll match you with independent, fiduciary advisors who fit your situation.</p>
  </div>
</section>

<section class="section section--green cta" id="intake">
  <div class="container cta__grid">
    <div class="cta__copy">
      <h2 class="display display--lg reveal">Tell us what<br><em>you're solving for.</em></h2>
      <p class="reveal">A short conversation can show you which decisions deserve attention first.</p>
    </div>

    {intake_form()}
  </div>
</section>
"""


def build_intake_page(write_fn):
    html = page(
        head("Find Your Advisor | Valora",
             "Answer four quick questions and Valora will match you with independent, fiduciary financial advisors who fit your situation. Free, no obligation.",
             path="/find-your-advisor/"),
        intake_body(),
    )
    write_fn("/find-your-advisor/", html)
