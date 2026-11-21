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
