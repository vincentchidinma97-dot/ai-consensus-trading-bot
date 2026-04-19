from flask import Flask, render_template_string, jsonify
from datetime import datetime
import os
from dotenv import load_dotenv
from ai_consensus import AIConsensusEngine
import asyncio

load_dotenv(os.path.expanduser('~/.env'))
app = Flask(__name__)
engine = AIConsensusEngine(os.getenv('ANTHROPIC_API_KEY'), os.getenv('GEMINI_API_KEY'))

latest_analysis = {"timestamp": None, "xauusd": None, "gbpjpy": None}

HTML = """<!DOCTYPE html>
<html>
<head>
    <title>AI Consensus Dashboard</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 30px; }
        .pairs-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .pair-card { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        .pair-title { font-size: 1.8em; font-weight: bold; color: #667eea; margin-bottom: 20px; }
        .ai-section { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 15px; border-left: 4px solid #667eea; }
        .analysis-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .consensus-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; padding: 20px; text-align: center; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Consensus Dashboard</h1>
        <div id="content"><p style="color:white;text-align:center;">Waiting for analysis...</p></div>
    </div>
    <script>
        setInterval(async () => {
            const res = await fetch('/api/analysis');
            const data = await res.json();
            if(data.timestamp) document.getElementById('content').innerHTML = '<p style="color:white;">Last update: ' + new Date(data.timestamp).toLocaleString() + '</p>';
        }, 5000);
    </script>
</body>
</html>"""

@app.route('/')
def dashboard():
    return render_template_string(HTML)

@app.route('/api/analysis')
def get_analysis():
    return jsonify(latest_analysis)

if __name__ == '__main__':
    print("\n🚀 Dashboard running at http://localhost:5001")
    print("Press Ctrl+C to stop\n")
    app.run(debug=False, port=5001)
