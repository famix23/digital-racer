/* DigitalRacer: accessible, preference-persistent day/night appearance switch.
   The default remains the original black-and-gold storefront. */
(function () {
  "use strict";
  var KEY = "digitalracer-theme";
  var html = document.documentElement;
  var sun = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>';
  var moon = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M20.95 13.1A9 9 0 0 1 10.9 3.05 9 9 0 1 0 20.95 13.1Z"/></svg>';
  var button;
  function preferred() {
    try { return localStorage.getItem(KEY) === "light" ? "light" : "dark"; }
    catch (_) { return html.getAttribute("data-dr-theme") === "light" ? "light" : "dark"; }
  }
  function apply(value, save) {
    var mode = value === "light" ? "light" : "dark";
    html.setAttribute("data-dr-theme", mode);
    html.style.colorScheme = mode;
    var bar = document.querySelector('meta[name="theme-color"]');
    if (bar) bar.setAttribute("content", mode === "light" ? "#f8f7f4" : "#050505");
    if (save) { try { localStorage.setItem(KEY, mode); } catch (_) { /* Session-only preference. */ } }
    if (!button) return;
    var next = mode === "dark" ? "light" : "dark";
    button.setAttribute("aria-label", "Switch to " + next + " theme");
    button.setAttribute("title", "Switch to " + next + " theme");
    button.setAttribute("aria-pressed", String(mode === "light"));
    button.innerHTML = (mode === "dark" ? sun : moon) +
      '<span class="dr-theme-label">' + (mode === "dark" ? "Light" : "Dark") + '<span class="dr-theme-sr"> theme</span></span>';
  }
  function install() {
    if (document.getElementById("dr-theme-toggle")) return;
    button = document.createElement("button");
    button.id = "dr-theme-toggle";
    button.className = "dr-theme-toggle";
    button.type = "button";
    button.addEventListener("click", function () {
      apply(html.getAttribute("data-dr-theme") === "light" ? "dark" : "light", true);
    });
    var host = document.querySelector("body > nav .nav-links") ||
      document.querySelector(".topbar .navright") ||
      document.querySelector("body.dr-category-page header nav") ||
      document.querySelector("body > header nav") ||
      document.querySelector("header nav");
    if (host) {
      host.appendChild(button);
    } else {
      button.classList.add("dr-theme-floating");
      document.body.appendChild(button);
    }
    apply(preferred(), false);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install);
  else install();
  window.addEventListener("storage", function (event) {
    if (event.key === KEY) apply(event.newValue === "light" ? "light" : "dark", false);
  });
})();

/* Sales funnel instrumentation: event delegation covers dynamically loaded cards,
   homepage, product pages, category hubs and Speed Drift WhatsApp links.
   This emits a GA4 event only when a real GA4 tag has been configured; no
   visitor identifiers or prefilled WhatsApp message text are collected here. */
(function () {
  "use strict";
  function findWhatsApp(el) {
    if (!el || !el.closest) return null;
    var a = el.closest("a[href]");
    if (!a) return null;
    try {
      var u = new URL(a.href, window.location.href);
      return u.protocol === "https:" &&
        (u.hostname === "wa.me" || u.hostname === "api.whatsapp.com" || u.hostname === "web.whatsapp.com") ? a : null;
    } catch (_) { return null; }
  }
  document.addEventListener("click", function (e) {
    var a = findWhatsApp(e.target);
    if (!a || typeof window.gtag !== "function") return;
    var tile = a.closest(".dr-product-tile");
    var detail = tile && tile.querySelector('a.product-card[href^="/p/"]');
    var productPath = detail ? detail.getAttribute("href") :
      (/^\/p\/[^/]+\/$/.test(window.location.pathname) ? window.location.pathname : "");
    var clickArea = a.id === "buy-btn" ? "product_buy" :
      a.classList.contains("dr-card-whatsapp") ? "product_card" :
      a.classList.contains("wa-float") ? "floating" :
      document.body.classList.contains("dr-category-page") ? "category_hub" : "other";
    var category = tile && tile.querySelector(".prod-category");
    try {
      window.gtag("event", "whatsapp_click", {
        click_area: clickArea,
        product_path: productPath || undefined,
        item_category: category ? category.textContent.trim() : undefined,
        page_path: window.location.pathname,
        destination: "whatsapp"
      });
    } catch (_) { /* A reporting error must never interrupt the buyer's click. */ }
  }, { passive: true });
})();

