# Trading Bot + Dashboard Integration Guide

## Overview

Your dashboard is a **web server** that displays real-time data from your trading bots. The bots send data to the dashboard via HTTP API calls.

```
┌─────────────────────┐
│  Forex Bot (Python) │──┐
└─────────────────────┘  │
                          │  HTTP API Calls
┌─────────────────────┐  │  (trades, alerts, stats)
│ Crypto Bot (Python) │──┼──────────────────────→ Dashboard Web Server
└─────────────────────┘  │  (Flask on port 5000)
                          │
┌─────────────────────┐  │
│    You (Browser)    │──┘  View in real-time
└─────────────────────┘
```

---

## Step 1: Install Dashboard Dependencies

```bash
pip install flask flask-cors
```

---

## Step 2: Project Structure

Your project should look like this:

```
trading-bot/
├── forex_trading_bot.py          # Your Forex bot
├── crypto_trading_bot.py          # Your Crypto bot
├── trading_dashboard.py           # Dashboard server (NEW)
├── templates/
│   └── dashboard.html            # Dashboard UI (NEW)
├── .env                          # Environment variables
└── requirements.txt
```

---

## Step 3: Update Your Trading Bots

### For Forex Bot (`forex_trading_bot.py`)

Add these imports at the top:

```python
import requests
from trading_dashboard import DashboardUpdater
```

Add this method to the `ForexBot` class:

```python
async def report_trade(self, signal: TradeSignal, order_result: Dict):
    """Report trade to dashboard"""
    try:
        trade_data = {
            'id': order_result.get('ticket', str(time.time())),
            'symbol': signal.symbol,
            'type': signal.order_type.value,
            'entry_price': order_result.get('openPrice', 0),
            'volume': order_result.get('volume', 0),
            'stop_loss': order_result.get('stopLoss', 0),
            'take_profit': order_result.get('takeProfit', 0),
            'strategy': signal.strategy.value
        }
        
        requests.post('http://localhost:5000/api/trade/open', json=trade_data)
    except Exception as e:
        logger.error(f"Error reporting trade: {e}")

async def report_alert(self, message: str, alert_type: str = 'info'):
    """Report alert to dashboard"""
    try:
        requests.post('http://localhost:5000/api/alerts', json={
            'message': message,
            'type': alert_type,
            'source': 'forex_bot'
        })
    except Exception as e:
        logger.error(f"Error reporting alert: {e}")

async def update_status(self):
    """Update bot status on dashboard"""
    try:
        account_info = await self.account.get_account_information()
        requests.post('http://localhost:5000/api/update/balance', json={
            'market': 'forex',
            'balance': account_info.get('balance', 0)
        })
        requests.post('http://localhost:5000/api/update/equity', json={
            'market': 'forex',
            'equity': account_info.get('equity', 0)
        })
    except Exception as e:
        logger.error(f"Error updating status: {e}")
```

Modify the `open_trade` method to call `report_trade`:

```python
async def open_trade(self, signal: TradeSignal) -> Optional[Dict]:
    """Open a new trade based on signal"""
    try:
        # ... existing code ...
        result = await self.account.create_market_order(...)
        
        # NEW: Report to dashboard
        await self.report_trade(signal, result)
        
        return result
    except Exception as e:
        logger.error(f"Error opening trade: {e}")
        return None
```

Add to the main loop in `run()`:

```python
async def run(self, interval: int = 300):
    """Main bot loop"""
    self.is_running = True
    logger.info(f"Starting bot loop with {interval}s interval")
    
    # NEW: Report that bot started
    await self.report_alert('Forex bot started', 'info')
    
    try:
        while self.is_running:
            try:
                # NEW: Update status
                await self.update_status()
                
                # ... existing code ...
                
                # Wait before next cycle
                await asyncio.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error in bot loop: {e}")
                await self.report_alert(f"Error: {str(e)}", 'danger')
                await asyncio.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        await self.report_alert('Forex bot stopped', 'warning')
```

---

### For Crypto Bot (`crypto_trading_bot.py`)

Add the same integration:

