/* DigitalRacer product-page marketplace discovery.
   Progressive enhancement only: no edits to product HTML, canonical URLs,
   structured data, original titles, sitemap, or the four static related links. */
(function (root) {
  "use strict";

  var CATEGORY_LINKS = {
    "Account": ["/shop/pubg-mobile-accounts/", "PUBG Mobile accounts"],
    "Car Card": ["/shop/pubg-mobile-car-cards/", "Car skin cards"],
    "UC Top-Up": ["/shop/pubg-mobile-uc-top-ups/", "UC top-ups"],
    "In-Game Items": ["/shop/pubg-mobile-in-game-items/", "In-game items"],
    "Popularity": ["/shop/pubg-mobile-popularity/", "Popularity"],
    "Rank Boosting": ["/shop/pubg-mobile-rank-boosting/", "Rank boosting"]
  };
  var VEHICLE_BRANDS = [
    "bentley", "ferrari", "mclaren", "lamborghini", "bugatti",
    "porsche", "aston martin", "koenigsegg", "tesla", "dodge", "lotus", "bmw"
  ];
  var STOP_WORDS = new Set([
    "pubg","mobile","account","accounts","card","cards","skin","skins",
    "item","items","for","with","sale","buy","digital","racer",
    "delivery","instant","offer","global","usd","and","the","level",
    "lvl","car","cars","new","rare","only","best","cheap","fast"
  ]);
  function validUrl(path) {
    return typeof path === "string" && /^\/p\/[a-z0-9-]+\/$/.test(path);
  }
  function normalize(text) {
    return String(text || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  }
  function tokens(text) {
    return new Set(normalize(text).split(/\s+/).filter(function (s) {
      return s.length > 2 && !STOP_WORDS.has(s);
    }));
  }
  function brandOf(item) {
    var title = normalize(item && item.title);
    var badge = normalize(item && item.badge);
    return VEHICLE_BRANDS.find(function (brand) {
      return (" " + title + " ").includes(" " + brand + " ") ||
             (" " + badge + " ").includes(" " + brand + " ");
    }) || "";
  }
  function scoreMatch(current, candidate) {
    if (!current || !candidate || !validUrl(candidate.url) ||
        candidate.url === current.url) return -1;
    var sameCategory = candidate.category === current.category;
    var sameBrand = brandOf(current) && brandOf(current) === brandOf(candidate);
    var shared = 0, a = tokens(current.title), b = tokens(candidate.title);
    a.forEach(function (word) { if (b.has(word)) shared++; });
    var currentPrice = Number(current.price), candidatePrice = Number(candidate.price);
    var priceSimilarity = Number.isFinite(currentPrice) && Number.isFinite(candidatePrice) &&
      currentPrice > 0 && candidatePrice > 0
      ? Math.max(0, 12 - Math.round(Math.abs(currentPrice - candidatePrice) /
        Math.max(currentPrice, candidatePrice) * 18)) : 0;
    return (sameCategory ? 150 : 0) + (sameBrand ? 250 : 0) +
      Math.min(shared, 9) * 17 + priceSimilarity;
  }
  // Export the pure ranking helper for regression tests. It never changes
  // the product catalog or sorts/reorders the source list in place.
  function rankSimilar(current, products, limit) {
    if (!current || !Array.isArray(products)) return [];
    var seen = new Set([current.url]);
    return products.map(function (p, index) {
      return { p:p, index:index, score:scoreMatch(current,p) };
    }).filter(function (x) {
      if (x.score < 0 || seen.has(x.p.url) || !Number.isFinite(Number(x.p.price))) return false;
      seen.add(x.p.url); return true;
    }).sort(function (a,b) {
      return b.score-a.score || a.index-b.index;
    }).slice(0,limit || 18).map(function (x) { return x.p; });
  }
  root.DRProductDiscoveryRank = rankSimilar;
  if (typeof document === "undefined") return;

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function imagePath(p) {
    var source = typeof p.thumbnail === "string" ? p.thumbnail : "";
    // Catalog images are optimized same-origin paths. Do not allow remote
    // script, javascript:, data:, or protocol-relative seller-supplied URLs.
    return /^\/(?!\/)[a-zA-Z0-9_\-\/.%]+$/.test(source) ? source : "";
  }
  function priceText(p) {
    return "$" + String(p.price) + " USD";
  }
  function productAnchor(p, compact) {
    var a = el("a", compact ? "dr-discovery-mini" : "dr-discovery-card");
    a.href = p.url;
    if (imagePath(p)) {
      var img = el("img", compact ? "dr-discovery-mini-img" : "dr-discovery-card-img");
      img.src = imagePath(p);
      img.alt = p.title;
      img.loading = "lazy";
      img.decoding = "async";
      img.onerror = function () { img.style.visibility = "hidden"; };
      a.appendChild(img);
    } else {
      var fallback = el("span", compact ? "dr-discovery-mini-img dr-no-image" : "dr-discovery-card-img dr-no-image");
      fallback.textContent = "Image unavailable";
      a.appendChild(fallback);
    }
    var copy = el("span", compact ? "dr-discovery-mini-copy" : "dr-discovery-card-copy");
    copy.appendChild(el("span", compact ? "dr-discovery-mini-title" : "dr-discovery-card-title", p.title));
    copy.appendChild(el("span", compact ? "dr-discovery-mini-price" : "dr-discovery-card-price", priceText(p)));
    if (!compact) copy.appendChild(el("span", "dr-discovery-card-action", "View item"));
    a.appendChild(copy);
    return a;
  }
  function makeSection(title, products, categoryHref, subtitle) {
    if (!products.length) return null;
    var section = el("section", "dr-discovery-section");
    var heading = el("div", "dr-discovery-section-head");
    var titleNode = el("h2", "", title);
    heading.appendChild(titleNode);
    if (categoryHref) {
      var view = el("a", "dr-discovery-all", "Browse category");
      view.href = categoryHref; heading.appendChild(view);
    }
    section.appendChild(heading);
    if (subtitle) section.appendChild(el("p", "dr-discovery-subtitle", subtitle));
    var cards = el("div", "dr-discovery-grid");
    products.forEach(function (p) { cards.appendChild(productAnchor(p,false)); });
    section.appendChild(cards);
    return section;
  }
  function canonicalPath() {
    var pathname = root.location && root.location.pathname;
    return validUrl(pathname) ? pathname : "";
  }
  function productFromFeed(feed) {
    var path = canonicalPath();
    var found = path && feed.find(function (p) { return p.url === path; });
    if (found) return found;
    var preset = root.DR_PRESET;
    if (preset) {
      found = feed.find(function (p) {
        return p.title === preset.title && String(p.price) === String(preset.price);
      });
      if (found) return found;
    }
    var title = document.getElementById("prod-title");
    var price = document.getElementById("prod-price");
    return feed.find(function (p) {
      return title && p.title === title.textContent.trim() &&
        price && price.textContent.includes("$" + p.price);
    }) || null;
  }
  function populateRail(rail, products, category) {
    var list = rail.querySelector(".dr-discovery-rail-products");
    if (!list) return;
    list.replaceChildren();
    products.forEach(function (p) { list.appendChild(productAnchor(p,true)); });
    var footer = rail.querySelector(".dr-discovery-rail-nav");
    if (!footer) return;
    footer.replaceChildren();
    var mainLink = CATEGORY_LINKS[category];
    if (mainLink) {
      var link = el("a", "dr-discovery-category-link", "All " + mainLink[1]);
      link.href = mainLink[0]; footer.appendChild(link);
    }
    footer.appendChild(el("div", "dr-discovery-rail-subhead", "Browse more categories"));
    Object.keys(CATEGORY_LINKS).forEach(function (name) {
      if (name === category) return;
      var dest = CATEGORY_LINKS[name];
      var link = el("a", "dr-discovery-category-link", dest[1]);
      link.href = dest[0];
      footer.appendChild(link);
    });
    var catalog = el("a", "dr-discovery-category-link", "Entire catalog");
    catalog.href = "/catalog"; footer.appendChild(catalog);
  }
  function init() {
    var layout = document.querySelector(".main-wrapper .product-grid-layout");
    var related = document.querySelector(".related-section");
    var grid = document.getElementById("related-grid");
    if (!layout || !related || !grid || document.querySelector(".dr-discovery-rail")) return;
    var left = layout.querySelector(".left-column");
    if (!left) return;

    var rail = el("aside", "dr-discovery-rail");
    rail.setAttribute("aria-label", "Discover more products");
    rail.appendChild(el("h2", "dr-discovery-rail-title", "Explore similar"));
    rail.appendChild(el("p", "dr-discovery-rail-caption", "Other listings from the catalog"));
    var railProducts = el("div", "dr-discovery-rail-products");
    // SSR fallback: existing 4 static, crawlable related links are preserved
    // in their original location even if the optional feed does not load.
    Array.prototype.slice.call(grid.querySelectorAll("a.rel-card"), 0, 4).forEach(function (a) {
      var title = a.querySelector(".rel-title");
      var price = a.querySelector(".rel-price");
      var img = a.querySelector("img");
      var p = { url:a.getAttribute("href"), title:title ? title.textContent : a.textContent.trim(),
                price:price ? price.textContent.replace(/[^\d.]/g,"") : "",
                thumbnail:img ? img.getAttribute("src") : "" };
      if (validUrl(p.url)) railProducts.appendChild(productAnchor(p,true));
    });
    rail.appendChild(railProducts);
    var railNav = el("div", "dr-discovery-rail-nav");
    var catalogLink = el("a", "dr-discovery-category-link", "Browse full catalog");
    catalogLink.href = "/catalog"; railNav.appendChild(catalogLink);
    rail.appendChild(railNav);
    layout.insertBefore(rail,left);
    document.documentElement.classList.add("dr-product-showcase");
    var shelf = el("div", "dr-discovery-shelves");
    shelf.setAttribute("aria-label", "Additional products to explore");
    related.insertAdjacentElement("afterend",shelf);

    fetch("/assets/catalog-index.json", { credentials:"same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("Catalog feed unavailable");
        return response.json();
      }).then(function (feed) {
        if (!Array.isArray(feed)) return;
        var current = productFromFeed(feed);
        if (!current || !validUrl(current.url)) return;
        // Account checkout: keep the original WhatsApp link and add a real USDT purchase link above it.
        var seller = document.getElementById("buy-btn");
        if (current.category === "Account" && seller && /\bbuy\s+now\b/i.test(seller.textContent) &&
            !document.getElementById("dr-usdt-buy") && Number.isFinite(Number(current.price)) && Number(current.price)>0) {
          var checkout = el("a", "whatsapp-btn", "Buy Now");
          checkout.id = "dr-usdt-buy";
          checkout.href = "/checkout-preview/?product=" + encodeURIComponent(current.url);
          checkout.style.marginBottom = "10px";
          seller.insertAdjacentElement("beforebegin",checkout);
          seller.textContent = "Chat with Seller";
          seller.style.background = "#155d39";
          seller.style.color = "#ffffff";
          seller.style.boxShadow = "none";
        }
        var ranked = rankSimilar(current,feed,Math.min(200,feed.length-1));
        var sameCategory = ranked.filter(function (p) { return p.category === current.category; });
        var relatedSource = new Set([current.url]);
        // Preserve static, SEO-crawlable related products; avoid duplicates
        // in the additional shelves and sidebar.
        grid.querySelectorAll("a.rel-card[href]").forEach(function (a) {
          relatedSource.add(a.getAttribute("href"));
        });
        var railMatches = sameCategory.slice(0,4);
        populateRail(rail,railMatches,current.category);
        var used = new Set([current.url]);
        railMatches.forEach(function (p) { used.add(p.url); });
        var featured = sameCategory.filter(function (p) {
          return !used.has(p.url) && !relatedSource.has(p.url);
        }).slice(0,8);
        featured.forEach(function (p) { used.add(p.url); });
        var categoryLink = CATEGORY_LINKS[current.category];
        var brand = brandOf(current);
        var featuredTitle = brand ? "More " + brand.charAt(0).toUpperCase() + brand.slice(1) + " and similar listings"
                                  : "More " + (categoryLink ? categoryLink[1] : "products");
        var first = makeSection(featuredTitle,featured,categoryLink && categoryLink[0],
          "Real listings matched by category and product features. Prices are in USD.");
        if (first) shelf.appendChild(first);
        var more = sameCategory.filter(function (p) {
          return !used.has(p.url) && !relatedSource.has(p.url) &&
            (!brand || brandOf(p) !== brand);
        }).slice(0,4);
        if (!more.length && sameCategory.length < 13) {
          more = ranked.filter(function (p) {
            return p.category !== current.category && !used.has(p.url) && !relatedSource.has(p.url);
          }).slice(0,4);
        }
        var second = makeSection(more.some(function (p) { return p.category !== current.category; })
          ? "Explore more on DigitalRacer"
          : "Other " + (categoryLink ? categoryLink[1] : "products"),more,
          more.some(function (p) { return p.category !== current.category; }) ? "/catalog" : categoryLink && categoryLink[0],
          "Browse alternative listings; confirm details and availability with the seller.");
        if (second) shelf.appendChild(second);
      }).catch(function () {
        // Related SSR links, prices and the existing Buy Now button stay
        // functional without this enhancement.
      });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded",init);
  else init();
})(typeof window !== "undefined" ? window : {});
