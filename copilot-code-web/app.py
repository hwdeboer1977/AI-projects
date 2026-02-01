"""
Copilot Code (Web Version)
Flask server with browser-based video capture
"""

from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import base64
import os
import json

app = Flask(__name__)

# Config
CONFIG_FILE = "config.json"
client = None
conversation_history = []

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', has_api_key=bool(config.get('api_key')))

@app.route('/save_api_key', methods=['POST'])
def save_api_key():
    global client
    data = request.json
    api_key = data.get('api_key', '').strip()
    
    if not api_key.startswith('sk-'):
        return jsonify({'error': 'Invalid API key (should start with sk-)'}), 400
    
    config = load_config()
    config['api_key'] = api_key
    save_config(config)
    
    client = OpenAI(api_key=api_key)
    return jsonify({'success': True})

@app.route('/analyze', methods=['POST'])
def analyze():
    global client, conversation_history
    
    config = load_config()
    api_key = config.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'No API key configured'}), 400
    
    if not client:
        client = OpenAI(api_key=api_key)
    
    data = request.json
    image_data = data.get('image', '')  # base64 image
    prompt = data.get('prompt', 'What do you see on this screen? If there\'s code, explain it. If there\'s a problem or error, help solve it.')
    include_image = data.get('include_image', True)
    
    try:
        messages = [
            {
                "role": "system",
                "content": """You are Copilot Code, an AI assistant helping with coding interviews and programming tasks.

When analyzing screens:
- If you see code, explain what it does and identify any issues
- If you see an error, explain the cause and how to fix it
- If you see a coding problem, help solve it step by step
- Be concise but thorough
- Use code blocks with syntax highlighting when showing code

Always be helpful and direct."""
            }
        ]
        
        # Add conversation history (last 6 messages)
        for msg in conversation_history[-6:]:
            messages.append(msg)
        
        # Add current message
        if include_image and image_data:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}",
                            "detail": "high"
                        }
                    }
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})
        
        # Call API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2000
        )
        
        answer = response.choices[0].message.content
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": prompt})
        conversation_history.append({"role": "assistant", "content": answer})
        
        return jsonify({'response': answer})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear():
    global conversation_history
    conversation_history = []
    return jsonify({'success': True})

@app.route('/check_api_key')
def check_api_key():
    config = load_config()
    return jsonify({'has_key': bool(config.get('api_key'))})

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  Copilot Code (Web Version)")
    print("="*50)
    print("\n  Open in browser: http://localhost:5000")
    print("\n  Press Ctrl+C to stop\n")
    app.run(debug=False, port=5000, threaded=True)
