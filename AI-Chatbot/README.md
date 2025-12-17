# Bolder Outdoor Customer Support Chatbot

A customer support chatbot POC for Bolder Outdoor, a fictional e-commerce outdoor gear store.

## Tech Stack

- **Frontend:** React + Vite
- **Backend:** Node.js + Express
- **AI:** OpenAI GPT-4o-mini
- **Styling:** Custom CSS with Bolder brand colors

## Features

- 💬 Conversational AI customer support
- 🏔️ Polished outdoor-themed UI
- 📦 Full knowledge of products, shipping, returns, and policies
- ⚡ Quick action buttons for common questions
- 📱 Responsive design
- ♿ Accessibility support

## Project Structure

```
bolder-chatbot/
├── backend/
│   ├── package.json
│   ├── server.js           # Express API server
│   ├── systemPrompt.js     # AI knowledge base
│   └── .env                # Environment variables
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js      # Vite configuration
│   ├── index.html          # Entry HTML
│   └── src/
│       ├── main.jsx        # React entry point
│       ├── App.jsx         # Main app component
│       ├── App.css         # Styles
│       └── components/
│           └── ChatWidget.jsx
│
└── README.md
```

## Prerequisites

- Node.js 18+ installed
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

## Setup

### 1. Backend Setup

```bash
cd backend
```

Create `package.json`:

```json
{
  "name": "bolder-chatbot-backend",
  "version": "1.0.0",
  "description": "Backend for Bolder Outdoor customer support chatbot",
  "main": "server.js",
  "type": "module",
  "scripts": {
    "start": "node server.js",
    "dev": "node --watch server.js"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.21.0",
    "openai": "^4.67.1"
  }
}
```

Install dependencies:

```bash
npm install
```

Create `.env` file:

```
OPENAI_API_KEY=sk-your-api-key-here
PORT=3000
```

Start the backend:

```bash
npm run dev
```

You should see:

```
🏔️  Bolder Outdoor Chatbot API running on http://localhost:3000
```

### 2. Frontend Setup

Open a new terminal:

```bash
cd frontend
```

Create `package.json`:

```json
{
  "name": "bolder-chatbot-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.6"
  }
}
```

Install dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

### 3. Open the App

Navigate to [http://localhost:5173](http://localhost:5173)

## Customization

### Changing the Company

Edit `backend/systemPrompt.js` to update:

- Company name and branding
- Product catalog
- Policies (shipping, returns, etc.)
- Support scenarios

### Styling

Edit `frontend/src/App.css` — CSS variables at the top control the color scheme:

```css
:root {
  --forest-dark: #1a3d28;
  --forest: #2d5a3d;
  --forest-light: #4a7c59;
  --sage: #8fbc8f;
  /* ... */
}
```

### Model Selection

In `backend/server.js`, change the model:

```javascript
model: 'gpt-4o-mini',  // or 'gpt-4o' for better quality
```

## API Endpoints

### POST /api/chat

Send a message and get a response.

**Request:**

```json
{
  "messages": [{ "role": "user", "content": "What's your return policy?" }]
}
```

**Response:**

```json
{
  "message": "We offer a 30-day return window...",
  "usage": { "prompt_tokens": 123, "completion_tokens": 45 }
}
```

### GET /api/health

Health check endpoint.

## Cost Estimation

GPT-4o-mini pricing (as of late 2024):

- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens

With the ~3,500 token system prompt, expect roughly:

- ~$0.0005 per message exchange
- ~$0.50 per 1,000 conversations

## Troubleshooting

### "Missing script: dev"

Make sure your `package.json` includes the scripts section and has `"type": "module"`.

### API Key Error

Check that your `.env` file exists in the backend folder and contains a valid OpenAI API key.

### CORS Errors

Make sure the backend is running on port 3000 and the frontend proxy in `vite.config.js` points to `http://localhost:3000`.

## Next Steps

Ideas for extending the POC:

- [ ] Add streaming responses
- [ ] Implement ticket creation (collect email, order number)
- [ ] Connect to a real product database
- [ ] Add conversation persistence
- [ ] Deploy to Vercel/Railway
- [ ] Add WhatsApp/Twilio integration
- [ ] Implement analytics dashboard

## License

MIT - Feel free to use this as a starting point for your own projects.
