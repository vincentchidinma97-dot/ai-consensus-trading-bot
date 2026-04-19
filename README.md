# AI Consensus Trading Bot 🤖

A professional-grade automated trading system that uses dual AI consensus (Claude + Gemini) to generate high-confidence forex trading signals.

## 📊 Project Overview

This bot addresses a critical problem in retail trading: **single AI models can be wrong**. By forcing two independent AI systems to debate and reach consensus, we dramatically increase signal quality and reduce false positives.

**Core Concept:** Only trade when BOTH Claude AND Gemini agree at 90%+ confidence on the same direction.

## ✨ Key Features

- **Dual AI Consensus:** Claude + Gemini collaborate to validate signals
- **Forex-Optimized Analysis:** Technical indicators, support/resistance, session analysis, volatility assessment
- **Real-Time Dashboard:** Live performance metrics, candlestick charts, trading journal
- **Telegram Notifications:** Instant trade alerts on your phone
- **MetaAPI Integration:** Direct connection to MetaTrader 5 accounts
- **Performance Tracking:** Win rate, profit factor, P&L, max drawdown
- **Risk Management:** Enforced 1:2 risk/reward ratio, position sizing, stop loss limits

## 🛠️ Tech Stack

**Backend:**
- Python 3.14
- Flask (web framework)
- MetaAPI SDK
- Anthropic Claude API
- Google Generative AI (Gemini)

**Frontend:**
- HTML/CSS/JavaScript
- Real-time candlestick charts
- Live performance dashboard

## 📦 Installation

### Prerequisites
- Python 3.10+
- MetaAPI account
- API keys: Anthropic, Google Gemini, Telegram

### Step 1: Clone the Repository
```bash
git clone https://github.com/vincentchidinma97-dot/ai-consensus-trading-bot.git
cd ai-consensus-trading-bot
```

### Step 2: Install Dependencies
```bash
pip3 install anthropic google-generativeai requests python-dotenv metaapi-cloud-sdk flask
```

### Step 3: Configure Environment
Create a `.env` file:
METAAPI_TOKEN=your_token
METAAPI_ACCOUNT_ID=your_account_id
ANTHROPIC_API_KEY=your_claude_key
GEMINI_API_KEY=your_gemini_key
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
TRADING_PAIRS=XAUUSD,GBPJPY
TIMEFRAME=1h
MIN_AI_CONFIDENCE=90
## 🚀 Usage

### Run the Trading Bot
```bash
python3 consensus_trader.py
```

### Run the Dashboard
```bash
python3 enhanced_dashboard.py
```
Open: `http://localhost:5001`

## 📈 System Specifications

- **Pairs:** XAUUSD, GBPJPY
- **Timeframe:** 1 hour
- **Risk per trade:** 1%
- **Min Confidence:** 90% (both AIs)
- **Risk/Reward:** 1:2 (enforced)
- **Max positions:** 3
- **Daily loss limit:** 3%

## 📋 How It Works

1. Bot fetches last 50 hourly candles
2. Claude analyzes price action
3. Gemini independently analyzes same data
4. If both agree at 90%+ → Signal generated
5. Telegram alert sent
6. Dashboard updates in real-time

## 📊 Project Timeline

**Day 1:** 14 hours of development
- Trading bot built
- AI analyzer created
- Dashboard developed
- API integration complete

**Day 2:** AI enhancement
- Forex-specific prompts
- Technical indicators
- Final testing

**Week 1:** Live Demo Testing
- Manual trade execution
- Performance tracking
- Dashboard data collection

**Week 2:** Auto-Execution Phase
- Auto trade opening/closing
- Position management
- Results analysis

## 📁 File Structure
ai-consensus-trading-bot/
├── consensus_trader.py        # Main trading bot
├── ai_consensus.py            # Dual AI analyzer
├── enhanced_dashboard.py       # Real-time dashboard
├── requirements.txt           # Dependencies
└── README.md                  # This file
## 🎯 Expected Performance

- **Win rate:** 55-65%
- **Profit factor:** 1.5-2.5
- **Monthly return:** 5-15% (on $5k demo)

## ⚠️ Important Notes

- Demo account only (testing phase)
- Not financial advice
- Always test on demo before live
- Risk management is critical
- Past performance ≠ future results

## 🚀 Next Steps

1. Week 1: Collect 30-50 trades, analyze results
2. Week 2: Implement auto-execution
3. Week 3: Monitor live for 7 days
4. Week 4+: Live trading decision

## 🤝 Contributing

This is a learning project. Feel free to fork and improve!

## 📝 License

MIT License

## 👤 Author

**Vincent Nwabuokei**
- GitHub: [@vincentchidinma97-dot](https://github.com/vincentchidinma97-dot)
- Status: Active Development (Testing Phase)

---

**Last Updated:** April 19, 2026
**Status:** Testing Phase (Demo Account)
