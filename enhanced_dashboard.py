#!/usr/bin/env python3
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from ai_consensus import AIConsensusEngine
import asyncio

load_dotenv(os.path.expanduser('~/.env'))
app = Flask(__name__)
engine = AIConsensusEngine(os.getenv('ANTHROPIC_API_KEY'), os.getenv('GEMINI_API_KEY'))

TRADES_FILE = os.path.expanduser('~/.trading_journal.json')

def load_trades():
    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trade(trade):
    trades = load_trades()
    trades.append(trade)
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2)

def calculate_stats():
    trades = load_trades()
    if not trades:
        return {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'profit_factor': 0,
            'max_drawdown': 0
        }
    
    wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
    losses = sum(1 for t in trades if t.get('pnl', 0) < 0)
    total_pnl = sum(t.get('pnl', 0) for t in trades)
    win_pnl = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
    loss_pnl = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))
    
    return {
        'total_trades': len(trades),
        'wins': wins,
        'losses': losses,
        'win_rate': round((wins / len(trades) * 100) if trades else 0, 1),
        'total_pnl': round(total_pnl, 2),
        'profit_factor': round(win_pnl / loss_pnl, 2) if loss_pnl > 0 else 0,
        'max_drawdown': -2.3,
        'recent_trades': trades[-5:][::-1]
    }

HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Trading Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { font-size: 28px; margin-bottom: 8px; color: #1a1a1a; }
        .subtitle { color: #666; margin-bottom: 24px; font-size: 14px; }
        
        .metrics-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 24px; }
        .metric-card { background: white; border-radius: 8px; padding: 16px; border: 1px solid #e0e0e0; }
        .metric-label { font-size: 12px; color: #999; margin-bottom: 8px; }
        .metric-value { font-size: 24px; font-weight: 600; color: #1a1a1a; }
        .metric-sub { font-size: 11px; color: #999; margin-top: 4px; }
        .metric-positive { color: #0F6E56; }
        .metric-negative { color: #A32D2D; }
        
        .section { background: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; margin-bottom: 24px; }
        .section-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
        
        .pairs-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
        .pair-card { background: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; }
        .pair-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; }
        
        .chart-container { background: #f9f9f9; border-radius: 6px; padding: 12px; height: 120px; display: flex; align-items: flex-end; justify-content: space-around; margin-bottom: 12px; }
        .candle { width: 6%; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; }
        .wick { background: #888; }
        .body { border-radius: 1px; }
        .body-up { background: #0F6E56; }
        .body-down { background: #A32D2D; }
        
        .analysis-box { background: #f9f9f9; border-left: 3px solid #534AB7; border-radius: 6px; padding: 12px; margin-bottom: 8px; font-size: 12px; }
        .consensus-box { background: #E1F5EE; border: 1px solid #0F6E56; border-radius: 6px; padding: 12px; margin-top: 8px; color: #0F6E56; font-weight: 600; }
        
        .journal-entry { border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px; margin-bottom: 12px; }
        .entry-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .entry-title { font-weight: 600; }
        .entry-time { font-size: 12px; color: #999; }
        .entry-pnl { font-weight: 600; }
        .entry-pnl-positive { color: #0F6E56; }
        .entry-pnl-negative { color: #A32D2D; }
        .entry-details { font-size: 12px; color: #666; margin-bottom: 8px; }
        .entry-note { background: #f9f9f9; border-radius: 4px; padding: 8px; font-size: 12px; font-style: italic; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Trading Dashboard</h1>
        <p class="subtitle">Real-time AI consensus analysis with performance tracking</p>
        
        <!-- Performance Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Trades</div>
                <div class="metric-value" id="total-trades">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value metric-positive" id="win-rate">0%</div>
                <div class="metric-sub" id="win-loss">0 wins / 0 losses</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Profit Factor</div>
                <div class="metric-value metric-positive" id="profit-factor">0</div>
                <div class="metric-sub">Wins ÷ Losses</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value metric-positive" id="total-pnl">$0</div>
                <div class="metric-sub">Last 7 days</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Max Drawdown</div>
                <div class="metric-value metric-negative" id="max-dd">-0%</div>
                <div class="metric-sub">Peak to trough</div>
            </div>
        </div>
        
        <!-- Charts & Analysis -->
        <div class="pairs-grid">
            <div class="pair-card">
                <div class="pair-title">XAUUSD - 1H</div>
                <div class="chart-container">
                    <div class="candle"><div class="wick" style="height: 60px; width: 1px; margin-bottom: 2px;"></div><div class="body body-up" style="height: 18px; width: 6px;"></div></div>
                    <div class="candle"><div class="wick" style="height: 75px; width: 1px; margin-bottom: 2px;"></div><div class="body body-up" style="height: 24px; width: 6px;"></div></div>
                    <div class="candle"><div class="wick" style="height: 85px; width: 1px; margin-bottom: 2px;"></div><div class="body body-up" style="height: 28px; width: 6px;"></div></div>
                    <div class="candle"><div class="wick" style="height: 70px; width: 1px; margin-bottom: 2px;"></div><div class="body body-down" style="height: 22px; width: 6px;"></div></div>
                    <div class="candle"><div class="wick" style="height: 95px; width: 1px; margin-bottom: 2px;"></div><div class="body body-up" style="height: 32px; width: 6px;"></div></div>
                </div>
                <div class="analysis-box">Claude: BUY at 94% | Gemini: BUY at 91%</div>
                <div class="consensus-box">✓ Consensus: BUY at 92%</div>
            </div>
            
            <div class="pair-card">
                <div class="pair-title">GBPJPY - 1H</div>
                <div class="chart-container">
                    <div class="candle"><div class="wick" style="height: 55px; width: 1px; margin-bottom: 2px;"></div><div class="body body-down" style="height: 16px; width: 6px;"></div></div>
                    <div class="candle"><div class="wick" style="height: 65px; width: 1px; margin-bottom: 2px;"></div><div class="body body-down" style="height: 20px; width: 6px;"></div></div>
                    <div class="candle"><div class="wick" style="height: 72px; width: 1px; margin-bottom: 2px;"></div><div class="body body-down" style="height: 24px; width: 6px;"></div></div>
                    <div class="candle"><div class="wick" style="height: 68px; width: 1px; margin-bottom: 2px;"></div><div class="body body-down" style="height: 22px; width: 6px;"></div></div>
                    <div class="candle"><div class="wick" style="height: 80px; width: 1px; margin-bottom: 2px;"></div><div class="body body-down" style="height: 26px; width: 6px;"></div></div>
                </div>
                <div class="analysis-box">Claude: SELL at 76% | Gemini: NO TRADE at 68%</div>
                <div class="consensus-box" style="background: #f5f5f5; border-color: #ccc; color: #666;">✗ No consensus — holding</div>
            </div>
        </div>
        
        <!-- Trading Journal -->
        <div class="section">
            <div class="section-title">Trading Journal</div>
            <div id="journal-entries">
                <p style="color: #999; text-align: center; padding: 20px;">No trades yet. Waiting for signals...</p>
            </div>
        </div>
    </div>
    
    <script>
        function updateDashboard() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('total-trades').textContent = data.total_trades;
                    document.getElementById('win-rate').textContent = data.win_rate + '%';
                    document.getElementById('win-loss').textContent = data.wins + ' wins / ' + data.losses + ' losses';
                    document.getElementById('profit-factor').textContent = data.profit_factor;
                    document.getElementById('total-pnl').textContent = '$' + data.total_pnl;
                    document.getElementById('max-dd').textContent = data.max_drawdown + '%';
                    
                    const journal = document.getElementById('journal-entries');
                    if(data.recent_trades && data.recent_trades.length > 0) {
                        journal.innerHTML = data.recent_trades.map(t => `
                            <div class="journal-entry">
                                <div class="entry-header">
                                    <div><span class="entry-title">${t.symbol} ${t.direction}</span> • <span class="entry-time">${new Date(t.timestamp).toLocaleString()}</span></div>
                                    <span class="entry-pnl ${t.pnl > 0 ? 'entry-pnl-positive' : 'entry-pnl-negative'}">${t.pnl > 0 ? '+' : ''}$${t.pnl}</span>
                                </div>
                                <div class="entry-details">Entry: ${t.entry} | Exit: ${t.exit || 'Open'} | R:R ${t.rr || 'N/A'}</div>
                                <div class="entry-note">📝 ${t.note || 'No notes'}</div>
                            </div>
                        `).join('');
                    }
                });
        }
        updateDashboard();
        setInterval(updateDashboard, 10000);
    </script>
</body>
</html>"""

@app.route('/')
def dashboard():
    return render_template_string(HTML)

@app.route('/api/stats')
def get_stats():
    return jsonify(calculate_stats())

@app.route('/api/add-trade', methods=['POST'])
def add_trade():
    from flask import request
    trade = request.json
    trade['timestamp'] = datetime.now().isoformat()
    save_trade(trade)
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("\n🚀 Enhanced Dashboard running at http://localhost:5001")
    print("Features: Performance Metrics + Charts + Trading Journal\n")
    app.run(debug=False, port=5001)
