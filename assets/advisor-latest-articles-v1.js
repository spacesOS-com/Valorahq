/* /for-advisors/: keep the six article cards current. The page ships with six cards already in it;
   this replaces them with the latest six from the site's own feed. If anything fails or looks
   wrong, the cards that shipped with the page stay as they are. Reads only; sends nothing. */
(function () {
  'use strict';
  var box = document.querySelector('#insights-for-advisors .advx-posts');
  if (!box || !window.fetch || !window.DOMParser) return;
  var BASE = 'https://www.valorahq.com/insights/';
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var text = function (item, tag) { var n = item.getElementsByTagName(tag)[0]; return n ? (n.textContent || '').trim() : ''; };
  var el = function (tag, cls, txt) { var n = document.createElement(tag); if (cls) n.className = cls; if (txt) n.textContent = txt; return n; };
  var link = function (cls, url, txt) { var a = el('a', cls, txt); a.href = url; return a; };
  function card(p) {
    var art = el('article', 'advx-post');
    if (p.image) {
      var media = link('advx-post__media', p.url); media.tabIndex = -1; media.setAttribute('aria-hidden', 'true');
      var img = el('img'); img.src = p.image; img.alt = ''; img.loading = 'lazy'; img.decoding = 'async'; img.width = 600; img.height = 338;
      media.appendChild(img); art.appendChild(media);
    }
    var body = el('div', 'advx-post__body');
    if (p.date) body.appendChild(el('p', 'advx-post__date', p.date));
    var h = el('h3'); h.appendChild(link('', p.url, p.title)); body.appendChild(h);
    if (p.excerpt) body.appendChild(el('p', '', p.excerpt));
    body.appendChild(link('advx-post__link', p.url, 'Read the article →'));
    art.appendChild(body);
    return art;
  }
  fetch('/insights/rss/', { credentials: 'omit' }).then(function (r) { if (!r.ok) throw new Error('feed'); return r.text(); }).then(function (xml) {
    var doc = new DOMParser().parseFromString(xml, 'application/xml');
    if (doc.getElementsByTagName('parsererror').length) return;
    var posts = [];
    Array.prototype.slice.call(doc.getElementsByTagName('item'), 0, 6).forEach(function (item) {
      var url = text(item, 'link'), title = text(item, 'title');
      if (!title || url.indexOf(BASE) !== 0) return;                       // only ever link the site's own articles
      var media = item.getElementsByTagName('media:content')[0], image = media ? media.getAttribute('url') || '' : '';
      image = image.indexOf(BASE + 'content/images/') === 0 ? image.replace('/content/images/', '/content/images/size/w600/format/webp/') : '';
      var d = new Date(text(item, 'pubDate'));
      posts.push({ url: url, title: title, excerpt: text(item, 'description').replace(/<[^>]*>/g, ''), image: image,
        date: isNaN(d) ? '' : MONTHS[d.getUTCMonth()] + ' ' + d.getUTCDate() + ', ' + d.getUTCFullYear() });
    });
    if (posts.length < 6) return;                                          // keep the shipped cards unless we have a full set
    var fresh = document.createDocumentFragment();
    posts.forEach(function (p) { fresh.appendChild(card(p)); });
    box.textContent = '';
    box.appendChild(fresh);
  }).catch(function () { /* the shipped cards stay */ });
})();
