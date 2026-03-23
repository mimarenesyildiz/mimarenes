/* ===== PriorityImageLoader =====
   Priority-based lazy image loader with race-condition protection
   Shared across all pages
   ================================================ */
class PriorityImageLoader {
  constructor(options) {
    options = options || {};
    this.maxConcurrent = options.maxConcurrent || 4;
    this.items = [];
    this.loading = 0;
    this.observer = null;
    this.activeFilter = 'featured';
    this.isDarkTheme = false;
    this.init();
  }

  init() {
    this.onFilterChange = this.onFilterChange.bind(this);
    this.onThemeChange = this.onThemeChange.bind(this);
    this.handleResize = this.handleResize.bind(this);
    this._resizeTimer = null;

    this.setupObserver();
    this.buildQueue();

    document.addEventListener('filterChanged', (e) => this.onFilterChange(e.detail.filter));
    document.addEventListener('themeChanged', (e) => this.onThemeChange(e.detail.isDark));
    window.addEventListener('resize', () => {
      clearTimeout(this._resizeTimer);
      this._resizeTimer = setTimeout(this.handleResize, 150);
    });

    this.syncPageState();
  }

  setupObserver() {
    this.observer = new IntersectionObserver((entries) => {
      let needsProcessing = false;
      entries.forEach(entry => {
        const item = this.findItem(entry.target);
        if (!item || item.status !== 'idle') return;

        if (item.inViewport !== entry.isIntersecting) {
          item.inViewport = entry.isIntersecting;
          this.updatePriority(item);
          needsProcessing = true;
        }
      });

      if (needsProcessing) {
        this.processQueue();
      }
    }, { threshold: 0.01, rootMargin: '200px 0px' });
  }

  buildQueue() {
    const images = document.querySelectorAll('img[data-src]');

    images.forEach(img => {
      if (img.dataset.loaded) return;

      const picture = img.closest('picture');
      const themeVariant = picture && picture.classList.contains('dark-only')
        ? 'dark'
        : picture && picture.classList.contains('light-only')
          ? 'light'
          : 'both';

      this.items.push({
        img: img,
        name: img.alt || img.dataset.src,
        workItem: img.closest('.work-item'),
        picture: picture,
        themeVariant: themeVariant,
        basePriority: 4,
        priority: 4,
        inViewport: false,
        status: 'idle',
        sources: Array.from((picture || { querySelectorAll: function () { return []; } }).querySelectorAll('source[data-srcset]'))
      });

      this.observer.observe(img);
    });
  }

  findItem(img) {
    return this.items.find((item) => item.img === img);
  }

  syncPageState() {
    const activeLink = document.querySelector('.sub-nav-link.active');
    this.activeFilter = activeLink ? activeLink.dataset.filter : 'featured';
    this.isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';
    this.refreshViewportFlags();
    this.items.forEach((item) => this.updatePriority(item));
    this.processQueue();
  }

  handleResize() {
    this.refreshViewportFlags();
    this.items.forEach((item) => this.updatePriority(item));
    this.processQueue();
  }

  refreshViewportFlags() {
    this.items.forEach((item) => {
      if (item.status !== 'idle') return;
      item.inViewport = this.isNearViewport(item.img);
    });
  }

  isNearViewport(element) {
    const workItem = element.closest('.work-item');
    if (workItem && workItem.classList.contains('hiding')) return false;

    const visibilityTarget =
      element.closest('.work-visual') ||
      element.closest('.related-visual') ||
      element.closest('picture') ||
      element;

    const rect = visibilityTarget.getBoundingClientRect();
    return rect.width > 0 &&
      rect.height > 0 &&
      rect.bottom >= -200 &&
      rect.top <= window.innerHeight + 200;
  }

  isThemeMatch(item) {
    if (item.themeVariant === 'dark') return this.isDarkTheme;
    if (item.themeVariant === 'light') return !this.isDarkTheme;
    return true;
  }

  isFilterMatch(item) {
    if (!item.workItem) return true;
    const tags = item.workItem.dataset.tags ? item.workItem.dataset.tags.split(',') : [];
    return tags.includes(this.activeFilter);
  }

  isRelatedCardImage(item) {
    return Boolean(item.img.closest('.related-visual'));
  }

  updatePriority(item) {
    if (item.status !== 'idle') return;

    let basePriority = 4;

    if (!this.isThemeMatch(item)) {
      basePriority = 6;
    } else if (item.workItem && item.workItem.classList.contains('hiding')) {
      basePriority = 6;
    } else if (this.isFilterMatch(item)) {
      basePriority = 2;
    }

    item.basePriority = basePriority;
    item.priority = item.inViewport ? Math.max(1, basePriority - 1) : basePriority;
  }

