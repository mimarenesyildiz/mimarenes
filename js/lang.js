/* ===== Dil Yönlendirme + TR↔EN Sayfa Eşlemesi =====
   Head içinde senkron yüklenir ki yönlendirme ilk boyamadan
   önce gerçekleşsin. Kayıtlı tercih yoksa tarayıcı diline
   bakılır: tr → Türkçe, diğer tüm diller → İngilizce.
   Dil düğmesiyle yapılan seçim localStorage'da tutulur ve
   sonraki ziyaretlerde tarayıcı diline bakılmaz.
   Yeni sayfa eklerken eşlemeye bir satır ekleyin.
   ==================================================== */
(function () {
  'use strict';

  var TR_TO_EN = {
    '/': '/en/',
    '/tasarim/mimari/tasarim-fakultesi.html': '/en/design/architecture/design-faculty.html',
    '/tasarim/mimari/herat-camii.html': '/en/design/architecture/herat-mosque.html',
    '/tasarim/mimari/seyir-kulesi.html': '/en/design/architecture/observation-tower.html',
    '/tasarim/mimari/studyo-balat.html': '/en/design/architecture/studio-balat.html',
    '/yazilim/ai/maskrcnn.html': '/en/software/ai/maskrcnn.html',
    '/yazilim/optimizasyon/toplukonut.html': '/en/software/optimization/mass-housing-daylight.html',
    '/yazilim/optimizasyon/uskudar-meydani.html': '/en/software/optimization/uskudar-square.html',
    '/yazilim/optimizasyon/mukarnas.html': '/en/software/optimization/muqarnas.html',
    '/yazilim/fabrikasyon/victory-park.html': '/en/software/fabrication/victory-park.html',
    '/arastirma/fikir/1284.html': '/en/research/ideas/1284.html',
    '/arastirma/fikir/minimalev.html': '/en/research/ideas/minimalev.html'
  };

  var EN_TO_TR = {};
  for (var key in TR_TO_EN) {
    if (Object.prototype.hasOwnProperty.call(TR_TO_EN, key)) {
      EN_TO_TR[TR_TO_EN[key]] = key;
    }
  }

  function normalizePathname(pathname) {
    var normalized = pathname.replace(/\/index\.html$/, '/');
    return normalized === '' ? '/' : normalized;
  }

  var path = normalizePathname(window.location.pathname);
  var isEn = path === '/en/' || path.indexOf('/en/') === 0;
  var currentLang = isEn ? 'en' : 'tr';

  function counterpart() {
    return isEn ? (EN_TO_TR[path] || null) : (TR_TO_EN[path] || null);
  }

  function setPreference(lang) {
    try { localStorage.setItem('lang', lang); } catch (error) {}
  }

  // nav.js dil düğmesi bu API'yi kullanır.
  window.__i18n = {
    lang: currentLang,
    counterpart: counterpart,
    setPreference: setPreference
  };

  var stored = null;
  try { stored = localStorage.getItem('lang'); } catch (error) {}
  var preferred = (stored === 'tr' || stored === 'en') ? stored : null;

  if (!preferred) {
    // Arama motoru botlarını yönlendirme; hreflang etiketleri onlara yeter.
    if (/bot|crawl|spider|slurp|headless|lighthouse|prerender/i.test(navigator.userAgent)) {
      return;
    }
    var browserLang = (navigator.languages && navigator.languages[0]) || navigator.language || '';
    preferred = /^tr(-|_|$)/i.test(browserLang) ? 'tr' : 'en';
  }

  if (preferred !== currentLang) {
    var target = counterpart();
    if (target) {
      // #about her iki dilde de aynı; diğer çapalar dile özgü olduğundan taşınmaz.
      if (window.location.hash === '#about') target += '#about';
      window.location.replace(target);
    }
  }
})();
