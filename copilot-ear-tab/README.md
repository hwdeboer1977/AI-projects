# Copilot Ear (Tab Audio Version)

🔊 A Chrome extension that captures audio from browser tabs, transcribes it using Deepgram, and provides AI-powered suggestions using Groq.

![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-purple)
![License](https://img.shields.io/badge/License-MIT-blue)

## Features

- **Tab audio capture** - transcribes what's playing in a Chrome tab
- **Professional transcription** using Deepgram Nova-2 (high accuracy)
- **AI-powered suggestions** using Groq's fast LLM inference
- **Audio passthrough** - you can still hear the tab audio while capturing
- **Real-time interim results** - see transcription as it happens
- **Auto-detection** of questions and commands

## Use Cases

- **Interview preparation**: Capture interviewer questions from video calls (Google Meet, Zoom Web, Teams Web)
- **Meeting notes**: Transcribe meetings happening in the browser
- **Video learning**: Get AI explanations while watching tutorials
- **Podcast assistance**: Get summaries and context from audio content

## Installation

1. Download and unzip `copilot-ear-tab.zip`
2. Open Chrome and go to `chrome://extensions`
3. Enable **Developer mode** (toggle in top right)
4. Click **Load unpacked**
5. Select the `copilot-ear-tab` folder

## Setup

### 1. Get a Deepgram API key (for transcription)

- Go to [console.deepgram.com](https://console.deepgram.com)
- Sign up (free - includes **$200 credit**)
- Create an API key

### 2. Get a Groq API key (for AI suggestions)

- Go to [console.groq.com](https://console.groq.com)
- Sign up (free)
- Create an API key (starts with `gsk_`)

### 3. Configure the extension

- Click the Copilot Ear extension icon (purple speaker icon)
- Enter both API keys and click **Save** for each

## Usage

1. **Open a tab with audio**:

   - YouTube video
   - Google Meet call
   - Zoom Web meeting
   - Any webpage playing audio

2. **Click the extension icon** to open the popup

3. **Click "🔊 Capture Tab Audio"**

4. **Audio will be transcribed** in real-time

   - You can still hear the audio through your speakers
   - Transcript appears in the panel
   - Questions are auto-detected and sent to AI

5. **Click "Stop Capture"** when done

### Manual AI Request

Click the **Ask AI** button to send the current transcript to the AI at any time.

### Reset

Click **Reset** to clear the transcript and start fresh.

## How It Works

```
Tab Audio → Chrome Tab Capture API → Deepgram WebSocket → Transcript
                                                              ↓
                                         Groq API ← Question Detection
                                              ↓
                                        AI Suggestion
```

1. Chrome's Tab Capture API captures audio from the active tab
2. Audio is streamed to Deepgram via WebSocket for real-time transcription
3. Audio is also routed back to your speakers (passthrough)
4. When a question is detected, it's sent to Groq for an AI response

## Troubleshooting

### "No audio stream - make sure the tab has audio"

- Make sure the tab is actually playing audio
- Some tabs may block audio capture
- Try refreshing the page and capturing again

### Can't hear the audio

- Make sure your volume is turned up
- Check that the correct output device is selected
- The audio should play through your default speakers

### Transcription not appearing

- Check your Deepgram API key is valid
- Make sure the audio is clear speech (not just music)
- Check the browser console for errors (F12 → Console)

### Poor transcription quality

- Deepgram works best with clear speech
- Background noise can affect accuracy
- Try the `nova-2` model (default) for best results

## Tech Stack

- **Audio Capture**: Chrome Tab Capture API
- **Transcription**: Deepgram Nova-2 (WebSocket streaming)
- **AI Model**: Groq Llama 3.1 8B Instant
- **Architecture**: Chrome Extension Manifest V3

## File Structure

```
copilot-ear-tab/
├── manifest.json    # Extension configuration
├── popup.html       # Extension popup UI
├── popup.js         # Main logic (capture, transcription, API calls)
└── icon.png         # Extension icon (purple)
```

## Privacy

- Audio is streamed to Deepgram for transcription
- Questions are sent to Groq for AI responses
- No data is permanently stored
- API keys are stored locally in your browser
- Review [Deepgram's privacy policy](https://deepgram.com/privacy) and [Groq's terms](https://groq.com/terms)

## Limitations

- Only captures audio from **one Chrome tab at a time**
- Cannot capture audio from **desktop apps** (Zoom app, Discord, etc.)
- Popup must stay open during capture
- Requires internet connection for transcription

## Cost

| Service         | Cost             | Free Tier                |
| --------------- | ---------------- | ------------------------ |
| Deepgram Nova-2 | ~$0.0059/min     | $200 credit (~560 hours) |
| Groq            | ~$0.05/1M tokens | Generous free tier       |

For typical use (a few hours of meetings per week), you'll likely stay within free tiers.

## Comparison: Mic vs Tab Version

| Feature                | Mic Version    | Tab Version       |
| ---------------------- | -------------- | ----------------- |
| Captures your voice    | ✅             | ❌                |
| Captures tab audio     | ❌             | ✅                |
| Captures meeting audio | ❌             | ✅ (web meetings) |
| Transcription          | Browser (free) | Deepgram (paid)   |
| Accuracy               | Variable       | High              |
| Works offline          | Partially      | No                |

**Use Mic Version** if you want to capture what **you** say.

**Use Tab Version** if you want to capture what **others** say in a meeting or video.

## License

MIT License - feel free to modify and distribute.

## Credits

Built with Claude (Anthropic) as a coding assistant experiment.
