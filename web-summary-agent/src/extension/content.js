(function () {
  // Try to pick the main content area if present
  const main =
    document.querySelector("main") ||
    document.querySelector("article") ||
    document.body;

  // Remove obvious noise
  const clone = main.cloneNode(true);
  clone
    .querySelectorAll("nav, header, footer, aside, script, style")
    .forEach((n) => n.remove());

  const text = clone.innerText || "";
  return {
    title: document.title || "",
    url: location.href,
    content: text.trim(),
  };
})();
