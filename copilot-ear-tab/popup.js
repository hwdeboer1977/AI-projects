// Elements
const deepgramKeyInput = document.getElementById('deepgramKey');
const groqKeyInput = document.getElementById('groqKey');
const saveDeepgramBtn = document.getElementById('saveDeepgram');
const saveGroqBtn = document.getElementById('saveGroq');
const captureBtn = document.getElementById('captureBtn');
const resetBtn = document.getElementById('resetBtn');
const askBtn = document.getElementById('askBtn');
const statusEl = document.getElementById('status');
const transcriptEl = document.getElementById('transcript');
const suggestionEl = document.getElementById('suggestion');

// State
let isCapturing = false;
let mediaStream = null;
let mediaRecorder = null;
let deepgramSocket = null;
let audioContext = null;
let fullTranscript = '';
let debounceTimer = null;
let deepgramKey = '';
let groqKey = '';

// Load saved keys
chrome.storage.local.get(['deepgramKey', 'groqKey'], (result) => {
  if (result.deepgramKey) {
    deepgramKey = result.deepgramKey;
    deepgramKeyInput.value = '••••••••••••••••';
  }
  if (result.groqKey) {
    groqKey = result.groqKey;
    groqKeyInput.value = 'gsk_••••••••••••';
  }
});

// Save Deepgram key
saveDeepgramBtn.onclick = () => {
  const val = deepgramKeyInput.value.trim();
  if (val.length > 20 && !val.includes('•')) {
    deepgramKey = val;
    chrome.storage.local.set({ deepgramKey: val });
    deepgramKeyInput.value = '••••••••••••••••';
    setStatus('Deepgram key saved!');
  } else if (val.includes('•')) {
    setStatus('Key already saved');
  } else {
    setStatus('Invalid Deepgram key', 'error');
  }
};

// Save Groq key
saveGroqBtn.onclick = () => {
  const val = groqKeyInput.value.trim();
  if (val.startsWith('gsk_') && val.length > 20) {
    groqKey = val;
    chrome.storage.local.set({ groqKey: val });
    groqKeyInput.value = 'gsk_••••••••••••';
    setStatus('Groq key saved!');
  } else if (val.includes('•')) {
    setStatus('Key already saved');
  } else {
    setStatus('Invalid Groq key (should start with gsk_)', 'error');
  }
};

// Reset
resetBtn.onclick = () => {
  fullTranscript = '';
  transcriptEl.textContent = 'Waiting for audio...';
  suggestionEl.textContent = 'AI suggestions will appear here...';
  setStatus('Cleared');
};

// Ask AI manually
askBtn.onclick = () => {
  if (fullTranscript.trim().length > 5) {
    getAISuggestion(fullTranscript.trim());
  } else {
    setStatus('No transcript yet', 'error');
  }
};

// Main capture button
captureBtn.onclick = async () => {
  if (isCapturing) {
    stopCapture();
  } else {
    await startCapture();
  }
};

