# Copilot Code (Web Version)

🖥️ AI-powered screen analyzer using your browser for video capture. Much more stable than the desktop version!

## Why Web Version?

- ✅ **Stable** - Browser handles video, no freezing
- ✅ **Smooth video** - Browsers are optimized for webcam/video
- ✅ **Simple** - Just Flask + HTML, minimal dependencies
- ✅ **Cross-platform** - Works on Windows, Mac, Linux

## Installation

```bash
pip install flask openai
```

## Usage

1. **Start the server:**
   ```bash
   python app.py
   ```

2. **Open browser:**
   ```
   http://localhost:5000
   ```

3. **Select your capture card** from the camera dropdown

4. **Enter OpenAI API key** and click Save

5. **Click "Analyze Screen"** or press F2

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| F2 | Analyze screen |
| F3 | Custom question |
| F4 | Clear chat |
| Enter | Send follow-up question |

## Hardware Setup

```
Desktop PC ──HDMI──▶ Capture Card ──USB──▶ Laptop
                                            │
                                   Browser shows video
                                   Flask sends to GPT-4o
```

## Troubleshooting

### Camera not showing
- Allow camera permission when browser asks
- Check if capture card is connected
- Try refreshing the page

### "Camera access denied"
- Click the camera icon in browser address bar
- Allow access to camera
- Refresh page

### Video is mirrored
- This is normal for webcams
- Capture cards usually show correct orientation

## Cost

- OpenAI GPT-4o Vision: ~$0.01-0.03 per analysis
- Much cheaper than GPT-4 Turbo

## Files

```
copilot-code-web/
├── app.py              # Flask server
├── requirements.txt    # Dependencies
├── templates/
│   └── index.html      # Web UI
└── config.json         # Saved API key (created on first use)
```
