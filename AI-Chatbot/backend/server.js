import express from "express";
import cors from "cors";
import OpenAI from "openai";
import dotenv from "dotenv";
import { systemPrompt } from "./systemPrompt.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Middleware
app.use(cors());
app.use(express.json());

// Health check
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", message: "Bolder Outdoor Chatbot API is running" });
});

// Chat endpoint
app.post("/api/chat", async (req, res) => {
  try {
    const { messages } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({
        error: "Invalid request. Messages array required.",
      });
    }

    // Build conversation with system prompt
    const conversation = [
      { role: "system", content: systemPrompt },
      ...messages,
    ];

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: conversation,
      temperature: 0.7,
      max_tokens: 1000,
    });

    const assistantMessage = completion.choices[0].message.content;

    res.json({
      message: assistantMessage,
      usage: completion.usage,
    });
  } catch (error) {
    console.error("OpenAI API error:", error);

    if (error.code === "invalid_api_key") {
      return res.status(401).json({
        error: "Invalid API key. Please check your OPENAI_API_KEY.",
      });
    }

    res.status(500).json({
      error: "Something went wrong. Please try again.",
    });
  }
});

app.listen(PORT, () => {
  console.log(
    `🏔️  Bolder Outdoor Chatbot API running on http://localhost:${PORT}`
  );
  console.log(`   Health check: http://localhost:${PORT}/api/health`);
});
