/* Product-first catalog sidebar. No extra product fetches or scroll listeners. */
(function () {
  "use strict";
  function init() {
    var sidebar = document.getElementById("catalog-sidebar");
    var toggle = document.getElementById("catalog-filter-open");
    var closeButton = document.getElementById("catalog-filter-close");
    var backdrop = document.getElementById("catalog-sidebar-backdrop");
    var selected = document.getElementById("catalog-filter-current");
    var results = document.getElementById("catalog-results");
    if (!sidebar || !toggle || !closeButton || !backdrop) return;
    var mobile = window.matchMedia("(max-width: 930px)");
    var previousFocus = null;

    function updateCategory() {
      var current = sidebar.querySelector(".filter-btn.active");
      if (!current || !selected) return;
      var label = current.textContent.trim();
      selected.textContent = label === "All" ? "All" : label;
      toggle.setAttribute("aria-label", "Filter products. Current category: " + label);
    }

    function openDrawer() {
      if (!mobile.matches || document.body.classList.contains("catalog-filters-open")) return;
      previousFocus = document.activeElement;
      backdrop.hidden = false;
      document.body.classList.add("catalog-filters-open");
      sidebar.setAttribute("role", "dialog");
      sidebar.setAttribute("aria-modal", "true");
      toggle.setAttribute("aria-expanded", "true");
      closeButton.focus();
    }

    function closeDrawer(restore) {
      if (!document.body.classList.contains("catalog-filters-open")) return;
      document.body.classList.remove("catalog-filters-open");
      backdrop.hidden = true;
      sidebar.removeAttribute("role");
      sidebar.removeAttribute("aria-modal");
      toggle.setAttribute("aria-expanded", "false");
      if (restore !== false && previousFocus && typeof previousFocus.focus === "function")
        previousFocus.focus();
    }

    toggle.addEventListener("click", openDrawer);
    closeButton.addEventListener("click", function () { closeDrawer(true); });
    backdrop.addEventListener("click", function () { closeDrawer(true); });
    document.addEventListener("keydown", function (event) {
      if (!document.body.classList.contains("catalog-filters-open")) return;
      if (event.key === "Escape") { event.preventDefault(); closeDrawer(true); return; }
      if (event.key !== "Tab") return;
      var focusables = Array.prototype.filter.call(
        sidebar.querySelectorAll('button:not([disabled]),a[href],summary,select:not([disabled]),input:not([disabled])'),
        function (el) { return !el.hasAttribute("hidden"); }
      );
      if (!focusables.length) return;
      var first = focusables[0], last = focusables[focusables.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    });

    sidebar.querySelectorAll(".filter-btn").forEach(function (button) {
      button.addEventListener("click", function () {
        updateCategory();
        if (mobile.matches && document.body.classList.contains("catalog-filters-open")) {
          closeDrawer(false);
          toggle.focus();
          if (results && typeof results.scrollIntoView === "function")
            results.scrollIntoView({ block: "start", behavior: "auto" });
        }
      });
    });
    if (typeof mobile.addEventListener === "function")
      mobile.addEventListener("change", function () { closeDrawer(false); });
    else if (typeof mobile.addListener === "function")
      mobile.addListener(function () { closeDrawer(false); });
    updateCategory();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