async function startCapture() {
  if (!deepgramKey) {
    setStatus('Enter Deepgram API key first', 'error');
    return;
  }
  if (!groqKey) {
    setStatus('Enter Groq API key first', 'error');
    return;
  }

  try {
    setStatus('Requesting tab audio...');
    
    // Capture tab audio
    mediaStream = await new Promise((resolve, reject) => {
      chrome.tabCapture.capture({ audio: true, video: false }, (stream) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else if (!stream) {
          reject(new Error('No audio stream - make sure the tab has audio'));
        } else {
          resolve(stream);
        }
      });
    });

    setStatus('Connecting to Deepgram...');

    // Connect to Deepgram WebSocket
    deepgramSocket = new WebSocket(
      'wss://api.deepgram.com/v1/listen?model=nova-2&punctuate=true&interim_results=true&smart_format=true',
      ['token', deepgramKey]
    );

    // Create audio context to play the audio back to the user
    audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(mediaStream);
    source.connect(audioContext.destination); // This plays audio through speakers

    deepgramSocket.onopen = () => {
      setStatus('Capturing tab audio...', 'active');
      isCapturing = true;
      captureBtn.textContent = '⏹ Stop Capture';
      captureBtn.classList.add('capturing');

      // Start recording and sending audio chunks
      mediaRecorder = new MediaRecorder(mediaStream, { mimeType: 'audio/webm' });
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && deepgramSocket.readyState === WebSocket.OPEN) {
          deepgramSocket.send(event.data);
        }
      };

      mediaRecorder.start(250); // Send chunks every 250ms
    };

    deepgramSocket.onmessage = (message) => {
      const data = JSON.parse(message.data);
      
      if (data.channel && data.channel.alternatives && data.channel.alternatives[0]) {
        const transcript = data.channel.alternatives[0].transcript;
        
        if (transcript) {
          if (data.is_final) {
            fullTranscript += transcript + ' ';
            transcriptEl.textContent = fullTranscript;
            
            // Auto-scroll
            transcriptEl.scrollTop = transcriptEl.scrollHeight;
            
            // Check for questions after a pause
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => checkForQuestion(fullTranscript), 1500);
          } else {
            // Show interim results
            transcriptEl.textContent = fullTranscript + transcript;
          }
        }
      }
    };

    deepgramSocket.onerror = (error) => {
      console.error('Deepgram error:', error);
      setStatus('Deepgram connection error', 'error');
      stopCapture();
    };

    deepgramSocket.onclose = (event) => {
      console.log('Deepgram closed:', event.code, event.reason);
      if (isCapturing) {
        setStatus('Connection closed: ' + (event.reason || 'unknown'), 'error');
        stopCapture();
      }
    };

  } catch (error) {
    console.error('Capture error:', error);
    setStatus('Error: ' + error.message, 'error');
    stopCapture();
  }
}

function stopCapture() {
  isCapturing = false;

  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  mediaRecorder = null;

  if (deepgramSocket) {
    deepgramSocket.close();
  }
  deepgramSocket = null;

  if (audioContext) {
    audioContext.close();
  }
  audioContext = null;

  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop());
  }
  mediaStream = null;

  captureBtn.textContent = '🔊 Capture Tab Audio';
  captureBtn.classList.remove('capturing');
  setStatus('Stopped');
}

function setStatus(text, className = '') {
  statusEl.textContent = text;
  statusEl.className = 'status ' + className;
}

function checkForQuestion(text) {
  const lastPart = text.split(/[.!]/).slice(-3).join(' ').trim();
  
  const isQuestion = lastPart.includes('?') || 
    /\b(what|how|why|when|where|who|which|can you|could you|tell me|explain|show me|give me|provide|create|write|make|list|describe)\b/i.test(lastPart);
  
  if (isQuestion && lastPart.length > 10) {
    getAISuggestion(lastPart);
  }
}

async function getAISuggestion(question) {
  suggestionEl.textContent = 'Thinking...';
  suggestionEl.classList.add('loading');

  try {
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + groqKey
      },
      body: JSON.stringify({
        model: 'llama-3.1-8b-instant',
        messages: [
          { 
            role: 'system', 
            content: 'You are helping someone in a meeting or interview. Give brief, helpful answers (2-4 sentences max). Be direct and actionable. If it\'s a code question, provide a concise example.' 
          },
          { 
            role: 'user', 
            content: 'Someone asked: "' + question + '"\n\nBrief helpful answer:' 
          }
        ],
        temperature: 0.7,
        max_tokens: 200
      })
    });

    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.error?.message || 'API error ' + res.status);
    }

    suggestionEl.textContent = data.choices[0]?.message?.content || 'No response';
    suggestionEl.classList.remove('loading');
  } catch (err) {
    suggestionEl.textContent = 'Error: ' + err.message;
    suggestionEl.classList.remove('loading');
  }
}

// Cleanup when popup closes
window.addEventListener('unload', () => {
  stopCapture();
});
