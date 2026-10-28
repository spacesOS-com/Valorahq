/* =========================================================
   NOTE (2026-09-28): re-homed under barot@valorahq.com. The
   previous web app + Sheet (1vWxHqtLPMb_RqE0rTuTyHWh_PJ5o7RkHx5Jyy2P3QCg)
   live in an unknown Google account (likely surgeaio/ndovu) - no
   access; its history (2 dev/test rows) is stranded there. Jay
   Boekeloo's 2026-09-21 row was migrated below via migrateLegacy().
   ========================================================= */
/* =========================================================
   Valora — lead form → Google Sheet + Notion CRM + emails
   v2 (2026-09-28): adds Timing column, lead auto-confirmation
   email (Marcus-approved verbatim copy), Notion CRM row via
   Script Properties (NOTION_TOKEN, NOTION_DB_ID — set in
   Project Settings ▸ Script Properties; no secrets in code).
   ========================================================= */

var SHEET_ID  = '170mJNZ9xscrm9xe026EqiG-PZg5d1N_2GckJRHdGDd0';
var SHEET_NAME = '';
var NOTIFY_TO  = 'barot@valorahq.com,brands@grow.surgeaio.com';
var HEADERS    = ['Name', 'Email', 'Phone Number', 'Solving For',
                  'Looking For Help With', 'Investable Assets', 'Situation',
                  'Location', 'Message', 'Timing', 'Confirmation'];
// Hidden field added to every lead form by assets/script.js. People never
// fill it; bots that fill every field do. Must match HONEYPOT there.
var HONEYPOT   = 'vl_contact_hp';

function doGet(e)  { return handleForm(e); }
function doPost(e) { return handleForm(e); }

function handleForm(e) {
  try {
    var params = (e && e.parameter) ? e.parameter : {};

    // Honeypot filled: answer exactly like a real success so the bot learns
    // nothing, but store nothing and send no email.
    if (str(params[HONEYPOT])) {
      console.log('Honeypot submission dropped');
      return json({ status: 'success', message: 'Lead captured' });
    }

    var name      = str(params.name);
    var email     = str(params.email);
    var phone     = str(params.phone);
    var solving   = str(params.goal || params.solving || params.service);
    var help      = str(params.help);
    var assets    = str(params.assets);
    var situation = str(params.situation);
    var location  = str(params.location);
    var timing    = str(params.timing);
    var message   = str(params.message || params.note);

    if (!name || !email || !phone) {
      return json({ status: 'error', message: 'Missing required fields' });
    }

    // No mail server for the domain (e.g. asdasd@ads.com): the confirmation
    // would only bounce and hurt our sender reputation, so skip it. The lead
    // is still recorded. If the lookup itself fails we send as before.
    var canReceive = domainAcceptsMail_(email);
    var confirmation = canReceive === false ? 'Suppressed: no mail server for the domain' : 'Sent';

    var sheet = getSheet();
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(HEADERS);
      sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
      sheet.setFrozenRows(1);
    } else if (!str(sheet.getRange(1, HEADERS.length).getValue())) {
      // Sheets created before the Confirmation column: add its header.
      sheet.getRange(1, HEADERS.length).setValue(HEADERS[HEADERS.length - 1]).setFontWeight('bold');
    }
    sheet.appendRow([name, email, phone, solving, help, assets, situation, location, message, timing, confirmation]);
    SpreadsheetApp.flush();

    var timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd/MM/yyyy HH:mm:ss');

    var lines = [
      'New Lead Received', '',
      'Name: ' + name, 'Email: ' + email, 'Phone Number: ' + phone
    ];
    if (solving)   lines.push('Solving For: ' + solving);
    if (help)      lines.push('Looking For Help With: ' + help);
    if (assets)    lines.push('Investable Assets: ' + assets);
    if (situation) lines.push('Situation: ' + situation);
    if (location)  lines.push('Location: ' + location);
    if (timing)    lines.push('Timing: ' + timing);
    lines.push('Message: ' + (message || '-'));
    lines.push('Confirmation email: ' + confirmation);
    lines.push('Time: ' + timestamp);
    GmailApp.sendEmail(NOTIFY_TO, 'Valora New Organic Lead - ' + name, lines.join('\n'));

    // Auto-confirmation to the lead (Marcus-approved verbatim body; from the
    // script owner's Gmail = barot@valorahq.com). No timing promises here -
    // the two-business-day line stays in the FAQ until the flow is verified.
    if (canReceive !== false) GmailApp.sendEmail(
      email,
      'We received your Valora request',
      'Hi ' + name.split(' ')[0] + ',\n\n' +
      'We received your request. We will review it by hand and email you about the next step. ' +
      'We will not introduce you to an advisor without your consent.\n\n' +
      '— The Valora team'
    );

    // Notion CRM row (best-effort; failure never blocks the lead)
    try { writeNotionRow_(name, email, phone, solving, timing, message); } catch (nErr) {
      console.error('Notion sync failed: ' + nErr);
    }

    // Valora app pipeline (best-effort, off until VALORA_INTAKE_URL and
    // VALORA_INTAKE_SECRET are set in Script Properties; failure never blocks
    // the lead). The Sheet, Notion and emails above stay as they are.
    try {
      forwardToApp_({ name: name, email: email, phone: phone, solving_for: solving, help_with: help,
        investable_assets: assets, situation: situation, location: location, message: message, timing: timing });
    } catch (fErr) {
      console.error('App intake failed: ' + fErr);
    }

    return json({ status: 'success', message: 'Lead captured' });

  } catch (err) {
    return json({ status: 'error', message: err.toString() });
  }
}

