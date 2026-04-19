"""
MetaTrader 5 Forex Trading Bot using MetaAPI
Author: Trading Bot Framework
Description: Fully functional bot with MT5 integration, risk management, and multiple strategies
"""

import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict
import json

# Install required packages:
# pip install metaapi-cloud-sdk pandas ta-lib numpy python-dotenv

try:
    from metaapi_cloud_sdk import MetaApi
    import pandas as pd
    import numpy as np
    from talib import RSI, MACD, BBANDS
except ImportError as e:
    print(f"Error: {e}. Please install required packages.")
    print("pip install metaapi-cloud-sdk pandas ta-lib numpy")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    BUY = 'BUY'
    SELL = 'SELL'


class StrategyType(Enum):
    MA_CROSS = 'ma_cross'
    RSI = 'rsi'
    BOLLINGER = 'bollinger'
    MACD = 'macd'


@dataclass
class TradeSignal:
    """Data class for trade signals"""
    symbol: str
    order_type: OrderType
    confidence: float  # 0-1
    strategy: StrategyType
    timestamp: datetime


@dataclass
class Position:
    """Data class for open positions"""
    ticket: int
    symbol: str
    order_type: OrderType
    volume: float
    entry_price: float
    stop_loss: float
    take_profit: float
    pnl: float
    pnl_percent: float


class RiskManager:
    """Manages position sizing and risk"""
    
    def __init__(self, account_balance: float, max_risk_per_trade: float = 0.02):
        """
        Initialize risk manager
        
        Args:
            account_balance: Current account balance
            max_risk_per_trade: Maximum risk per trade (default 2%)
        """
        self.account_balance = account_balance
        self.max_risk_per_trade = max_risk_per_trade
    
    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """
        Calculate position size based on risk
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Position size in lots
        """
        risk_amount = self.account_balance * self.max_risk_per_trade
        price_difference = abs(entry_price - stop_loss)
        
        if price_difference == 0:
            return 0.1  # Minimum lot size
        
        # For forex: 1 lot = 100,000 units (adjust based on your broker)
        position_size = (risk_amount / (price_difference * 100000)) * 100000
        
        # Cap at reasonable levels
        return max(0.01, min(position_size / 100000, 10.0))
    
    def should_trade(self, open_positions: int, max_concurrent_trades: int = 3) -> bool:
        """Check if we should open new trades"""
        return open_positions < max_concurrent_trades


