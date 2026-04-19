#!/usr/bin/env python3
import asyncio
import logging
import os
from dotenv import load_dotenv
from metaapi_cloud_sdk import MetaApi
from ai_consensus import AIConsensusEngine
import requests

load_dotenv(os.path.expanduser('~/.env'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token, chat_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message):
        if not self.chat_id:
            return
        try:
            url = f"{self.base_url}/sendMessage"
            requests.post(url, data={"chat_id": self.chat_id, "text": message})
        except:
            pass
    
    def get_updates(self):
        try:
            url = f"{self.base_url}/getUpdates"
            data = requests.get(url).json()
            if data.get('result'):
                return str(data['result'][-1]['message']['chat']['id'])
        except:
            pass
        return None

class ConsensusBot:
    def __init__(self):
        self.metaapi_token = os.getenv('METAAPI_TOKEN')
        self.account_id = os.getenv('METAAPI_ACCOUNT_ID')
        self.claude_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.pairs = os.getenv('TRADING_PAIRS', 'XAUUSD,GBPJPY').split(',')
        self.ai_engine = AIConsensusEngine(self.claude_key, self.gemini_key)
        self.telegram = TelegramNotifier(self.telegram_token, os.getenv('TELEGRAM_CHAT_ID'))
        self.account = None
    
    async def initialize(self):
        logger.info("🚀 Starting Consensus Bot...")
        try:
            api = MetaApi(self.metaapi_token)
            self.account = await api.metatrader_account_api.get_account(self.account_id)
            logger.info(f"✅ Account: {self.account_id}")
            
            if self.account.state == 'DEPLOYED':
                await asyncio.sleep(2)
                if True:
                    logger.info("✅ Connected to MetaTrader")
                    try:
                        info = await self.account.get_account_information()
                        logger.info(f"💰 Balance: ${info['balance']:.2f}")
                        chat_id = self.telegram.get_updates()
                        if chat_id:
                            self.telegram.chat_id = chat_id
                            self.telegram.send_message("🤖 Bot Started!")
                    except:
                        pass
                    return True
            return False
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
    
    async def get_market_data(self, symbol):
        try:
            candles = await self.account.get_candles(symbol=symbol, timeframe='1h', limit=50)
            if candles:
                latest = candles[-1]
                return {
                    "symbol": symbol,
                    "timeframe": "1H",
                    "current_price": latest['close'],
                    "open": latest['open'],
                    "high": latest['high'],
                    "low": latest['low'],
                    "close": latest['close'],
                    "volume": latest.get('tickVolume', 0),
                    "trend": "uptrend" if latest['close'] > latest['open'] else "downtrend",
                    "support_level": min([c['low'] for c in candles[-20:]]),
                    "resistance_level": max([c['high'] for c in candles[-20:]])
                }
        except:
            pass
        return None
    
    async def run(self):
        if not await self.initialize():
            logger.error("Failed to initialize")
            return
        
        logger.info("✅ Bot ready!")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                for symbol in self.pairs:
                    data = await self.get_market_data(symbol)
                    if data:
                        consensus = await self.ai_engine.get_consensus(data, min_confidence=90)
                        if consensus['agree']:
                            msg = f"📊 {symbol}\n📈 {consensus['signal']}\n💰 Confidence: {consensus['confidence']}%"
                            self.telegram.send_message(msg)
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Bot stopped")
            self.telegram.send_message("🛑 Bot stopped")

async def main():
    bot = ConsensusBot()
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())
