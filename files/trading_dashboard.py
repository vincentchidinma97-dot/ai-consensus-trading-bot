"""
Trading Bot Dashboard - Flask Web Server
Integrates with Forex and Crypto bots for real-time monitoring
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import asyncio
import json
from datetime import datetime, timedelta
from dataclasses import asdict
import logging
from typing import Dict, List, Optional
import threading

# Import your trading bots
# from forex_trading_bot import ForexBot, StrategyType as FxStrategy
# from crypto_trading_bot import CryptoBot, StrategyType as CryptoStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global state for dashboard
dashboard_state = {
    'forex': {
        'balance': 10000.00,
        'equity': 10000.00,
        'profit_loss': 0.00,
        'profit_loss_percent': 0.00,
        'open_trades': [],
        'closed_trades': [],
        'win_rate': 0.0,
        'total_trades': 0,
        'active_trades': 0,
        'status': 'disconnected',
        'connected_at': None,
        'strategy': 'MA_CROSS',
        'symbols': ['EURUSD', 'GBPUSD', 'USDJPY']
    },
    'crypto': {
        'balance': 1000.00,
        'equity': 1000.00,
        'profit_loss': 0.00,
        'profit_loss_percent': 0.00,
        'open_trades': [],
        'closed_trades': [],
        'win_rate': 0.0,
        'total_trades': 0,
        'active_trades': 0,
        'status': 'disconnected',
        'connected_at': None,
        'strategy': 'MOMENTUM',
        'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
        'exchange': 'binance'
    },
    'widgets': {
        'price_chart': {'visible': True, 'data': []},
        'rsi_indicator': {'visible': True, 'value': 50, 'status': 'neutral'},
        'macd': {'visible': True, 'signal': 'neutral'},
        'news_feed': {'visible': True, 'events': []},
        'positions': {'visible': True, 'list': []},
        'heatmap': {'visible': True, 'currencies': {}}
    },
    'trades_history': [],
    'alerts': []
}


# ============================================================================
# ROUTES - API Endpoints
# ============================================================================

@app.route('/')
def index():
    """Serve the dashboard HTML"""
    return render_template('dashboard.html')


@app.route('/api/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """Get overall dashboard summary"""
    return jsonify({
        'forex': {
            'balance': dashboard_state['forex']['balance'],
            'equity': dashboard_state['forex']['equity'],
            'profit_loss': dashboard_state['forex']['profit_loss'],
            'profit_loss_percent': dashboard_state['forex']['profit_loss_percent'],
            'status': dashboard_state['forex']['status'],
            'active_trades': dashboard_state['forex']['active_trades'],
            'win_rate': dashboard_state['forex']['win_rate']
        },
        'crypto': {
            'balance': dashboard_state['crypto']['balance'],
            'equity': dashboard_state['crypto']['equity'],
            'profit_loss': dashboard_state['crypto']['profit_loss'],
            'profit_loss_percent': dashboard_state['crypto']['profit_loss_percent'],
            'status': dashboard_state['crypto']['status'],
            'active_trades': dashboard_state['crypto']['active_trades'],
            'win_rate': dashboard_state['crypto']['win_rate']
        },
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/forex/status', methods=['GET'])
def get_forex_status():
    """Get Forex bot status"""
    return jsonify(dashboard_state['forex'])


@app.route('/api/crypto/status', methods=['GET'])
def get_crypto_status():
    """Get Crypto bot status"""
    return jsonify(dashboard_state['crypto'])


@app.route('/api/forex/trades', methods=['GET'])
def get_forex_trades():
    """Get Forex trades history"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        'trades': dashboard_state['forex']['closed_trades'][-limit:],
        'total': len(dashboard_state['forex']['closed_trades'])
    })


