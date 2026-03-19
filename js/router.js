alert('Router yüklendi!');
/* ===== SPA Router (PJAX) =====
   Nav bar'ı sabit tutarak sadece #page-body içeriğini değiştirir.
   - Index → Subpage: fetch + swap
   - Subpage → Subpage: fetch + swap
   - Subpage/Any → Index: full reload
   ============================================= */
(function () {
  'use strict';

  var pageBody, indexCssLink, subpageCssLink, currentPageStyle;
  var subpageCssLoaded, fontCssLoaded;
  var navigating = false;

  function init() {
    pageBody = document.getElementById('page-body');
    if (!pageBody) { console.warn('[Router] #page-body bulunamadı'); return; }
    console.log('[Router] Başlatıldı');

    indexCssLink = document.querySelector('link[href*="index.css"]:not([rel="preload"])');
    subpageCssLink = document.querySelector('link[href*="subpage.css"]');
    currentPageStyle = null;
    subpageCssLoaded = !!subpageCssLink;
    fontCssLoaded = !!document.querySelector('link[href*="inter.css"]');

    // İlk yüklemede mevcut state'i kaydet
    history.replaceState({ routerPage: location.href }, '', location.href);

    // ── Click interception ──
    document.addEventListener('click', function (e) {
      var link = e.target.closest('a[href]');
      if (!link) return;

      var href = link.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('http') ||
          href.startsWith('mailto:') || href.startsWith('tel:') ||
          e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;

      // Sadece .html linklerini yakala
      var cleanHref = href.split('#')[0];
      if (!cleanHref.endsWith('.html')) return;

      var resolved = new URL(href, location.href);

      // index.html'e dönüş → full reload
      if (resolved.pathname === '/' ||
          resolved.pathname.endsWith('/index.html')) {
        return; // normal navigasyon
      }

      e.preventDefault();
      console.log('[Router] Navigasyon yakalandı:', resolved.href);
      if (!navigating) navigateTo(resolved.href);
    });

    // ── Popstate (geri/ileri) ──
    window.addEventListener('popstate', function (e) {
      if (e.state && e.state.routerPage) {
        var url = e.state.routerPage;
        var resolved = new URL(url);
        if (resolved.pathname === '/' ||
            resolved.pathname.endsWith('/index.html')) {
          location.reload();
          return;
        }
        loadPage(url);
      } else {
        location.reload();
      }
    });
  }

  function navigateTo(url) {
    history.pushState({ routerPage: url }, '', url);
    loadPage(url);
  }

  function loadPage(url) {
    navigating = true;

    fetch(url)
      .then(function (r) {
        if (!r.ok) { location.href = url; return null; }
        return r.text();
      })
      .then(function (html) {
        if (!html) return;

        var doc = new DOMParser().parseFromString(html, 'text/html');
        var newBody = doc.getElementById('page-body');
        if (!newBody) { location.href = url; return; }

        console.log('[Router] Sayfa yüklendi, swap başlıyor');

        // DEBUG: Router çalıştığını göster (geçici kırmızı border)
        document.querySelector('.nav').style.borderBottom = '3px solid red';

        // 1. Önce CSS swap (subpage.css aktif, index.css devre dışı)
        //    Böylece içerik swap edildiğinde doğru stiller hazır olur
        swapCSS(url);

        // 2. Inline style (accent renkleri)
        injectPageStyles(doc);

        // 3. Nav elementlerinin animasyonlarını sıfırla
        //    (index.css'teki opacity:0 + animation kaldırılınca
        //     default opacity:1'e döner, ama garanti olsun)
        freezeNav();

        // 4. İçerik swap
        pageBody.innerHTML = newBody.innerHTML;

        // 5. Title
        document.title = doc.title;

        // 6. Nav linklerini subpage moduna güncelle
        updateNav(url);

        // 7. Scroll
        window.scrollTo(0, 0);

        // 8. body class
        document.body.classList.remove('js-loading');

        // 9. Gerekli scriptleri yükle, sonra reinit et
        var basePath = resolveBasePath(url);
        ensureScripts(basePath).then(function () {
          reinitImageLoader();
          reinitObservers();
          trackPageView(url);
          navigating = false;
        });
      })
      .catch(function (err) {
        console.error('[Router] Fetch hatası:', err);
        location.href = url;
      });
  }

  // ── Nav'ı dondur (animasyon kalıntılarını temizle) ──
  function freezeNav() {
    var els = document.querySelectorAll('.nav-logo, .nav-link, .theme-toggle');
    els.forEach(function (el) {
      el.style.opacity = '1';
      el.style.transform = 'none';
      el.style.animation = 'none';
    });
  }

  // ── Nav güncelleme ──
  function updateNav(url) {
    var logo = document.querySelector('.nav-logo');
    var aboutEl = document.getElementById('aboutLink') ||
                  document.querySelector('.nav-link');

    var indexPath = resolveIndexPath(url);

    if (logo) {
      logo.setAttribute('href', indexPath);
    }

    if (aboutEl && aboutEl.tagName === 'BUTTON') {
      var a = document.createElement('a');
      a.className = aboutEl.className;
      a.textContent = aboutEl.textContent;
      a.href = indexPath + '#about';
      a.style.opacity = '1';
      a.style.animation = 'none';
      aboutEl.parentNode.replaceChild(a, aboutEl);
    } else if (aboutEl) {
      aboutEl.setAttribute('href', indexPath + '#about');
    }
  }

  function resolveIndexPath(subpageUrl) {
    var path = new URL(subpageUrl).pathname;
    var segments = path.split('/').filter(Boolean);
    var depth = segments.length - 1;
    var prefix = '';
    for (var i = 0; i < depth; i++) prefix += '../';
    return prefix + 'index.html';
  }

  // ── CSS swap ──
  function swapCSS(url) {
    // index.css devre dışı
    if (indexCssLink) {
      indexCssLink.disabled = true;
    }

    // index-font-presets.css de devre dışı
    var fontPresets = document.querySelector('link[href*="index-font-presets"]');
    if (fontPresets) fontPresets.disabled = true;

    var basePath = resolveBasePath(url);

    // subpage.css: disabled olarak eklenmişse aktif et, yoksa yükle
    if (subpageCssLink) {
      subpageCssLink.disabled = false;
    } else if (!subpageCssLoaded) {
      subpageCssLink = document.createElement('link');
      subpageCssLink.rel = 'stylesheet';
      subpageCssLink.href = basePath + 'css/subpage.css';
      document.head.appendChild(subpageCssLink);
      subpageCssLoaded = true;
    }

    // inter.css font yükle
    if (!fontCssLoaded) {
      var fontLink = document.createElement('link');
      fontLink.rel = 'stylesheet';
      fontLink.href = basePath + 'fonts/inter.css';
      document.head.appendChild(fontLink);
      fontCssLoaded = true;
    }
  }

  function resolveBasePath(subpageUrl) {
    var path = new URL(subpageUrl).pathname;
    var segments = path.split('/').filter(Boolean);
    var depth = segments.length - 1;
    var prefix = '';
    for (var i = 0; i < depth; i++) prefix += '../';
    return prefix;
  }

  // ── Inline style inject ──
  function injectPageStyles(doc) {
    if (currentPageStyle) {
      currentPageStyle.remove();
      currentPageStyle = null;
    }

    var styles = doc.querySelectorAll('head style');
    if (styles.length) {
      currentPageStyle = document.createElement('style');
      currentPageStyle.id = 'router-page-style';
      var css = '';
      styles.forEach(function (s) { css += s.textContent; });
      currentPageStyle.textContent = css;
      document.head.appendChild(currentPageStyle);
    }
  }

  // ── Script yükleme ──
  var scriptsLoaded = {
    imageLoader: typeof PriorityImageLoader === 'function'
  };

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function ensureScripts(basePath) {
    var promises = [];
    if (!scriptsLoaded.imageLoader) {
      promises.push(
        loadScript(basePath + 'js/image-loader.js').then(function () {
          scriptsLoaded.imageLoader = true;
        })
      );
    }
    return promises.length ? Promise.all(promises) : Promise.resolve();
  }

  // ── Image loader reinit ──
  function reinitImageLoader() {
    if (window.imageLoader && window.imageLoader.observer) {
      window.imageLoader.observer.disconnect();
    }
    if (typeof PriorityImageLoader === 'function') {
      window.imageLoader = new PriorityImageLoader();
    }
  }

  // ── Scroll reveal + video observers ──
  function reinitObservers() {
    // Reveal
    var revealObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.reveal').forEach(function (el) {
      revealObs.observe(el);
    });

    // Video autoplay
    var videos = document.querySelectorAll('video[autoplay]');
    if (videos.length) {
      var vidObs = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.play().catch(function () {});
          } else {
            entry.target.pause();
          }
        });
      }, { threshold: 0.25 });
      videos.forEach(function (v) { vidObs.observe(v); });
    }

    // Nav scroll state reset
    var nav = document.querySelector('.nav');
    if (nav) {
      nav.classList.remove('scrolled');
      nav.classList.remove('nav--merged');
    }
  }

  // ── Analytics ──
  function trackPageView(url) {
    if (typeof gtag === 'function') {
      gtag('event', 'page_view', {
        page_location: url,
        page_title: document.title
      });
    }
  }

  // ── Başlat ──
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
