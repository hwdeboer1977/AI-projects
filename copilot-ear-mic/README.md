# Copilot Ear (Microphone Version)

🎧 A Chrome extension that listens to your microphone, transcribes speech in real-time, and provides AI-powered suggestions using Groq.

![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-green)
![License](https://img.shields.io/badge/License-MIT-blue)

## Features

- **Real-time speech-to-text** using Chrome's built-in Web Speech API (free)
- **AI-powered suggestions** using Groq's fast LLM inference
- **Auto-detection** of questions and commands
- **Manual "Ask AI" button** for any transcript
- **Reset button** to clear transcript and start fresh
- **Draggable overlay** that works on any webpage

## Use Cases

- Technical interview preparation
- Meeting assistance
- Quick fact-checking during calls
- Language learning practice

## Installation

1. Download and unzip `copilot-ear-mic.zip`
2. Open Chrome and go to `chrome://extensions`
3. Enable **Developer mode** (toggle in top right)
4. Click **Load unpacked**
5. Select the `copilot-ear-mic` folder

## Setup

**Get a Groq API key** (free):

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up and create an API key (starts with `gsk_`)
3. Navigate to any webpage (e.g., wikipedia.org)
4. Click the Copilot Ear extension icon
5. Paste your Groq API key and click **Save**

## Usage

1. Go to a webpage (avoid Google.com as it has its own voice features that may conflict)
2. Click the extension icon to open the overlay
3. Click **Start Listening**
4. Allow microphone access when prompted
5. Speak a question or statement
6. The transcript appears in real-time
7. Questions are automatically detected and sent to AI for suggestions

### Trigger Words

The AI is automatically triggered when it detects:

- Question marks (`?`)
- Question words: what, how, why, when, where, who, which
- Command words: explain, tell me, show me, give me, provide, create, write, make, list, describe

### Manual AI Request

Click the **Ask AI** button to send the current transcript to the AI at any time.

## Troubleshooting

### "Speech error: aborted"

- Close other tabs that might be using the microphone (WhatsApp Web, Google Meet, etc.)
- Try a different webpage (some sites like Google.com have voice features that conflict)
- Make sure you're not in Chrome's device emulation mode

### "Microphone access denied"

- Click the lock icon in the address bar
- Set Microphone to **Allow**
- Refresh the page

### No transcript appearing

- Speak louder and closer to the microphone
- Check that the correct microphone is selected in Chrome settings
- Try a different webpage

## Tech Stack

- **Speech Recognition**: Web Speech API (browser-native, free)
- **AI Model**: Groq Llama 3.1 8B Instant (free tier available)
- **Architecture**: Chrome Extension Manifest V3

## File Structure

```
copilot-ear-mic/
├── manifest.json    # Extension configuration
├── background.js    # Service worker for icon clicks
├── content.js       # Main logic (overlay, speech recognition, API calls)
└── icon.png         # Extension icon
```

## Privacy

- Audio is processed locally by Chrome's Speech Recognition
- Only detected questions are sent to Groq's API
- No data is stored or logged
- API keys are stored locally in your browser

## Limitations

- Only captures microphone audio (not system/tab audio)
- Requires an active internet connection
- Web Speech API accuracy varies by accent and background noise
- Only one tab can use speech recognition at a time

## Cost

| Service               | Cost                  |
| --------------------- | --------------------- |
| Speech Recognition    | Free (browser-native) |
| AI Suggestions (Groq) | Free tier available   |

## License

MIT License - feel free to modify and distribute.

## Credits

Built with Claude (Anthropic) as a coding assistant experiment.
