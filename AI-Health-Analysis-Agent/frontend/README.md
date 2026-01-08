# Health Dashboard Frontend

A React-based health tracking dashboard that visualizes nutrition and exercise data from the AI Health Analysis Agent backend.

![React](https://img.shields.io/badge/React-19.2-61dafb?logo=react)
![Vite](https://img.shields.io/badge/Vite-7.2-646cff?logo=vite)
![Recharts](https://img.shields.io/badge/Recharts-3.6-22d3ee)

## Overview

This frontend provides a visual interface for tracking daily health metrics including calorie intake, macronutrients (protein, carbs, fat), and exercise minutes. It connects to a Python backend that aggregates data from Google Fitness and nutrition sources.

## Features

- **Daily Nutrition Tracking** — Calorie consumption with circular progress indicator and remaining/over display
- **Macro Breakdown** — Protein, carbs, and fat progress bars against daily targets
- **Exercise Monitoring** — Daily minutes, session counts, and exercise type breakdowns
- **7-Day Trends** — Line chart for calorie history and bar chart for exercise minutes
- **Weekly Summary** — Aggregated stats including averages and logging streaks
- **Day Selector** — Navigate between the last 7 days of data

## Tech Stack

| Package  | Version | Purpose                      |
| -------- | ------- | ---------------------------- |
| React    | 19.2    | UI framework                 |
| Vite     | 7.2     | Build tool & dev server      |
| Recharts | 3.6     | Charts (LineChart, BarChart) |
| ESLint   | 9.39    | Code linting                 |

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── HealthDashboard.jsx   # Main dashboard component
│   │   └── HealthDashboard.css   # Dashboard styles
│   ├── api.js                    # API client functions
│   ├── App.jsx                   # Root component
│   ├── index.css                 # Global styles
│   └── main.jsx                  # Entry point
├── public/                       # Static assets
├── .env                          # Environment variables
├── index.html                    # HTML template
├── package.json
├── vite.config.js
└── eslint.config.js
```

## Getting Started

### Prerequisites

- Node.js 18+
- Backend server running (default: `http://localhost:5000`)

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create a `.env` file (or modify the existing one):

```env
VITE_API_URL=http://localhost:5000
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:5173`

### Production Build

```bash
npm run build
npm run preview
```

Build output goes to `dist/`.

## API Integration

The frontend consumes three endpoints from the backend:

| Function                | Endpoint                | Description                           |
| ----------------------- | ----------------------- | ------------------------------------- |
| `fetchHealthData(days)` | `GET /api/health/:days` | Fetch nutrition & exercise for N days |
| `fetchTodayData()`      | `GET /api/health/today` | Fetch today's data only               |
| `fetchTargets()`        | `GET /api/targets`      | Fetch daily macro/calorie targets     |

### Expected Response Format

```json
{
  "success": true,
  "data": [
    {
      "date": "2026-01-08",
      "nutrition": {
        "calories": 1850,
        "protein": 145,
        "carbs": 200,
        "fat": 55
      },
      "exercise": { "minutes": 45, "sessions": 1, "types": { "Strength": 1 } }
    }
  ],
  "targets": { "calories": 2130, "protein": 160, "carbs": 240, "fat": 60 }
}
```

## Scripts

| Command           | Description              |
| ----------------- | ------------------------ |
| `npm run dev`     | Start development server |
| `npm run build`   | Build for production     |
| `npm run preview` | Preview production build |
| `npm run lint`    | Run ESLint               |

## Related

This frontend is part of the **AI-Health-Analysis-Agent** project which includes:

- `health-analysis-agent.py` — Main backend server
- `ai_conversational.py` — AI chat interface for health queries
- `ai_daily_suggestions.py` — Daily AI-generated health recommendations
- `ai_weekly_suggestions.py` — Weekly AI summaries
- Google Sheets integration for fitness and nutrition data

## License

MIT