@app.route('/api/crypto/trades', methods=['GET'])
def get_crypto_trades():
    """Get Crypto trades history"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        'trades': dashboard_state['crypto']['closed_trades'][-limit:],
        'total': len(dashboard_state['crypto']['closed_trades'])
    })


@app.route('/api/forex/positions', methods=['GET'])
def get_forex_positions():
    """Get open Forex positions"""
    return jsonify({
        'positions': dashboard_state['forex']['open_trades'],
        'count': len(dashboard_state['forex']['open_trades'])
    })


@app.route('/api/crypto/positions', methods=['GET'])
def get_crypto_positions():
    """Get open Crypto positions"""
    return jsonify({
        'positions': dashboard_state['crypto']['open_trades'],
        'count': len(dashboard_state['crypto']['open_trades'])
    })


@app.route('/api/widgets', methods=['GET'])
def get_widgets():
    """Get all widgets state"""
    return jsonify(dashboard_state['widgets'])


@app.route('/api/widgets/<widget_type>', methods=['GET'])
def get_widget(widget_type):
    """Get specific widget data"""
    if widget_type in dashboard_state['widgets']:
        return jsonify(dashboard_state['widgets'][widget_type])
    return jsonify({'error': 'Widget not found'}), 404


@app.route('/api/widgets/<widget_type>', methods=['POST'])
def toggle_widget(widget_type):
    """Toggle widget visibility"""
    data = request.get_json()
    if widget_type in dashboard_state['widgets']:
        dashboard_state['widgets'][widget_type]['visible'] = data.get('visible', True)
        return jsonify({'success': True, 'widget': widget_type})
    return jsonify({'error': 'Widget not found'}), 404


@app.route('/api/bot/forex/start', methods=['POST'])
def start_forex_bot():
    """Start Forex bot"""
    dashboard_state['forex']['status'] = 'running'
    dashboard_state['forex']['connected_at'] = datetime.now().isoformat()
    logger.info("Forex bot started from dashboard")
    return jsonify({'success': True, 'status': 'running'})


@app.route('/api/bot/forex/stop', methods=['POST'])
def stop_forex_bot():
    """Stop Forex bot"""
    dashboard_state['forex']['status'] = 'stopped'
    logger.info("Forex bot stopped from dashboard")
    return jsonify({'success': True, 'status': 'stopped'})


@app.route('/api/bot/crypto/start', methods=['POST'])
def start_crypto_bot():
    """Start Crypto bot"""
    dashboard_state['crypto']['status'] = 'running'
    dashboard_state['crypto']['connected_at'] = datetime.now().isoformat()
    logger.info("Crypto bot started from dashboard")
    return jsonify({'success': True, 'status': 'running'})


@app.route('/api/bot/crypto/stop', methods=['POST'])
def stop_crypto_bot():
    """Stop Crypto bot"""
    dashboard_state['crypto']['status'] = 'stopped'
    logger.info("Crypto bot stopped from dashboard")
    return jsonify({'success': True, 'status': 'stopped'})


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts"""
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        'alerts': dashboard_state['alerts'][-limit:],
        'total': len(dashboard_state['alerts'])
    })


@app.route('/api/alerts', methods=['POST'])
def add_alert():
    """Add new alert (from bot)"""
    data = request.get_json()
    alert = {
        'timestamp': datetime.now().isoformat(),
        'type': data.get('type', 'info'),
        'message': data.get('message'),
        'source': data.get('source', 'unknown')
    }
    dashboard_state['alerts'].append(alert)
    return jsonify({'success': True, 'alert': alert})


@app.route('/api/trade/open', methods=['POST'])
def record_open_trade():
    """Record an opened trade"""
    data = request.get_json()
    trade = {
        'id': data.get('id'),
        'timestamp': datetime.now().isoformat(),
        'symbol': data.get('symbol'),
        'type': data.get('type'),  # BUY/SELL
        'entry_price': data.get('entry_price'),
        'volume': data.get('volume'),
        'stop_loss': data.get('stop_loss'),
        'take_profit': data.get('take_profit'),
        'status': 'open',
        'pnl': 0
    }
    
    market = data.get('market', 'unknown')
    if market == 'forex':
        dashboard_state['forex']['open_trades'].append(trade)
        dashboard_state['forex']['active_trades'] = len(dashboard_state['forex']['open_trades'])
    elif market == 'crypto':
        dashboard_state['crypto']['open_trades'].append(trade)
        dashboard_state['crypto']['active_trades'] = len(dashboard_state['crypto']['open_trades'])
    
    logger.info(f"Trade opened: {trade['symbol']} {trade['type']}")
    return jsonify({'success': True, 'trade': trade})


@app.route('/api/trade/close', methods=['POST'])
def record_close_trade():
    """Record a closed trade"""
    data = request.get_json()
    market = data.get('market', 'unknown')
    trade_id = data.get('trade_id')
    exit_price = data.get('exit_price')
    pnl = data.get('pnl')
    
    if market == 'forex':
        trades_list = dashboard_state['forex']['open_trades']
        closed_trades_list = dashboard_state['forex']['closed_trades']
    else:
        trades_list = dashboard_state['crypto']['open_trades']
        closed_trades_list = dashboard_state['crypto']['closed_trades']
    
    # Find and move trade from open to closed
    for i, trade in enumerate(trades_list):
        if trade['id'] == trade_id:
            trade['status'] = 'closed'
            trade['exit_price'] = exit_price
            trade['pnl'] = pnl
            trade['closed_at'] = datetime.now().isoformat()
            closed_trades_list.append(trades_list.pop(i))
            break
    
    # Update stats
    if market == 'forex':
        dashboard_state['forex']['active_trades'] = len(dashboard_state['forex']['open_trades'])
        dashboard_state['forex']['total_trades'] += 1
        dashboard_state['forex']['closed_trades'] = closed_trades_list
        # Calculate win rate
        wins = sum(1 for t in closed_trades_list if t.get('pnl', 0) > 0)
        dashboard_state['forex']['win_rate'] = (wins / len(closed_trades_list) * 100) if closed_trades_list else 0
    else:
        dashboard_state['crypto']['active_trades'] = len(dashboard_state['crypto']['open_trades'])
        dashboard_state['crypto']['total_trades'] += 1
        dashboard_state['crypto']['closed_trades'] = closed_trades_list
        wins = sum(1 for t in closed_trades_list if t.get('pnl', 0) > 0)
        dashboard_state['crypto']['win_rate'] = (wins / len(closed_trades_list) * 100) if closed_trades_list else 0
    
    logger.info(f"Trade closed: PnL {pnl}")
    return jsonify({'success': True})