```python
import requests

# In the CryptoBot class
async def report_trade(self, symbol: str, order_type: str, order: Dict):
    """Report trade to dashboard"""
    try:
        trade_data = {
            'id': order.get('id', str(time.time())),
            'symbol': symbol,
            'type': order_type.upper(),
            'entry_price': order.get('average', 0),
            'volume': order.get('amount', 0),
            'strategy': self.strategy.value
        }
        requests.post('http://localhost:5000/api/trade/open', json=trade_data)
    except Exception as e:
        logger.error(f"Error reporting trade: {e}")

async def report_alert(self, message: str, alert_type: str = 'info'):
    """Report alert to dashboard"""
    try:
        requests.post('http://localhost:5000/api/alerts', json={
            'message': message,
            'type': alert_type,
            'source': 'crypto_bot'
        })
    except Exception as e:
        logger.error(f"Error reporting alert: {e}")

async def update_status(self):
    """Update bot status on dashboard"""
    try:
        balance = await self.get_balance()
        usdt_balance = balance.get('USDT', {}).get('total', 0)
        requests.post('http://localhost:5000/api/update/balance', json={
            'market': 'crypto',
            'balance': usdt_balance
        })
        requests.post('http://localhost:5000/api/update/equity', json={
            'market': 'crypto',
            'equity': usdt_balance
        })
    except Exception as e:
        logger.error(f"Error updating status: {e}")
```

Modify `create_order`:

```python
async def create_order(self, symbol: str, order_type: OrderType, amount: float):
    """Create a market order"""
    try:
        side = 'buy' if order_type == OrderType.BUY else 'sell'
        order = await self.exchange.create_market_order(symbol, side, amount)
        
        # NEW: Report to dashboard
        await self.report_trade(symbol, side, order)
        
        logger.info(f"Order created: {side.upper()} {amount} {symbol}")
        return order
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return None
```

Update the `run()` method:

```python
async def run(self, interval: int = 60):
    """Main bot loop"""
    self.is_running = True
    logger.info(f"Starting bot loop with {interval}s interval")
    
    # NEW: Report that bot started
    await self.report_alert('Crypto bot started', 'info')
    
    try:
        while self.is_running:
            try:
                # NEW: Update status
                await self.update_status()
                
                # ... existing code ...
                
                await asyncio.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error in bot loop: {e}")
                await self.report_alert(f"Error: {str(e)}", 'danger')
                await asyncio.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        await self.report_alert('Crypto bot stopped', 'warning')
```

---

## Step 4: Create requirements.txt

```bash
# requirements.txt
flask==2.3.0
flask-cors==4.0.0
metaapi-cloud-sdk==16.0.0
ccxt==4.0.0
pandas==2.0.0
ta-lib==0.4.28
numpy==1.24.0
requests==2.31.0
aiohttp==3.8.0
python-dotenv==1.0.0
```

Install all:

```bash
pip install -r requirements.txt
```

---

## Step 5: Run Everything

### Terminal 1 - Start Dashboard Server

```bash
python trading_dashboard.py
```

Output:
```
 * Running on http://0.0.0.0:5000
```

### Terminal 2 - Start Forex Bot

```bash
python forex_trading_bot.py
```

### Terminal 3 - Start Crypto Bot

```bash
python crypto_trading_bot.py
```

### Terminal 4 (or Browser) - View Dashboard

Open your browser and go to:

```
http://localhost:5000
```

---

## Step 6: What You'll See

Once everything is running, your dashboard will show:

✅ **Real-time updates every 3 seconds**
- Account balance and equity
- P&L calculations
- Open and closed trades
- Win rate statistics
- Bot connection status

✅ **Trade History**
- All executed trades
- Entry and exit prices
- P&L for each trade

✅ **Alerts**
- Bot start/stop messages
- Trade execution alerts
- Error notifications

✅ **Control Panel**
- Start/stop buttons for each bot
- Widget toggle options
- Live status indicators

---

## Step 7: Advanced - Run Everything with One Command

Create `run_all.py`:

