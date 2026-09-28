/* =========================================================
   Valora / Wealth — lead form → Google Sheet + email alert
   Sheet columns: Name | Email | Phone Number | Solving For |
                  Looking For Help With | Investable Assets |
                  Situation | Location | Message
   ---------------------------------------------------------
   Deploy: Deploy ▸ New deployment ▸ Web app
           Execute as: Me
           Who has access: Anyone
           Copy the /exec URL into SHEET_ENDPOINT in script.js

   The hero-card and popup forms only ask "What are you solving
   for?" (goal); the full contact-page form asks the newer
   help/assets/situation/location questions instead. Either set
   of params may arrive empty — that's expected, not an error.
   ========================================================= */

// Sheet ID only — NOT the full URL
var SHEET_ID  = '1vWxHqtLPMb_RqE0rTuTyHWh_PJ5o7RkHx5Jyy2P3QCg';
var SHEET_NAME = '';                         // '' = first sheet, or e.g. 'Leads'
var NOTIFY_TO  = 'barot@valorahq.com,brands@grow.surgeaio.com';
var HEADERS    = ['Name', 'Email', 'Phone Number', 'Solving For',
                   'Looking For Help With', 'Investable Assets', 'Situation',
                   'Location', 'Message'];

function doGet(e)  { return handleForm(e); }
function doPost(e) { return handleForm(e); }

function handleForm(e) {
  try {
    var params = (e && e.parameter) ? e.parameter : {};

    var name      = str(params.name);
    var email     = str(params.email);
    var phone     = str(params.phone);
    var solving   = str(params.goal || params.solving || params.service);
    var help      = str(params.help);
    var assets    = str(params.assets);
    var situation = str(params.situation);
    var location  = str(params.location);
    var message   = str(params.message || params.note);

    if (!name || !email || !phone) {
      return json({ status: 'error', message: 'Missing required fields' });
    }

    var sheet = getSheet();

    // Write the header row only once, on an empty sheet
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(HEADERS);
      sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
      sheet.setFrozenRows(1);
    }

    sheet.appendRow([name, email, phone, solving, help, assets, situation, location, message]);
    SpreadsheetApp.flush();

    var timestamp = Utilities.formatDate(
      new Date(),
      Session.getScriptTimeZone(),
      'dd/MM/yyyy HH:mm:ss'
    );

    var lines = [
      'New Lead Received',
      '',
      'Name: '         + name,
      'Email: '        + email,
      'Phone Number: ' + phone
    ];
    if (solving)  lines.push('Solving For: ' + solving);
    if (help)     lines.push('Looking For Help With: ' + help);
    if (assets)   lines.push('Investable Assets: ' + assets);
    if (situation) lines.push('Situation: ' + situation);
    if (location) lines.push('Location: ' + location);
    lines.push('Message: ' + (message || '-'));
    lines.push('Time: ' + timestamp);

    GmailApp.sendEmail(NOTIFY_TO, 'Valora New Organic Lead - ' + name, lines.join('\n'));

    return json({ status: 'success', message: 'Lead captured' });

  } catch (err) {
    return json({ status: 'error', message: err.toString() });
  }
}

/* ---------------- helpers ---------------- */

function getSheet() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  if (SHEET_NAME) {
    return ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  }
  return ss.getSheets()[0];
}

function str(v) {
  return (v === null || v === undefined) ? '' : String(v).trim();
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/* ---------------- manual test ---------------- */

function testHandleForm() {
  var fakeEvent = {
    parameter: {
      name: 'Test User',
      email: 'test@example.com',
      phone: '9999999999',
      goal: 'Retirement income',
      help: 'Retirement planning, Tax planning',
      assets: '$1M to $3M',
      situation: 'Executive / professional',
      location: 'Austin, TX',
      message: 'Looking for a second opinion on my 401k.'
    }
  };
  Logger.log(handleForm(fakeEvent).getContent());
}
