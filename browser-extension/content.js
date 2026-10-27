// Alt-click on a link sends it to shepherd instead of navigating.
// Capture phase so page handlers (and Chromium's Alt-click-to-download)
// never see the click.

function linkFrom(event) {
  for (const node of event.composedPath()) {
    if (node instanceof Element && node.matches("a[href], area[href]")) return node;
  }
  return null;
}

window.addEventListener(
  "click",
  (event) => {
    if (event.button !== 0 || !event.altKey) return;
    if (event.ctrlKey || event.metaKey || event.shiftKey) return;
    const link = linkFrom(event);
    if (!link) return;

    event.preventDefault();
    event.stopImmediatePropagation();
    chrome.runtime.sendMessage({ type: "open", url: link.href });
  },
  true,
);
