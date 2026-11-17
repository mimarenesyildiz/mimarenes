/* ============================================================
   Motion figures
   <figure class="motion" data-motion="/motion/dosya.svg"> yuvalarına
   SVG'yi satır içi gömer (tema renklerini sayfadan alabilsin diye),
   ekrana girince oynatır, ekrandan çıkınca duraklatır.

   SVG içindeki data-en taşıyan metinler İngilizce sayfada o değerle
   değiştirilir; böylece iki dil aynı dosyayı kullanır.
   ============================================================ */
(function () {
  'use strict';

  var supportsIO = 'IntersectionObserver' in window;
  var isEn = /^en/i.test(document.documentElement.lang || '');
  var PLAY_AT = 0.25;   // şeklin dörtte biri göründüğünde oynamaya başlar

  // Yakına gelince yükle
  var loadObserver = supportsIO ? new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      loadObserver.unobserve(entry.target);
      load(entry.target);
    });
  }, { rootMargin: '600px 0px' }) : null;

  // Yeterince görününce oynat, tamamen çıkınca durdur
  var playObserver = supportsIO ? new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.intersectionRatio >= PLAY_AT) {
        entry.target.classList.remove('is-paused');
        startCounting();
      } else if (!entry.isIntersecting) {
        entry.target.classList.add('is-paused');
      }
    });
  }, { threshold: [0, PLAY_AT] }) : null;

  function localize(root) {
    if (!isEn) return;
    Array.prototype.forEach.call(root.querySelectorAll('[data-en]'), function (el) {
      el.textContent = el.getAttribute('data-en');
    });
  }

  // Sayaçlar: data-count taşıyan metinler, CSS animasyonunun yürüttüğü
  // --motion-count değerini gösterir. Sayının zaman içindeki seyri SVG'nin
  // kendi keyframe'lerinde durur; burada yalnızca ekrana yazılır.
  var counters = [];
  var counting = false;

  function count() {
    var active = false;
    counters.forEach(function (c) {
      if (c.fig.classList.contains('is-paused')) return;
      active = true;
      var value = Math.round(parseFloat(getComputedStyle(c.el).getPropertyValue('--motion-count')));
      if (isNaN(value) || value === c.last) return;
      c.last = value;
      c.el.textContent = value.toLocaleString(isEn ? 'en-US' : 'tr-TR');
    });
    if (active) requestAnimationFrame(count); else counting = false;
  }

  function startCounting() {
    if (counting || !counters.length) return;
    counting = true;
    requestAnimationFrame(count);
  }

  function collectCounters(fig, root) {
    Array.prototype.forEach.call(root.querySelectorAll('[data-count]'), function (el) {
      counters.push({ fig: fig, el: el, last: null });
    });
  }

  function load(fig) {
    var src = fig.getAttribute('data-motion');
    var frame = fig.querySelector('.motion-frame') || fig;
    fetch(src)
      .then(function (res) {
        if (!res.ok) throw new Error(res.status);
        return res.text();
      })
      .then(function (svg) {
        // Ekrana girene kadar başlamasın: açılış çizimi görülmeden bitmesin
        if (playObserver) fig.classList.add('is-paused');
        frame.innerHTML = svg;
        localize(frame);
        collectCounters(fig, frame);
        if (playObserver) playObserver.observe(fig); else startCounting();
      })
      .catch(function () { fig.hidden = true; });
  }

  function boot() {
    var figs = document.querySelectorAll('[data-motion]:not([data-motion-ready])');
    Array.prototype.forEach.call(figs, function (fig) {
      fig.setAttribute('data-motion-ready', '');
      // İlk ekrandakiler (başlık animasyonu) beklemeden yüklenir
      var nearTop = fig.getBoundingClientRect().top < window.innerHeight * 1.5;
      if (nearTop || !loadObserver) load(fig); else loadObserver.observe(fig);
    });
  }

  boot();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  }
})();