```python
#!/usr/bin/env python3
"""
Run all trading bots and dashboard together
"""

import subprocess
import time
import os
from pathlib import Path

def run_all():
    """Start all services"""
    
    print("🚀 Starting Trading Bot Suite...")
    print("\n" + "="*50)
    
    # Ensure templates directory exists
    Path('templates').mkdir(exist_ok=True)
    
    processes = []
    
    # Start Dashboard
    print("\n[1/3] Starting Dashboard on http://localhost:5000")
    dashboard_proc = subprocess.Popen([
        'python', 'trading_dashboard.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    processes.append(('Dashboard', dashboard_proc))
    time.sleep(2)
    
    # Start Forex Bot
    print("[2/3] Starting Forex Bot...")
    forex_proc = subprocess.Popen([
        'python', 'forex_trading_bot.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    processes.append(('Forex Bot', forex_proc))
    time.sleep(1)
    
    # Start Crypto Bot
    print("[3/3] Starting Crypto Bot...")
    crypto_proc = subprocess.Popen([
        'python', 'crypto_trading_bot.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    processes.append(('Crypto Bot', crypto_proc))
    
    print("\n" + "="*50)
    print("✅ All services started!")
    print("\n📊 Dashboard: http://localhost:5000")
    print("🔌 API: http://localhost:5000/api")
    print("\nPress Ctrl+C to stop all services...\n")
    print("="*50 + "\n")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
            
            # Check if any process died
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"⚠️  {name} stopped unexpectedly!")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all services...")
        for name, proc in processes:
            proc.terminate()
            time.sleep(0.5)
            if proc.poll() is None:
                proc.kill()
            print(f"   ✓ {name} stopped")
        
        print("\n👋 Goodbye!")

if __name__ == '__main__':
    run_all()
```

Run with:

```bash
python run_all.py
```

---

## Step 8: Troubleshooting

### Dashboard not loading?

```bash
# Check if Flask server is running
curl http://localhost:5000

# If not working:
# 1. Make sure port 5000 is available
# 2. Check firewall settings
# 3. Reinstall Flask: pip install --upgrade flask
```

### Bots not sending data to dashboard?

```bash
# Check if dashboard is running:
ps aux | grep trading_dashboard

# Check if bots can reach dashboard:
python -c "import requests; requests.get('http://localhost:5000/api/alerts')"

# Check logs for errors
# Add this to both bots for debugging:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### API calls failing?

Add this to `forex_trading_bot.py` and `crypto_trading_bot.py`:

```python
import time

async def report_trade(self, signal, order_result):
    """Report trade to dashboard with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            trade_data = {...}
            response = requests.post(
                'http://localhost:5000/api/trade/open',
                json=trade_data,
                timeout=5
            )
            if response.status_code == 200:
                logger.info(f"Trade reported successfully")
                return
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

## Step 9: Optional - Deploy Dashboard Online

### Using Ngrok (Free Tunneling)

```bash
pip install pyngrok

# In Python:
from pyngrok import ngrok

public_url = ngrok.connect(5000)
print(f"Dashboard available at: {public_url}")
```

### Using Heroku (Free Tier)

```bash
# Install Heroku CLI
brew install heroku

# Login
heroku login

# Create Procfile
echo "web: python trading_dashboard.py" > Procfile

# Deploy
git push heroku main
```

---

## Summary

Your complete setup now has:

```
┌─────────────────────────────────────────────────┐
│         Trading Bot Dashboard (Port 5000)        │
│  ✓ Real-time monitoring                         │
│  ✓ Trade history                                │
│  ✓ Start/stop controls                          │
│  ✓ Alert notifications                          │
│  ✓ Performance metrics                          │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
    Forex Bot  Crypto Bot  Historical Data
    (Python)   (Python)    (JSON)
```

**All bots now send real-time data to your dashboard!**

---

## What's Next?

1. ✅ Deploy on VPS for 24/7 access
2. ✅ Add email/Telegram alerts to dashboard
3. ✅ Implement backtesting results display
4. ✅ Add performance charts
5. ✅ Create mobile app version
6. ✅ Add database (PostgreSQL) for historical data

Let me know if you need help with any of these!
