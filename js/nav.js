/* ===== Shared Navigation Bar =====
   Tüm sayfalarda aynı nav bar'ı inject eder.
   Ana sayfada animasyonlu, iç sayfalarda sabit.
   ===================================== */
(function () {
  'use strict';

  function normalizePathname(pathname) {
    var normalized = pathname.replace(/\/index\.html$/, '/');
    return normalized === '' ? '/' : normalized;
  }

  // Determine base path relative to root
  var scripts = document.getElementsByTagName('script');
  var currentScript = scripts[scripts.length - 1];
  var src = currentScript.getAttribute('src') || '';
  var basePath = src.replace(/js\/nav\.js.*$/, '');

  // Detect if we're on the homepage
  var path = window.location.pathname;
  var isHome = path === '/' || path.endsWith('/index.html') || path.endsWith('/mimarenes-main/') || path.endsWith('/mimarenes-main/index.html');
  var suppressHomeIntro = false;
  var cameFromSameOrigin = false;

  // Language: /en/ altındaki sayfalar İngilizce'dir (bkz. js/lang.js)
  var isEn = path === '/en' || path === '/en/' || path.indexOf('/en/') === 0;
  var t = isEn ? {
    homeAria: 'Home - Enes Yıldız',
    about: 'About',
    navAria: 'Main navigation',
    toDark: 'Switch to dark mode',
    toLight: 'Switch to light mode',
    langLabel: 'TR',
    langAria: 'Türkçe sürüm',
    langTarget: 'tr'
  } : {
    homeAria: 'Ana Sayfa - Enes Yıldız',
    about: 'Hakkımda',
    navAria: 'Ana navigasyon',
    toDark: 'Karanlık moda geç',
    toLight: 'Aydınlık moda geç',
    langLabel: 'EN',
    langAria: 'English version',
    langTarget: 'en'
  };

  try {
    suppressHomeIntro = sessionStorage.getItem('skipHomeNavIntro') === '1';
    if (suppressHomeIntro) {
      sessionStorage.removeItem('skipHomeNavIntro');
    }
  } catch (error) {}

  try {
    cameFromSameOrigin = !!document.referrer && new URL(document.referrer, window.location.href).origin === window.location.origin;
  } catch (error) {}

  // Build nav HTML
  var homeClass = isHome && !suppressHomeIntro && !cameFromSameOrigin ? ' nav--home' : '';
  var homeHref = isEn ? basePath + 'en/index.html' : basePath + 'index.html';
  var aboutHref = isHome ? '#about' : homeHref + '#about';
  var logoTag = '<a href="' + homeHref + '" class="nav-logo" id="logoLink" aria-label="' + t.homeAria + '">Enes Yıldız</a>';
  var aboutTag = '<a href="' + aboutHref + '" class="nav-link" id="aboutLink">' + t.about + '</a>';

  // Dil düğmesi: karşılık gelen sayfa lang.js eşlemesinden gelir,
  // eşleme yoksa diğer dilin ana sayfasına düşer.
  var langHref = isEn ? '/' : '/en/';
  try {
    if (window.__i18n && window.__i18n.counterpart()) {
      langHref = window.__i18n.counterpart();
    }
  } catch (error) {}
  var langTag = '<a href="' + langHref + '" class="nav-link lang-toggle" id="langToggle" lang="' + t.langTarget + '" aria-label="' + t.langAria + '">' + t.langLabel + '</a>';

  var navHTML = '<nav class="nav' + homeClass + '" id="mainNav" role="navigation" aria-label="' + t.navAria + '">'
    + '<div class="nav-inner">'
    + logoTag
    + '<div class="nav-menu">'
    + aboutTag
    + langTag
    + '<button class="theme-toggle" id="themeToggle" type="button" aria-label="' + t.toDark + '" title="' + t.toDark + '" aria-pressed="false">'
    +   '<svg class="theme-icon theme-icon-sun" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
    +   '<span class="theme-toggle-core" aria-hidden="true"></span>'
    +   '<svg class="theme-icon theme-icon-moon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
    + '</button>'
    + '</div>'
    + '</div>'
    + '</nav>';

  // Inject nav at the placeholder or at the start of body
  var placeholder = document.getElementById('nav-placeholder');
  if (placeholder) {
    placeholder.outerHTML = navHTML;
  } else {
    document.body.insertAdjacentHTML('afterbegin', navHTML);
  }

  // Suppress the homepage intro animation after internal navigations.
  document.addEventListener('click', function (event) {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }

    var link = event.target.closest('a[href]');
    if (!link || link.target === '_blank' || link.hasAttribute('download')) {
      return;
    }

    var href = link.getAttribute('href') || '';
    if (!href || href.indexOf('mailto:') === 0 || href.indexOf('tel:') === 0 || href.indexOf('javascript:') === 0) {
      return;
    }

    var targetUrl;
    try {
      targetUrl = new URL(link.href, window.location.href);
    } catch (error) {
      return;
    }

    if (targetUrl.origin !== window.location.origin) {
      return;
    }

    if (normalizePathname(targetUrl.pathname) === normalizePathname(window.location.pathname)) {
      return;
    }

    try {
      sessionStorage.setItem('skipHomeNavIntro', '1');
    } catch (error) {}
  });

  // --- Theme Toggle ---
  var html = document.documentElement;
  var themeToggle = document.getElementById('themeToggle');

  function getPreferredTheme() {
    var savedTheme = localStorage.getItem('theme');
    if (savedTheme) return savedTheme;
    return 'light';
  }

  function updateThemeToggle(theme) {
    if (!themeToggle) return;
    var isDark = theme === 'dark';
    var nextLabel = isDark ? t.toLight : t.toDark;
    themeToggle.setAttribute('aria-pressed', String(isDark));
    themeToggle.setAttribute('aria-label', nextLabel);
    themeToggle.setAttribute('title', nextLabel);
  }

  function setTheme(theme) {
    var normalizedTheme = theme === 'dark' ? 'dark' : 'light';
    html.setAttribute('data-theme', normalizedTheme);
    localStorage.setItem('theme', normalizedTheme);
    updateThemeToggle(normalizedTheme);
    var meta = document.getElementById('themeColorMeta');
    if (meta) meta.setAttribute('content', normalizedTheme === 'dark' ? '#0a0a0a' : '#f8f8f8');
    document.dispatchEvent(new CustomEvent('themeChanged', {
      detail: { theme: normalizedTheme, isDark: normalizedTheme === 'dark' }
    }));
  }

  setTheme(getPreferredTheme());

  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var currentTheme = html.getAttribute('data-theme');
      setTheme(currentTheme === 'dark' ? 'light' : 'dark');
    });
  }

  // --- Language Toggle ---
  // Seçim kaydedilir ki lang.js sonraki sayfalarda geri yönlendirmesin.
  var langToggle = document.getElementById('langToggle');
  if (langToggle) {
    langToggle.addEventListener('click', function () {
      try {
        if (window.__i18n) {
          window.__i18n.setPreference(t.langTarget);
        } else {
          localStorage.setItem('lang', t.langTarget);
        }
      } catch (error) {}
    });
  }

  // --- Nav Scroll Shadow ---
  var nav = document.getElementById('mainNav');
  var scrollTicking = false;

  window.addEventListener('scroll', function () {
    if (!scrollTicking) {
      scrollTicking = true;
      requestAnimationFrame(function () {
        if (window.scrollY > 10) {
          nav.classList.add('scrolled');
        } else {
          nav.classList.remove('scrolled');
        }
        scrollTicking = false;
      });
    }
  });

  function initScrollReveal() {
    var revealEls = document.querySelectorAll('.reveal');
    if (!revealEls.length) return;

    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    revealEls.forEach(function (el) { revealObserver.observe(el); });
  }

  function initVideoAutoplay() {
    var videos = document.querySelectorAll('video[autoplay]');
    if (!videos.length) return;

    var videoObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.play().catch(function () {});
        } else {
          entry.target.pause();
        }
      });
    }, { threshold: 0.25 });

    videos.forEach(function (v) { videoObserver.observe(v); });
  }

  function initDeferredFeatures() {
    initScrollReveal();
    initVideoAutoplay();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDeferredFeatures, { once: true });
  } else {
    initDeferredFeatures();
  }
})();
