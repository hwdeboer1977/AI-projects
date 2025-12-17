"use client";

import { useState } from "react";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [error, setError] = useState("");

  async function ask() {
    setLoading(true);
    setError("");
    setAnswer("");
    setSources([]);

    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:4000";
      const res = await fetch(`${base}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, topK: 6 }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Request failed");

      setAnswer(data.answer || "");
      setSources(data.sources || []);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        maxWidth: 900,
        margin: "40px auto",
        padding: 16,
        fontFamily: "system-ui",
      }}
    >
      <h1 style={{ fontSize: 28, marginBottom: 8 }}>AI Knowledge Agent</h1>
      <p style={{ color: "#555", marginBottom: 16 }}>
        Ask questions about ingested policies / docs. Answers include sources.
      </p>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask something…"
          style={{
            flex: 1,
            padding: "12px 14px",
            border: "1px solid #ddd",
            borderRadius: 10,
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (!loading && question.trim()) ask();
            }
          }}
        />
        <button
          onClick={ask}
          disabled={loading || !question.trim()}
          style={{
            padding: "12px 16px",
            borderRadius: 10,
            border: "1px solid #ddd",
            background: loading ? "#f5f5f5" : "white",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Asking…" : "Ask"}
        </button>
      </div>

      {error && (
        <div
          style={{
            marginTop: 14,
            padding: 12,
            borderRadius: 10,
            border: "1px solid #f2b8b5",
            background: "#fff5f5",
          }}
        >
          <b>Error:</b> {error}
        </div>
      )}

      {answer && (
        <div
          style={{
            marginTop: 18,
            padding: 16,
            borderRadius: 12,
            border: "1px solid #eee",
          }}
        >
          <h2 style={{ margin: 0, marginBottom: 10, fontSize: 18 }}>Answer</h2>
          <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
            {answer}
          </div>
        </div>
      )}

      {sources?.length > 0 && (
        <div
          style={{
            marginTop: 14,
            padding: 16,
            borderRadius: 12,
            border: "1px solid #eee",
          }}
        >
          <h2 style={{ margin: 0, marginBottom: 10, fontSize: 18 }}>Sources</h2>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {sources.map((s, i) => (
              <li key={i} style={{ marginBottom: 8 }}>
                <b>{s.ref}</b>{" "}
                {s.source ? (
                  <a href={s.source} target="_blank" rel="noreferrer">
                    {s.source}
                  </a>
                ) : (
                  <span>(no url)</span>
                )}
                {typeof s.chunk_index === "number" ? (
                  <span> — chunk {s.chunk_index}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}