/* Preserve built, factual buyer guidance if the product data API re-renders
   the description after hydration. Avoid new network requests or duplicates. */
(function () {
  "use strict";
  function preserveNotes() {
    var desc = document.getElementById("prod-desc");
    var original = desc && desc.querySelector(".dr-buyer-verification");
    if (!original || typeof MutationObserver !== "function") return;
    var safeCopy = original.cloneNode(true);
    var observer = new MutationObserver(function () {
      if (!desc.querySelector(".dr-buyer-verification")) {
        desc.appendChild(safeCopy.cloneNode(true));
      }
    });
    observer.observe(desc, {childList:true});
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", preserveNotes);
  } else preserveNotes();
})();

/* Product-page marketplace enhancement: load only on product views.
   Script and styles are intentionally outside the generated SEO HTML so
   canonical, JSON-LD, title and static related links cannot be rewritten. */
(function () {
  "use strict";
  if (typeof document === "undefined" || !document.querySelector(".product-grid-layout") ||
      !document.querySelector(".related-section")) return;
  if (document.querySelector('script[data-dr-product-discovery]')) return;
  var script = document.createElement("script");
  script.src = "/assets/product-discovery.js";
  script.defer = true;
  script.setAttribute("data-dr-product-discovery", "true");
  document.head.appendChild(script);
})();

/* Shared purchase actions for catalog, homepage and category cards; compact View only for recommendations.
   Eligibility is rechecked against the actual product page before checkout
   displays a wallet; no price or availability is trusted from URL parameters. */
(function () {
  "use strict";
  if (typeof document === "undefined" || typeof document.querySelectorAll !== "function" ||
      typeof MutationObserver !== "function") return;
  var selector = '.dr-product-tile, .dr-category-page a.product-card[href^="/p/"], .dr-bentley-fast-card';
  var recommendationSelector = 'a.rel-card[href^="/p/"], a.dr-discovery-card[href^="/p/"], a.dr-discovery-mini[href^="/p/"]';
  function enhanceRecommendation(node) {
    if (!node || node.nodeType !== 1 || node.dataset.drViewReady) return;
    var path = node.getAttribute("href");
    if (!path || !/^\/p\/[a-z0-9-]+\/$/.test(path)) return;
    node.dataset.drViewReady = "1";
    // The original card remains the sole, crawlable product link. The view
    // label is inside that link, never a nested anchor or separate purchase action.
    if (node.querySelector(".dr-recommendation-view")) return;
    var host = node.querySelector(".rel-content, .dr-discovery-mini-copy, .dr-discovery-card-copy") || node;
    var existing = host.querySelector(".dr-discovery-card-action");
    if (existing) { existing.textContent = "View"; existing.classList.add("dr-recommendation-view"); }
    else {
      var view = document.createElement("span");
      view.className = "dr-recommendation-view";
      view.textContent = "View";
      host.appendChild(view);
    }
  }
  function action(path, label, className, href) {
    var a = document.createElement("a");
    a.className = className;
    a.textContent = label;
    a.href = href;
    a.setAttribute("aria-label", label + " — " + path);
    return a;
  }
  function enhance(node) {
    if (!node || node.nodeType !== 1 || node.dataset.drPurchaseReady) return;
    var detail = node.matches('a[href^="/p/"]') ? node :
      node.querySelector('a[href^="/p/"]');
    var path = detail && detail.getAttribute("href");
    if (!path || !/^\/p\/[a-z0-9-]+\/$/.test(path)) return;
    node.dataset.drPurchaseReady = "1";
    var seller = node.matches("a") ? null : node.querySelector('a[href^="https://wa.me/923454342911"]');
    var buy = action(path, "Buy Now", "dr-card-buy", "/checkout-preview/?product=" + encodeURIComponent(path));
    if (seller) {
      seller.textContent = "Chat with Seller";
      seller.classList.add("dr-card-chat");
      seller.parentNode.insertBefore(buy, seller);
    } else {
      seller = action(path, "Chat with Seller", "dr-card-chat",
        "https://wa.me/923454342911?text=" + encodeURIComponent("Hello DigitalRacer, I am interested in this product: https://www.digitalracer.store" + path));
      seller.target = "_blank";
      seller.rel = "noopener noreferrer";
      var group = document.createElement("div");
      group.className = "dr-card-purchase-actions";
      group.appendChild(buy);
      group.appendChild(seller);
      if (node.matches("a")) {
        var wrapper = document.createElement("div");
        wrapper.className = "dr-card-purchase-wrapper";
        node.parentNode.insertBefore(wrapper,node);
        wrapper.appendChild(node);
        wrapper.appendChild(group);
      } else node.appendChild(group);
    }
  }
  function scan(root) {
    if (root.nodeType === 1 && root.matches(selector)) enhance(root);
    if (root.querySelectorAll) root.querySelectorAll(selector).forEach(enhance);
    if (root.nodeType === 1 && root.matches(recommendationSelector)) enhanceRecommendation(root);
    if (root.querySelectorAll) root.querySelectorAll(recommendationSelector).forEach(enhanceRecommendation);
  }
  function install() {
    if (!document.body) return;
    scan(document.body);
    new MutationObserver(function (records) {
      records.forEach(function (record) {
        record.addedNodes.forEach(function (node) { if (node.nodeType === 1) scan(node); });
      });
    }).observe(document.body, {childList:true, subtree:true});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install);
  else install();
})();

