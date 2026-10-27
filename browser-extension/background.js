// Hands URLs to the shepherd native messaging host, which runs shepherd.py.

const HOST = "io.github.d1rewolf.shepherd";

function isRoutable(url) {
  try {
    const { protocol } = new URL(url);
    return protocol === "http:" || protocol === "https:";
  } catch {
    return false;
  }
}

async function sendToShepherd(url) {
  if (!isRoutable(url)) return { ok: false, error: `not an http(s) URL: ${url}` };
  try {
    const reply = await chrome.runtime.sendNativeMessage(HOST, { url });
    if (!reply?.ok) console.warn("shepherd host refused", url, reply);
    return reply ?? { ok: false, error: "empty reply from host" };
  } catch (err) {
    // Usually: host manifest missing from NativeMessagingHosts.
    console.error("shepherd host unreachable:", err.message);
    return { ok: false, error: err.message };
  }
}

async function flagFailure(reply) {
  if (reply.ok) return;
  await chrome.action.setBadgeBackgroundColor({ color: "#c0392b" });
  await chrome.action.setBadgeText({ text: "!" });
  await chrome.action.setTitle({ title: `Shepherd: ${reply.error}` });
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "open-link",
    title: "Open link with Shepherd",
    contexts: ["link"],
  });
  chrome.contextMenus.create({
    id: "open-page",
    title: "Open page with Shepherd",
    contexts: ["page"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const url = info.menuItemId === "open-link" ? info.linkUrl : tab?.url;
  await flagFailure(await sendToShepherd(url));
});

chrome.action.onClicked.addListener(async (tab) => {
  await chrome.action.setBadgeText({ text: "" });
  await flagFailure(await sendToShepherd(tab.url));
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type !== "open") return false;
  sendToShepherd(msg.url).then(async (reply) => {
    await flagFailure(reply);
    sendResponse(reply);
  });
  return true; // keep the channel open for the async reply
});
