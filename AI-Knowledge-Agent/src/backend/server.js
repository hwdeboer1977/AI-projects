import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { answerQuestion } from "../rag/answer.js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json({ limit: "1mb" }));

app.get("/health", (req, res) => res.json({ ok: true }));

app.post("/ask", async (req, res) => {
  try {
    const { question, topK } = req.body || {};
    if (!question || typeof question !== "string") {
      return res.status(400).json({ error: "Missing 'question' (string)" });
    }

    const result = await answerQuestion(question, { topK: topK ?? 6 });
    res.json(result);
  } catch (err) {
    console.error("ASK ERROR:", err);
    res
      .status(500)
      .json({ error: "Internal error", details: String(err?.message || err) });
  }
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`API running on http://localhost:${PORT}`);
});
