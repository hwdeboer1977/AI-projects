import "dotenv/config";
import express from "express";
import cors from "cors";
import rateLimit from "express-rate-limit";

import { summarizeAdd } from "../tools/summarize_add.js";
import { summarizeStrict } from "../tools/summarize_strict.js";
import { summarizeText } from "../tools/summarize_text.js";

const app = express();

/* ---------------------------------------------
   Middleware
---------------------------------------------- */

app.use(cors({ origin: true }));
app.use(express.json({ limit: "1mb" }));

app.use(
  "/v1/",
  rateLimit({
    windowMs: 60_000,
    max: 30,
    standardHeaders: true,
    legacyHeaders: false,
  })
);

/* ---------------------------------------------
   Health check
---------------------------------------------- */

app.get("/health", (_, res) => {
  res.json({ ok: true });
});

/* ---------------------------------------------
   Summarize URL
---------------------------------------------- */

app.post("/v1/summarize/url", async (req, res) => {
  try {
    const { url, mode = "strict", depth = "medium" } = req.body || {};

    if (!url) throw new Error("Missing url");
    if (!["strict", "add"].includes(mode))
      throw new Error("mode must be 'strict' or 'add'");
    if (!["short", "medium", "long"].includes(depth))
      throw new Error("depth must be short | medium | long");

    const result =
      mode === "add"
        ? await summarizeAdd({ url, depth })
        : await summarizeStrict({ url, depth });

    res.json({
      ok: true,
      mode: result.mode,
      depth: result.depth,
      url: result.url,
      finalUrl: result.finalUrl,
      title: result.title,
      markdown: result.markdown,
      meta: result.meta,
    });
  } catch (err) {
    res.status(400).json({
      ok: false,
      error: err.message || "Unknown error",
    });
  }
});

app.post("/v1/summarize/text", async (req, res) => {
  try {
    const {
      content,
      title = "",
      url = "",
      mode = "strict",
      depth = "medium",
    } = req.body || {};

    const result = await summarizeText({ content, title, url, mode, depth });

    res.json({
      ok: true,
      mode: result.mode,
      depth: result.depth,
      url: result.url,
      title: result.title,
      markdown: result.markdown,
      meta: result.meta,
    });
  } catch (err) {
    res.status(400).json({
      ok: false,
      error: err.message || "Unknown error",
    });
  }
});

/* ---------------------------------------------
   Start server
---------------------------------------------- */

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`🚀 Web Summary API running on http://localhost:${PORT}`);
});