  getPendingItems() {
    return this.items
      .filter((item) => item.status === 'idle')
      .sort((a, b) => a.priority - b.priority);
  }

  canLoad(item) {
    return item.basePriority < 6 && (item.inViewport || this.isRelatedCardImage(item));
  }

  parseSrcset(srcset) {
    if (!srcset) return [];
    return srcset
      .split(',')
      .map((entry) => entry.trim().split(/\s+/)[0])
      .filter(Boolean);
  }

  shouldApplyImgFallback(item, img) {
    if (!img.dataset.src) return false;
    if (!item.sources.length) return true;

    const fallbackSrc = img.dataset.src;
    const isJpegFallback = /\.jpe?g(?:[?#].*)?$/i.test(fallbackSrc);
    if (!isJpegFallback) return true;

    const sourceUrls = item.sources.flatMap((source) => this.parseSrcset(source.dataset.srcset));
    return sourceUrls.some((url) => url === fallbackSrc);
  }

  processQueue() {
    const pendingItems = this.getPendingItems();

    for (const item of pendingItems) {
      if (this.loading >= this.maxConcurrent) break;
      if (!this.canLoad(item)) continue;
      this.loadImage(item);
    }
  }

  loadImage(item) {
    item.status = 'loading';
    this.loading++;
    const targetImg = item.img;
    let retryCount = 0;
    const MAX_RETRIES = 3;

    let timeoutId;
    const isPlaceholderSrc = (src) => !src || src.startsWith('data:image');

    const finishLoad = () => {
      clearTimeout(timeoutId);
      if (targetImg.dataset.loaded) return;

      // Safety layer: if naturalWidth is 0 and src is not a placeholder,
      // the image hasn't actually rendered — retry instead of marking loaded
      if (targetImg.naturalWidth === 0 && !isPlaceholderSrc(targetImg.src) && retryCount < MAX_RETRIES) {
        retryCount++;
        setTimeout(() => {
          if (targetImg.dataset.loaded) return;
          if (typeof targetImg.decode === 'function') {
            targetImg.decode().then(finishLoad).catch(finishLoad);
          } else {
            finishLoad();
          }
        }, 200 * retryCount);
        return;
      }

      this.loading--;
      item.status = 'loaded';
      targetImg.dataset.loaded = 'true';
      targetImg.classList.add('loaded');

      if (this.observer) {
        this.observer.unobserve(targetImg);
      }

      this.processQueue();
    };

    const handleError = () => {
      finishLoad();
    };

    targetImg.addEventListener('load', finishLoad, { once: true });
    targetImg.addEventListener('error', handleError, { once: true });

    timeoutId = setTimeout(() => {
      if (targetImg.dataset.loaded) return;

      // Timeout: check if the image actually rendered
      if (targetImg.naturalWidth === 0 && !isPlaceholderSrc(targetImg.src) && retryCount < MAX_RETRIES) {
        retryCount++;
        const currentSrc = targetImg.src;
        targetImg.src = '';
        targetImg.src = currentSrc;
        timeoutId = setTimeout(() => {
          if (!targetImg.dataset.loaded) {
            finishLoad();
          }
        }, 5000);
      } else {
        finishLoad();
      }
    }, 10000);

    item.sources.forEach(source => {
      if (source.dataset.srcset) {
        source.srcset = source.dataset.srcset;
        source.removeAttribute('data-srcset');
      }
    });

    if (targetImg.dataset.srcset) {
      targetImg.srcset = targetImg.dataset.srcset;
      targetImg.removeAttribute('data-srcset');
    }

    if (this.shouldApplyImgFallback(item, targetImg)) {
      targetImg.src = targetImg.dataset.src;
      targetImg.removeAttribute('data-src');
    } else if (targetImg.dataset.src) {
      targetImg.removeAttribute('data-src');
    } else {
      handleError();
      return;
    }

    // Sync check: image may already be complete (cached)
    if (targetImg.complete && targetImg.currentSrc) {
      if (targetImg.naturalWidth > 0) {
        requestAnimationFrame(finishLoad);
      } else {
        // complete but not decoded yet — wait for decode
        if (typeof targetImg.decode === 'function') {
          targetImg.decode().then(finishLoad).catch(finishLoad);
        } else {
          requestAnimationFrame(finishLoad);
        }
      }
    }
  }

  onFilterChange(filter) {
    this.activeFilter = filter || this.activeFilter;
    this.refreshViewportFlags();
    this.items.forEach((item) => this.updatePriority(item));
    this.processQueue();
  }

  onThemeChange(isDark) {
    this.isDarkTheme = Boolean(isDark);
    this.refreshViewportFlags();
    this.items.forEach((item) => this.updatePriority(item));
    this.processQueue();
  }
}

document.addEventListener('DOMContentLoaded', function () {
  window.imageLoader = new PriorityImageLoader();
});
