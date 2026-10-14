// Language switch shared by the subpages: same storage key as index.html, so the choice follows the visitor.
(function () {
  var root = document.documentElement;
  var titles = { sv: root.getAttribute("data-title-sv"), en: root.getAttribute("data-title-en") };
  function setLang(lang) {
    root.setAttribute("data-lang", lang);
    root.setAttribute("lang", lang);
    if (titles[lang]) document.title = titles[lang];
    document.querySelectorAll("[data-set-lang]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-set-lang") === lang));
    });
    try { localStorage.setItem("tt-lang", lang); } catch (e) {}
  }
  var saved = null;
  try { saved = localStorage.getItem("tt-lang"); } catch (e) {}
  var browser = (navigator.language || "sv").toLowerCase().indexOf("sv") === 0 ? "sv" : "en";
  setLang(saved || browser);
  document.querySelectorAll("[data-set-lang]").forEach(function (b) {
    b.addEventListener("click", function () { setLang(b.getAttribute("data-set-lang")); });
  });
})();
