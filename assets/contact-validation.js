/* Contact syntax and disposable-domain screening, not ownership verification. */
(function (root) {
  'use strict';
  var disposable = new Set(root.ValoraDisposableDomains || []);
  var wildcards = new Set(root.ValoraDisposableWildcards || []);
  var reserved = /(^|\.)(example\.(com|net|org)|invalid|test|localhost)$/i;
  var commonTypos = { 'gmial.com': 'gmail.com', 'gamil.com': 'gmail.com', 'gmail.con': 'gmail.com', 'gmai.com': 'gmail.com', 'yahoo.con': 'yahoo.com', 'hotmial.com': 'hotmail.com', 'outlok.com': 'outlook.com' };
  function emailError(value) {
    var v = String(value || '').trim();
    if (v.length > 254 || !/^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$/.test(v)) return 'Please enter a valid email address.';
    var parts = v.split('@'), local = parts[0], domain = parts[1].toLowerCase();
    if (local.length > 64 || local[0] === '.' || local.slice(-1) === '.' || local.indexOf('..') !== -1 || domain.split('.').some(function (x) { return !x || x.length > 63 || x[0] === '-' || x.slice(-1) === '-'; })) return 'Please enter a valid email address.';
    var parent = domain;
    while (parent.indexOf('.') !== -1) {
      if (disposable.has(domain) || wildcards.has(parent)) return 'Please use an email address that can receive our follow-up, not a temporary inbox.';
      parent = parent.slice(parent.indexOf('.') + 1);
    }
    if (reserved.test(domain)) return 'Please use an email address that can receive our follow-up.';
    return '';
  }
  function phoneError(value) {
    var v = String(value || '').trim();
    if (!root.libphonenumber || !/^[+\d\s().-]+$/.test(v)) return 'Enter a valid phone number. For a non-US number, include its + country code.';
    var p = root.libphonenumber.parsePhoneNumberFromString(v, 'US');
    if (!p || !p.isValid()) return 'Enter a valid phone number. For a non-US number, include its + country code.';
    if (/^(.)\1{6,}$/.test(p.nationalNumber) || /^(0123456789|1234567890|9876543210)$/.test(p.nationalNumber)) return 'Please enter your phone number, not a placeholder.';
    // NANP 555-0100 through 555-0199 are reserved fictional numbers.
    if (p.countryCallingCode === '1' && /^\d{3}55501\d{2}$/.test(p.nationalNumber)) return 'Please enter your phone number, not a reserved example number.';
    return '';
  }
  root.ValoraContactValidation = { emailError: emailError, phoneError: phoneError, emailSuggestion: function (v) { return commonTypos[String(v || '').trim().split('@')[1]] || ''; }, ownershipVerified: false };
})(typeof window !== 'undefined' ? window : globalThis);
