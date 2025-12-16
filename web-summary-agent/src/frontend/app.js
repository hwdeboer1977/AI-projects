const $ = (id) => document.getElementById(id);

const apiBaseEl = $("apiBase");
const urlEl = $("url");
const modeEl = $("mode");
const depthEl = $("depth");

const summarizeBtn = $("summarizeBtn");
const copyBtn = $("copyBtn");
const clearBtn = $("clearBtn");

const statusEl = $("status");
const titleEl = $("title");
const finalUrlEl = $("finalUrl");

const markdownEl = $("markdown");
const previewEl = $("preview");

function setStatus(msg) {
  statusEl.textContent = msg || "";
}

function setLoading(isLoading) {
  summarizeBtn.disabled = isLoading;
  summarizeBtn.textContent = isLoading ? "Summarizing..." : "Summarize";
}

function renderMarkdown(md) {
  if (!md || !md.trim()) {
    previewEl.innerHTML = "Nothing yet.";
    return;
  }
  previewEl.innerHTML = marked.parse(md);
}

async function summarizeUrl() {
  const apiBase = apiBaseEl.value.trim().replace(/\/+$/, "");
  const url = urlEl.value.trim();
  const mode = modeEl.value;
  const depth = depthEl.value;

  if (!apiBase) {
    setStatus("Backend URL missing.");
    return;
  }
  if (!url) {
    setStatus("Please paste a URL.");
    return;
  }

  setLoading(true);
  setStatus("Calling backend...");
  copyBtn.disabled = true;

  titleEl.textContent = "—";
  finalUrlEl.textContent = "—";
  finalUrlEl.href = "#";

  markdownEl.value = "";
  renderMarkdown("");

  try {
    const res = await fetch(`${apiBase}/v1/summarize/url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, mode, depth }),
    });

    const data = await res.json();

    if (!res.ok || !data.ok) {
      throw new Error(data?.error || `Request failed (${res.status})`);
    }

    titleEl.textContent = data.title || "—";
    finalUrlEl.textContent = data.finalUrl || data.url || "—";
    finalUrlEl.href = data.finalUrl || data.url || "#";

    markdownEl.value = data.markdown || "";
    renderMarkdown(data.markdown || "");

    copyBtn.disabled = !(data.markdown && data.markdown.trim());
    setStatus(`Done. mode=${data.mode}, depth=${data.depth}`);
  } catch (err) {
    setStatus(`Error: ${err.message}`);
  } finally {
    setLoading(false);
  }
}

summarizeBtn.addEventListener("click", summarizeUrl);

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(markdownEl.value || "");
    setStatus("Copied markdown to clipboard.");
  } catch {
    setStatus("Copy failed (browser permissions).");
  }
});

clearBtn.addEventListener("click", () => {
  urlEl.value = "";
  markdownEl.value = "";
  titleEl.textContent = "—";
  finalUrlEl.textContent = "—";
  finalUrlEl.href = "#";
  renderMarkdown("");
  setStatus("");
  copyBtn.disabled = true;
});
