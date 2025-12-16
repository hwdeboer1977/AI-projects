const $ = (id) => document.getElementById(id);

const apiBaseEl = $("apiBase");
const modeEl = $("mode");
const depthEl = $("depth");
const summarizeBtn = $("summarizeBtn");
const statusEl = $("status");

const titleEl = $("title");
const urlEl = $("url");

const markdownEl = $("markdown");
const previewEl = $("preview");
const copyBtn = $("copyBtn");

function setStatus(msg) {
  statusEl.textContent = msg || "";
}

function render(md) {
  if (!md || !md.trim()) {
    previewEl.textContent = "Nothing yet.";
    return;
  }
  previewEl.innerHTML = marked.parse(md);
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function extractFromTab(tabId) {
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => {
      const main =
        document.querySelector("main") ||
        document.querySelector("article") ||
        document.body;

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
    },
  });

  return result;
}

async function summarizeCurrentPage() {
  const apiBase = apiBaseEl.value.trim().replace(/\/+$/, "");
  const mode = modeEl.value;
  const depth = depthEl.value;

  markdownEl.value = "";
  render("");
  copyBtn.disabled = true;

  if (!apiBase) return setStatus("Backend URL missing.");

  summarizeBtn.disabled = true;
  summarizeBtn.textContent = "Summarizing...";
  setStatus("Extracting content from the page...");

  try {
    const tab = await getActiveTab();
    if (!tab?.id) throw new Error("No active tab");

    const extracted = await extractFromTab(tab.id);

    if (!extracted?.content || extracted.content.length < 50) {
      throw new Error("Could not extract enough text from this page.");
    }

    titleEl.textContent = extracted.title || "—";
    urlEl.textContent = extracted.url || "—";
    urlEl.href = extracted.url || "#";

    setStatus("Sending to backend...");

    const res = await fetch(`${apiBase}/v1/summarize/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: extracted.title,
        url: extracted.url,
        content: extracted.content,
        mode,
        depth,
      }),
    });

    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data?.error || "Request failed");

    markdownEl.value = data.markdown || "";
    render(data.markdown || "");
    copyBtn.disabled = !(data.markdown && data.markdown.trim());
    setStatus(`Done. mode=${data.mode}, depth=${data.depth}`);
  } catch (e) {
    setStatus(`Error: ${e.message}`);
  } finally {
    summarizeBtn.disabled = false;
    summarizeBtn.textContent = "Summarize current page";
  }
}

summarizeBtn.addEventListener("click", summarizeCurrentPage);

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(markdownEl.value || "");
    setStatus("Copied markdown to clipboard.");
  } catch {
    setStatus("Copy failed (clipboard permission).");
  }
});
