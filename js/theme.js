/* ===== Theme Toggle + Scroll + Reveal =====
   Shared across all subpages
   ============================================= */
(function () {
  'use strict';

  const themeToggle = document.getElementById('themeToggle');
  const html = document.documentElement;

  function getPreferredTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) return savedTheme;
    return 'light';
  }

  function updateThemeToggle(theme) {
    if (!themeToggle) return;
    const isDark = theme === 'dark';
    const nextLabel = isDark ? 'Aydınlık moda geç' : 'Karanlık moda geç';
    themeToggle.setAttribute('aria-pressed', String(isDark));
    themeToggle.setAttribute('aria-label', nextLabel);
    themeToggle.setAttribute('title', nextLabel);
  }

  function setTheme(theme) {
    const normalizedTheme = theme === 'dark' ? 'dark' : 'light';
    const isDark = normalizedTheme === 'dark';
    html.setAttribute('data-theme', normalizedTheme);
    localStorage.setItem('theme', normalizedTheme);
    updateThemeToggle(normalizedTheme);
    document.dispatchEvent(new CustomEvent('themeChanged', {
      detail: { theme: normalizedTheme, isDark: isDark }
    }));
  }

  // Initialize theme
  setTheme(getPreferredTheme());

  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var currentTheme = html.getAttribute('data-theme');
      var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      setTheme(newTheme);
    });
  }

  // Nav scroll shadow — rAF-throttled
  var nav = document.querySelector('.nav');
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

  // Scroll reveal — unobserve after visible
  var revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -40px 0px'
  });

  document.querySelectorAll('.reveal').forEach(function (el) {
    revealObserver.observe(el);
  });

  // Video autoplay observer (if any videos on the page)
  var videos = document.querySelectorAll('video[autoplay]');
  if (videos.length) {
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
})();