class StrategyAnalyzer:
    """Technical analysis strategies"""
    
    @staticmethod
    def ma_cross_strategy(prices: np.ndarray, short_window: int = 10, long_window: int = 20) -> Optional[TradeSignal]:
        """
        Moving Average Crossover Strategy
        
        Args:
            prices: Array of closing prices
            short_window: Short MA period
            long_window: Long MA period
            
        Returns:
            TradeSignal if crossover detected, None otherwise
        """
        if len(prices) < long_window:
            return None
        
        short_ma = pd.Series(prices[-long_window:]).rolling(window=short_window).mean().iloc[-1]
        long_ma = pd.Series(prices[-long_window:]).rolling(window=long_window).mean().iloc[-1]
        prev_short_ma = pd.Series(prices[-(long_window+1):-1]).rolling(window=short_window).mean().iloc[-1]
        prev_long_ma = pd.Series(prices[-(long_window+1):-1]).rolling(window=long_window).mean().iloc[-1]
        
        # Bullish crossover
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            return TradeSignal(
                symbol='',
                order_type=OrderType.BUY,
                confidence=0.75,
                strategy=StrategyType.MA_CROSS,
                timestamp=datetime.now()
            )
        
        # Bearish crossover
        if prev_short_ma >= prev_long_ma and short_ma < long_ma:
            return TradeSignal(
                symbol='',
                order_type=OrderType.SELL,
                confidence=0.75,
                strategy=StrategyType.MA_CROSS,
                timestamp=datetime.now()
            )
        
        return None
    
    @staticmethod
    def rsi_strategy(prices: np.ndarray, period: int = 14, oversold: int = 30, overbought: int = 70) -> Optional[TradeSignal]:
        """
        RSI (Relative Strength Index) Strategy
        
        Args:
            prices: Array of closing prices
            period: RSI period
            oversold: Oversold threshold
            overbought: Overbought threshold
            
        Returns:
            TradeSignal if signal detected, None otherwise
        """
        if len(prices) < period:
            return None
        
        rsi = RSI(prices, timeperiod=period)
        current_rsi = rsi[-1]
        
        # Oversold - potential buy
        if current_rsi < oversold:
            return TradeSignal(
                symbol='',
                order_type=OrderType.BUY,
                confidence=0.65,
                strategy=StrategyType.RSI,
                timestamp=datetime.now()
            )
        
        # Overbought - potential sell
        if current_rsi > overbought:
            return TradeSignal(
                symbol='',
                order_type=OrderType.SELL,
                confidence=0.65,
                strategy=StrategyType.RSI,
                timestamp=datetime.now()
            )
        
        return None
    
    @staticmethod
    def bollinger_bands_strategy(prices: np.ndarray, period: int = 20) -> Optional[TradeSignal]:
        """
        Bollinger Bands Strategy
        
        Args:
            prices: Array of closing prices
            period: BB period
            
        Returns:
            TradeSignal if signal detected, None otherwise
        """
        if len(prices) < period:
            return None
        
        upper, middle, lower = BBANDS(prices, timeperiod=period)
        
        current_price = prices[-1]
        current_lower = lower[-1]
        current_upper = upper[-1]
        
        # Price near lower band - potential buy
        if current_price <= current_lower:
            return TradeSignal(
                symbol='',
                order_type=OrderType.BUY,
                confidence=0.70,
                strategy=StrategyType.BOLLINGER,
                timestamp=datetime.now()
            )
        
        # Price near upper band - potential sell
        if current_price >= current_upper:
            return TradeSignal(
                symbol='',
                order_type=OrderType.SELL,
                confidence=0.70,
                strategy=StrategyType.BOLLINGER,
                timestamp=datetime.now()
            )
        
        return None
    
    @staticmethod
    def macd_strategy(prices: np.ndarray) -> Optional[TradeSignal]:
        """
        MACD (Moving Average Convergence Divergence) Strategy
        
        Args:
            prices: Array of closing prices
            
        Returns:
            TradeSignal if signal detected, None otherwise
        """
        if len(prices) < 26:
            return None
        
        macd_line, signal_line, histogram = MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
        
        # MACD crosses above signal line - buy
        if histogram[-2] < 0 and histogram[-1] > 0:
            return TradeSignal(
                symbol='',
                order_type=OrderType.BUY,
                confidence=0.75,
                strategy=StrategyType.MACD,
                timestamp=datetime.now()
            )
        
        # MACD crosses below signal line - sell
        if histogram[-2] > 0 and histogram[-1] < 0:
            return TradeSignal(
                symbol='',
                order_type=OrderType.SELL,
                confidence=0.75,
                strategy=StrategyType.MACD,
                timestamp=datetime.now()
            )
        
        return None


