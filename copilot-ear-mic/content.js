// Toggle overlay if exists, otherwise create
if (document.getElementById('copilot-ear-overlay')) {
  const overlay = document.getElementById('copilot-ear-overlay');
  overlay.style.display = overlay.style.display === 'none' ? 'block' : 'none';
} else {
  createOverlay();
}

function createOverlay() {
  const overlay = document.createElement('div');
  overlay.id = 'copilot-ear-overlay';
  overlay.innerHTML = `
    <style>
      #copilot-ear-overlay {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 380px;
        background: #1a1a2e;
        border-radius: 12px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        color: #eee;
        z-index: 2147483647;
      }
      #copilot-ear-overlay * { box-sizing: border-box; }
      .ce-header {
        background: #252542;
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 12px 12px 0 0;
        cursor: move;
      }
      .ce-header h1 { margin: 0; font-size: 16px; }
      .ce-close {
        background: none;
        border: none;
        color: #888;
        font-size: 20px;
        cursor: pointer;
      }
      .ce-close:hover { color: #fff; }
      .ce-body { padding: 16px; }
      .ce-api-row {
        display: flex;
        gap: 8px;
        margin-bottom: 12px;
      }
      .ce-api-input {
        flex: 1;
        padding: 8px 12px;
        border: 1px solid #333;
        border-radius: 6px;
        background: #252542;
        color: #eee;
        font-size: 13px;
      }
      .ce-api-input:focus { outline: none; border-color: #6366f1; }
      .ce-btn {
        padding: 8px 16px;
        background: #6366f1;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
      }
      .ce-btn:hover { background: #5254cc; }
      .ce-btn-clear {
        padding: 8px 10px;
        background: #444;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
      }
      .ce-btn-clear:hover { background: #ef4444; }
      .ce-toggle {
        width: 100%;
        padding: 12px;
        font-size: 15px;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        background: #22c55e;
        color: white;
        margin-bottom: 12px;
      }
      .ce-toggle:hover { background: #1ea34d; }
      .ce-toggle.listening { background: #ef4444; }
      .ce-toggle.listening:hover { background: #dc2626; }
      .ce-reset {
        width: 100%;
        padding: 8px;
        font-size: 13px;
        border: 1px solid #444;
        border-radius: 6px;
        cursor: pointer;
        background: transparent;
        color: #888;
        margin-bottom: 12px;
      }
      .ce-reset:hover { background: #333; color: #fff; }
      .ce-status {
        text-align: center;
        font-size: 12px;
        color: #888;
        margin-bottom: 12px;
      }
      .ce-status.listening { color: #22c55e; }
      .ce-status.error { color: #ef4444; }
      .ce-section { margin-bottom: 12px; }
      .ce-section h2 {
        font-size: 11px;
        text-transform: uppercase;
        color: #888;
        margin: 0 0 6px 0;
      }
      .ce-transcript {
        background: #252542;
        border-radius: 8px;
        padding: 10px;
        min-height: 60px;
        max-height: 100px;
        overflow-y: auto;
        font-size: 13px;
        color: #ccc;
      }
      .ce-suggestion {
        background: #1e3a5f;
        border: 1px solid #2563eb;
        border-radius: 8px;
        padding: 10px;
        min-height: 80px;
        max-height: 150px;
        overflow-y: auto;
        font-size: 13px;
        color: #e0e7ff;
      }
      .ce-suggestion.loading { opacity: 0.7; font-style: italic; }
    </style>
    
    <div class="ce-header">
      <h1>🎧 Copilot Ear</h1>
      <button class="ce-close">×</button>
    </div>
    
    <div class="ce-body">
      <div class="ce-api-row">
        <input type="text" class="ce-api-input" placeholder="Paste Groq API key (gsk_...)">
        <button class="ce-btn-clear">✕</button>
        <button class="ce-btn ce-save">Save</button>
      </div>
      
      <button class="ce-toggle">Start Listening</button>
      <button class="ce-reset">Reset</button>
      <div class="ce-status">Ready</div>
      
      <div class="ce-section">
        <h2>Transcript</h2>
        <div class="ce-transcript">Waiting for speech...</div>
      </div>
      
      <div class="ce-section">
        <h2>Suggestion</h2>
        <div class="ce-suggestion">AI suggestions will appear here...</div>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  initApp();
}

function initApp() {
  const overlay = document.getElementById('copilot-ear-overlay');
  const closeBtn = overlay.querySelector('.ce-close');
  const apiInput = overlay.querySelector('.ce-api-input');
  const saveBtn = overlay.querySelector('.ce-save');
  const clearBtn = overlay.querySelector('.ce-btn-clear');
  const toggleBtn = overlay.querySelector('.ce-toggle');
  const resetBtn = overlay.querySelector('.ce-reset');
  const statusEl = overlay.querySelector('.ce-status');
  const transcriptEl = overlay.querySelector('.ce-transcript');
  const suggestionEl = overlay.querySelector('.ce-suggestion');

  let isListening = false;
  let recognition = null;
  let fullTranscript = '';
  let debounceTimer = null;
  let apiKey = '';

  // Load saved key
  const saved = localStorage.getItem('copilot-ear-key');
  if (saved) {
    apiKey = saved;
    apiInput.value = 'gsk_••••••••••••';
  }

  // Close
  closeBtn.onclick = () => {
    overlay.style.display = 'none';
    if (recognition) recognition.stop();
    isListening = false;
  };

  // Clear key
  clearBtn.onclick = () => {
    localStorage.removeItem('copilot-ear-key');
    apiKey = '';
    apiInput.value = '';
    statusEl.textContent = 'Key cleared';
  };

  // Reset transcript and suggestion
  resetBtn.onclick = () => {
    fullTranscript = '';
    transcriptEl.textContent = 'Waiting for speech...';
    suggestionEl.textContent = 'AI suggestions will appear here...';
    statusEl.textContent = 'Cleared';
  };

  // Save key
  saveBtn.onclick = () => {
    const val = apiInput.value.trim();
    if (val.startsWith('gsk_') && val.length > 20) {
      apiKey = val;
      localStorage.setItem('copilot-ear-key', val);
      apiInput.value = 'gsk_••••••••••••';
      statusEl.textContent = 'Key saved!';
    } else {
      statusEl.textContent = 'Invalid key (should start with gsk_)';
      statusEl.className = 'ce-status error';
    }
  };

  // Speech recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    statusEl.textContent = 'Speech not supported in this browser';
    statusEl.className = 'ce-status error';
    toggleBtn.disabled = true;
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    statusEl.textContent = 'Listening...';
    statusEl.className = 'ce-status listening';
  };

  recognition.onresult = (e) => {
    let interim = '';
    let final = '';
    
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) {
        final += e.results[i][0].transcript + ' ';
      } else {
        interim += e.results[i][0].transcript;
      }
    }

    if (final) {
      fullTranscript += final;
      transcriptEl.textContent = fullTranscript;
      
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => checkQuestion(fullTranscript), 1500);
    }
    
    if (interim) {
      transcriptEl.textContent = fullTranscript + interim;
    }
  };

  recognition.onerror = (e) => {
    console.error('Speech error:', e.error);
    statusEl.textContent = 'Error: ' + e.error;
    statusEl.className = 'ce-status error';
  };

  recognition.onend = () => {
    if (isListening) recognition.start();
  };

  // Toggle
  toggleBtn.onclick = () => {
    if (isListening) {
      isListening = false;
      recognition.stop();
      toggleBtn.textContent = 'Start Listening';
      toggleBtn.classList.remove('listening');
      statusEl.textContent = 'Stopped';
      statusEl.className = 'ce-status';
    } else {
      if (!apiKey) {
        statusEl.textContent = 'Enter API key first';
        statusEl.className = 'ce-status error';
        return;
      }
      isListening = true;
      fullTranscript = '';
      transcriptEl.textContent = 'Listening...';
      suggestionEl.textContent = 'AI suggestions will appear here...';
      toggleBtn.textContent = 'Stop Listening';
      toggleBtn.classList.add('listening');
      recognition.start();
    }
  };

  function checkQuestion(text) {
    const last = text.split(/[.!]/).slice(-3).join(' ').trim();
    const isQ = last.includes('?') || /\b(what|how|why|when|where|who|which|can you|could you|tell me|explain)\b/i.test(last);
    if (isQ && last.length > 20) {
      getAnswer(last);
    }
  }

  async function getAnswer(question) {
    suggestionEl.textContent = 'Thinking...';
    suggestionEl.classList.add('loading');

    try {
      const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + apiKey
        },
        body: JSON.stringify({
          model: 'llama-3.1-8b-instant',
          messages: [
            { role: 'system', content: 'Give brief, helpful answers (2-3 sentences max). Be direct and actionable.' },
            { role: 'user', content: 'Question asked: "' + question + '"\n\nBrief answer:' }
          ],
          temperature: 0.7,
          max_tokens: 150
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
}