function writeNotionRow_(name, email, phone, solving, timing, message) {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('NOTION_TOKEN');
  var dbId  = props.getProperty('NOTION_DB_ID');
  if (!token || !dbId) return; // sync not configured
  var payload = {
    parent: { database_id: dbId },
    properties: {
      Name:   { title: [{ text: { content: name } }] },
      Email:  { email: email },
      Phone:  { phone_number: phone },
      Status: { select: { name: 'New Lead' } }
    }
  };
  if (solving) payload.properties['Solving For'] = { rich_text: [{ text: { content: solving } }] };
  if (timing)  payload.properties['Timing']      = { rich_text: [{ text: { content: timing } }] };
  if (message) payload.properties['Message']     = { rich_text: [{ text: { content: message.slice(0, 1900) } }] };
  UrlFetchApp.fetch('https://api.notion.com/v1/pages', {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + token, 'Notion-Version': '2022-06-28' },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
}

/**
 * Whether the email's domain has a mail server (MX record), via Google's
 * public DNS-over-HTTPS. true: MX found. false: the domain does not exist or
 * has no MX. null: the lookup failed, so the caller does not guess.
 */
function domainAcceptsMail_(email) {
  var domain = String(email).split('@').pop().trim().toLowerCase();
  if (!domain || domain.indexOf('.') === -1) return false;
  try {
    var res = UrlFetchApp.fetch('https://dns.google/resolve?name=' + encodeURIComponent(domain) + '&type=MX', { muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) return null;
    var body = JSON.parse(res.getContentText());
    if (body.Status === 3) return false; // NXDOMAIN: the domain does not exist
    if (body.Status !== 0) return null;  // SERVFAIL and friends: unknown
    var mx = (body.Answer || []).filter(function (a) { return a.type === 15; });
    // A "null MX" (RFC 7505, exchange ".") means the domain accepts no mail.
    return mx.some(function (a) { return !/^0\s+\.$/.test(String(a.data).trim()); });
  } catch (err) {
    console.error('MX lookup failed: ' + err);
    return null;
  }
}

/**
 * Sends the lead to the Valora app's website-lead intake. One retry with the
 * same Idempotency-Key, so a retried request is stored once. Empty fields
 * are left out (the intake rejects nothing else).
 */
function forwardToApp_(lead) {
  var props = PropertiesService.getScriptProperties();
  var url = props.getProperty('VALORA_INTAKE_URL');
  var secret = props.getProperty('VALORA_INTAKE_SECRET');
  if (!url || !secret || url.indexOf('https://') !== 0) return;
  var body = {};
  Object.keys(lead).forEach(function (k) { if (lead[k]) body[k] = lead[k]; });
  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: { 'X-Valora-Intake-Secret': secret, 'Idempotency-Key': 'site-' + Utilities.getUuid() },
    payload: JSON.stringify(body),
    muteHttpExceptions: true
  };
  for (var attempt = 0; attempt < 2; attempt++) {
    var code = UrlFetchApp.fetch(url, options).getResponseCode();
    if (code === 200 || code === 201) return;
    if (code < 500) { console.error('App intake refused the lead: HTTP ' + code); return; }
  }
  console.error('App intake unavailable after a retry');
}

function getSheet() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  if (SHEET_NAME) {
    return ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  }
  return ss.getSheets()[0];
}

function str(v) { return (v === null || v === undefined) ? '' : String(v).trim(); }

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

/* ---------------- one-off legacy migration (run once, then ignore) ---------------- */
function migrateLegacy() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  ss.rename('Valora Leads (Organic)');
  var sheet = getSheet();
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  // Jay Boekeloo, 21/09/2026 09:54 IST (from the old pipeline's alert email)
  sheet.appendRow(['Jay Boekeloo', 'boekeloo.jay@gmail.com', '5039575594',
                   'Retirement income', '', '', '', '', 'This is a trial', '']);
  SpreadsheetApp.flush();
  return 'migrated: rows=' + sheet.getLastRow() + ' name=' + ss.getName();
}