@app.route('/api/update/balance', methods=['POST'])
def update_balance():
    """Update account balance"""
    data = request.get_json()
    market = data.get('market', 'unknown')
    balance = data.get('balance')
    
    if market == 'forex':
        dashboard_state['forex']['balance'] = balance
    else:
        dashboard_state['crypto']['balance'] = balance
    
    return jsonify({'success': True})


@app.route('/api/update/equity', methods=['POST'])
def update_equity():
    """Update account equity and P&L"""
    data = request.get_json()
    market = data.get('market', 'unknown')
    equity = data.get('equity')
    
    if market == 'forex':
        dashboard_state['forex']['equity'] = equity
        pnl = equity - 10000  # Assuming initial balance of 10000
        dashboard_state['forex']['profit_loss'] = pnl
        dashboard_state['forex']['profit_loss_percent'] = (pnl / 10000) * 100
    else:
        dashboard_state['crypto']['equity'] = equity
        pnl = equity - 1000  # Assuming initial balance of 1000
        dashboard_state['crypto']['profit_loss'] = pnl
        dashboard_state['crypto']['profit_loss_percent'] = (pnl / 1000) * 100
    
    return jsonify({'success': True})


# ============================================================================
# DATA UPDATE FUNCTIONS (Call from your bots)
# ============================================================================

def update_price_chart(symbol: str, prices: List[dict], market: str = 'crypto'):
    """Update price chart data"""
    dashboard_state['widgets']['price_chart']['data'] = {
        'symbol': symbol,
        'market': market,
        'prices': prices,
        'timestamp': datetime.now().isoformat()
    }


def update_rsi_indicator(value: float, status: str):
    """Update RSI indicator"""
    dashboard_state['widgets']['rsi_indicator']['value'] = value
    dashboard_state['widgets']['rsi_indicator']['status'] = status


def update_macd(signal: str):
    """Update MACD indicator"""
    dashboard_state['widgets']['macd']['signal'] = signal


def update_news_feed(events: List[dict]):
    """Update economic news feed"""
    dashboard_state['widgets']['news_feed']['events'] = events


def update_positions(positions: List[dict], market: str):
    """Update positions widget"""
    if market == 'forex':
        dashboard_state['widgets']['positions']['list'] = positions
    else:
        dashboard_state['widgets']['positions']['list'] = positions


def update_heatmap(currencies: Dict):
    """Update currency heatmap"""
    dashboard_state['widgets']['heatmap']['currencies'] = currencies


# ============================================================================
# HELPER FUNCTIONS FOR BOT INTEGRATION
# ============================================================================

class DashboardUpdater:
    """Helper class to update dashboard from bot"""
    
    @staticmethod
    def log_trade(trade_data: dict, market: str):
        """Log trade to dashboard"""
        try:
            response = request.post(
                f'http://localhost:5000/api/trade/open',
                json={**trade_data, 'market': market}
            )
            logger.info(f"Trade logged to dashboard: {response.status_code}")
        except Exception as e:
            logger.error(f"Error logging trade to dashboard: {e}")
    
    @staticmethod
    def log_alert(message: str, alert_type: str = 'info', source: str = 'bot'):
        """Log alert to dashboard"""
        try:
            alert = {
                'message': message,
                'type': alert_type,
                'source': source,
                'timestamp': datetime.now().isoformat()
            }
            dashboard_state['alerts'].append(alert)
            logger.info(f"Alert: {message}")
        except Exception as e:
            logger.error(f"Error logging alert: {e}")
    
    @staticmethod
    def update_bot_status(market: str, status: str):
        """Update bot connection status"""
        if market == 'forex':
            dashboard_state['forex']['status'] = status
        else:
            dashboard_state['crypto']['status'] = status


if __name__ == '__main__':
    logger.info("Starting Trading Dashboard Server...")
    app.run(host='0.0.0.0', port=5000, debug=False)