/* Product photos for deep category directories. The original static links,
   titles and prices remain in HTML even when the optional feed is unavailable.
   Load only on opening a directory, not on blogs or on initial storefront load. */
(function () {
  "use strict";
  if (typeof document.querySelectorAll !== "function" || !window.location ||
      !/^\/shop\/[^/]+\/(?:page\/[0-9]+\/)?$/.test(window.location.pathname)) return;
  var directories = document.querySelectorAll("details.listing-directory");
  if (!directories.length || typeof fetch !== "function") return;
  var feed;
  function loadFeed() {
    if (!feed) feed = fetch("/assets/catalog-index.json").then(function (response) {
      if (!response.ok) throw new Error("Catalog photos unavailable");
      return response.json();
    }).then(function (items) {
      var byUrl = new Map();
      if (Array.isArray(items)) items.forEach(function (item) {
        if (item && typeof item.url === "string" && typeof item.thumbnail === "string") {
          byUrl.set(item.url, item.thumbnail);
        }
      });
      return byUrl;
    }).catch(function () { feed = null; return null; });
    return feed;
  }
  function enhance(directory) {
    if (!directory.open || directory.dataset.drPhotosLoading) return;
    directory.dataset.drPhotosLoading = "1";
    loadFeed().then(function (photos) {
      if (!photos) { delete directory.dataset.drPhotosLoading; return; }
      var links = directory.querySelectorAll("a.directory-product");
      function addPhoto(link) {
        if (link.querySelector(".dr-directory-photo")) return;
        var raw = photos.get(link.getAttribute("href"));
        if (!raw) return;
        var url;
        try { url = new URL(raw, window.location.origin); } catch (_) { return; }
        if (url.protocol !== "https:" || url.username || url.password ||
            (url.origin !== window.location.origin && !/^https:\/\//i.test(raw))) return;
        var img = document.createElement("img");
        img.className = "dr-directory-photo";
        img.alt = "";
        img.width = 480; img.height = 360;
        img.loading = "lazy"; img.decoding = "async";
        img.addEventListener("error", function () { img.hidden = true; }, { once: true });
        img.src = url.href;
        link.insertBefore(img, link.firstChild);
      }
      if (typeof IntersectionObserver === "function") {
        var observer = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) { addPhoto(entry.target); observer.unobserve(entry.target); }
          });
        }, { rootMargin: "200px" });
        links.forEach(function (link) { observer.observe(link); });
      } else links.forEach(addPhoto);
    });
  }
  directories.forEach(function (directory) {
    directory.addEventListener("toggle", function () { enhance(directory); });
    if (directory.open) enhance(directory);
  });
})();