class ForexBot:
    """Main Forex Trading Bot"""
    
    def __init__(self, token: str, account_id: str, symbols: List[str] = None, strategy: StrategyType = StrategyType.MA_CROSS):
        """
        Initialize Forex Bot
        
        Args:
            token: MetaAPI token
            account_id: MetaAPI account ID
            symbols: List of symbols to trade (e.g., ['EURUSD', 'GBPUSD'])
            strategy: Trading strategy to use
        """
        self.token = token
        self.account_id = account_id
        self.symbols = symbols or ['EURUSD', 'GBPUSD', 'USDJPY']
        self.strategy = strategy
        self.api = None
        self.account = None
        self.risk_manager = None
        self.analyzer = StrategyAnalyzer()
        self.is_running = False
        
        logger.info(f"Forex Bot initialized with strategy: {strategy.value}")
    
    async def connect(self):
        """Connect to MetaAPI"""
        try:
            self.api = MetaApi(self.token)
            self.account = await self.api.metatrader_account_api.get_account(self.account_id)
            # Connection handled automatically
            
            # Wait for connection
            await asyncio.sleep(5)
            
            # Get account information
            account_info = await self.account.get_account_information()
            balance = account_info.get('balance', 0)
            
            self.risk_manager = RiskManager(balance)
            logger.info(f"Connected to account {self.account_id} with balance: ${balance:,.2f}")
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    async def get_market_data(self, symbol: str, timeframe: str = 'H1', bars: int = 100) -> Optional[pd.DataFrame]:
        """
        Get market data for analysis
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (e.g., 'H1', 'M15')
            bars: Number of bars to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            candles = await self.account.get_historical_candles(symbol, timeframe, bars)
            
            if not candles:
                return None
            
            df = pd.DataFrame(candles)
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    async def analyze_signal(self, symbol: str) -> Optional[TradeSignal]:
        """
        Analyze market and generate signal
        
        Args:
            symbol: Trading symbol
            
        Returns:
            TradeSignal if signal detected, None otherwise
        """
        df = await self.get_market_data(symbol)
        
        if df is None or len(df) < 30:
            return None
        
        prices = df['close'].values
        
        # Run selected strategy
        if self.strategy == StrategyType.MA_CROSS:
            signal = self.analyzer.ma_cross_strategy(prices)
        elif self.strategy == StrategyType.RSI:
            signal = self.analyzer.rsi_strategy(prices)
        elif self.strategy == StrategyType.BOLLINGER:
            signal = self.analyzer.bollinger_bands_strategy(prices)
        elif self.strategy == StrategyType.MACD:
            signal = self.analyzer.macd_strategy(prices)
        else:
            signal = None
        
        if signal:
            signal.symbol = symbol
            logger.info(f"Signal detected for {symbol}: {signal.order_type.value} (Confidence: {signal.confidence:.0%})")
        
        return signal
    
    async def open_trade(self, signal: TradeSignal) -> Optional[Dict]:
        """
        Open a new trade based on signal
        
        Args:
            signal: Trade signal
            
        Returns:
            Trade result or None
        """
        try:
            df = await self.get_market_data(signal.symbol)
            if df is None:
                return None
            
            current_price = df['close'].iloc[-1]
            atr = self._calculate_atr(df['high'].values, df['low'].values, df['close'].values)
            
            # Calculate stop loss and take profit
            if signal.order_type == OrderType.BUY:
                stop_loss = current_price - (atr * 2)
                take_profit = current_price + (atr * 3)
            else:
                stop_loss = current_price + (atr * 2)
                take_profit = current_price - (atr * 3)
            
            # Calculate position size
            volume = self.risk_manager.calculate_position_size(current_price, stop_loss)
            
            # Place order
            result = await self.account.create_market_order(
                symbol=signal.symbol,
                operation=signal.order_type.value,
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            logger.info(f"Trade opened: {signal.order_type.value} {volume} {signal.symbol} @ {current_price:.5f}")
            logger.info(f"SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error opening trade: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        try:
            positions = await self.account.get_positions()
            
            position_objects = []
            for pos in positions:
                position_objects.append(Position(
                    ticket=pos['ticket'],
                    symbol=pos['symbol'],
                    order_type=OrderType.BUY if pos['type'] == 'BUY' else OrderType.SELL,
                    volume=pos['volume'],
                    entry_price=pos['openPrice'],
                    stop_loss=pos['stopLoss'],
                    take_profit=pos['takeProfit'],
                    pnl=pos['profit'],
                    pnl_percent=(pos['profit'] / (pos['openPrice'] * pos['volume'])) * 100 if pos['openPrice'] != 0 else 0
                ))
            
            return position_objects
        
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []
    
    async def close_position(self, ticket: int) -> bool:
        """Close a position by ticket"""
        try:
            await self.account.close_position_by_ticket(ticket)
            logger.info(f"Position {ticket} closed")
            return True
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    @staticmethod
    def _calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = np.mean(tr[-period:])
        return atr
    
    async def run(self, interval: int = 300):
        """
        Main bot loop
        
        Args:
            interval: Seconds between analysis cycles
        """
        self.is_running = True
        logger.info(f"Starting bot loop with {interval}s interval")
        
        try:
            while self.is_running:
                try:
                    # Get current positions
                    positions = await self.get_positions()
                    logger.info(f"Current positions: {len(positions)}")
                    
                    # Analyze each symbol
                    for symbol in self.symbols:
                        signal = await self.analyze_signal(symbol)
                        
                        if signal and signal.confidence >= 0.60:
                            # Check if we should trade
                            if self.risk_manager.should_trade(len(positions)):
                                await self.open_trade(signal)
                    
                    # Wait before next cycle
                    await asyncio.sleep(interval)
                
                except Exception as e:
                    logger.error(f"Error in bot loop: {e}")
                    await asyncio.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        
        finally:
            await self.disconnect()
    
    async def disconnect(self):
        """Disconnect from MetaAPI"""
        try:
            if self.account:
                await self.account.close()
            logger.info("Disconnected from MetaAPI")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")


async def main():
    """Main entry point"""
    
    # Configuration
    METAAPI_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJkOTg0ZTRkZmRlZTRiZWNjZTU0OGRjN2E4ZjNmYzk1YSIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVzdC1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcnBjLWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6d3M6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJtZXRhc3RhdHMtYXBpIiwibWV0aG9kcyI6WyJtZXRhc3RhdHMtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6InJpc2stbWFuYWdlbWVudC1hcGkiLCJtZXRob2RzIjpbInJpc2stbWFuYWdlbWVudC1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoiY29weWZhY3RvcnktYXBpIiwibWV0aG9kcyI6WyJjb3B5ZmFjdG9yeS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibXQtbWFuYWdlci1hcGkiLCJtZXRob2RzIjpbIm10LW1hbmFnZXItYXBpOnJlc3Q6ZGVhbGluZzoqOioiLCJtdC1tYW5hZ2VyLWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJiaWxsaW5nLWFwaSIsIm1ldGhvZHMiOlsiYmlsbGluZy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiZDk4NGU0ZGZkZWU0YmVjY2U1NDhkYzdhOGYzZmM5NWEiLCJpYXQiOjE3NzY1NjkzODAsImV4cCI6MTc4NDM0NTM4MH0.NUzeQZitYGfGGjif5AEQna4yDVCZLP2BJbN75YWwnEjA-MDYHdRyEbWt9tbkTaXpha9S43P-i93QlMTEnu-vxRWldUj9KfvNol0bQd5BFZ64MS7R0L4IBILAiRmQJgjS_72ufdebzrUDjKWZKf-RjOLhrKagcIE75hycvlbI9CnNFXgBH5q_26K3AetH03kVOwq2sJYnum8E0cyBiEcvk28RTUkBJTtoZ3CSWg7tQFbVTMwGC-ycJEd6Q2cKxif7gJTu-5dQLdnGOjQ_fsVXsBsryizM1zXs09dApK3gBwAppDY4LVvpDDcIF902k6-8jZkru9mW_2VkFmMKGkvr0liHTT5RVf7hab7cUGMIDGinKZJTO21BDendDnjyD5xugNWpj36e7IyzlrelrHuF4luDjrROdSWip1ypDFmeFse58U_hqnyKzdU4BCvCw__1bt48_mZTAqNSB9D0vm4EQsUE-dOBjz6CCbZ0Di1K2nW3zHF_012IGqZaZh2QBEQZb6MhwpYMpcHB9Fo_frSD1JYuBmOLGPhvhj1gxKGlZjbHNQPBrVoa957sYkDIz35l84BqsOtcnr_tFVj4jXG7syiWhZTQk-rsovrt1LpcM7Fi3Xt0sRosWmSLJcm-rw9smc8a_XrwBQ0yT_e_3u5fzUZampBDB_Kiv4jTJhYvtbA"
    ACCOUNT_ID = "7084f319-3aae-4c6f-9a6f-1583529803ab"
    SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY']
    STRATEGY = StrategyType.MA_CROSS
    
    # Create and run bot
    bot = ForexBot(
        token=METAAPI_TOKEN,
        account_id=ACCOUNT_ID,
        symbols=SYMBOLS,
        strategy=STRATEGY
    )
    
    try:
        await bot.connect()
        await bot.run(interval=300)  # Run every 5 minutes
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    # Run the bot
    asyncio.run(main())
