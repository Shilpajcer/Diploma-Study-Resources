// Press "/" anywhere to jump to the search box (like GitHub / YouTube).
document.addEventListener("keydown", function (e) {
  const tag = document.activeElement ? document.activeElement.tagName : "";
  if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/i.test(tag)) {
    const search = document.querySelector("[data-search-focus]");
    if (search) {
      e.preventDefault();
      search.focus();
    }
  }
});
