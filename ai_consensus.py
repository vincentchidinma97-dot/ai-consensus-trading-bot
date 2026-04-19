#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
import anthropic
import google.generativeai as genai
import re

class AIConsensusEngine:
    def __init__(self, claude_key: str, gemini_key: str):
        self.claude_client = anthropic.Anthropic(api_key=claude_key)
        genai.configure(api_key=gemini_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
    
    async def analyze_with_claude(self, market_data: dict) -> dict:
        prompt = f"""
You are a professional forex trader with 20+ years experience. Analyze this FOREX pair with STRICT technical analysis.

MARKET DATA:
{json.dumps(market_data, indent=2)}

ANALYZE LIKE A PRO:
1. Technical Indicators:
   - RSI(14): Overbought >70, Oversold <30, Neutral 40-60
   - MACD: Trend confirmation, signal crossovers
   - Bollinger Bands: Entry/exit zones, volatility assessment
   - Moving Averages: 20/50/200 crossovers, trend direction

2. Support & Resistance:
   - Key levels in data
   - How strong is price respecting them?
   - Are we bouncing or breaking through?

3. Price Action:
   - Candlestick patterns (pin bars, engulfing, dojis)
   - Trend strength (strong uptrend = more reliable)
   - Entry confirmation needed

4. Risk/Reward:
   - ONLY trade if Risk:Reward >= 1:2
   - Example: Risk $100 to make $200+

5. Volatility & Sessions:
   - Is volatility normal or extreme?
   - What trading session (London/NY overlap is best)

6. Final Signal Rules:
   - Confidence >= 90% only if ALL above confirm
   - Confidence 70-89% if 2-3 factors agree
   - Confidence <70% or NO_TRADE if mixed signals

RESPOND ONLY IN JSON (NO MARKDOWN):
{{
    "direction": "BUY|SELL|NO_TRADE",
    "confidence": 0-100,
    "entry_price": X.XXX,
    "stop_loss": X.XXX,
    "take_profit": X.XXX,
    "reasoning": "Technical analysis summary: RSI says..., MACD says..., Price action shows..., R:R is 1:X"
}}
"""
        try:
            message = self.claude_client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = {"direction": "NO_TRADE", "confidence": 0, "reasoning": "Parse error"}
            
            analysis["ai"] = "Claude"
            return analysis
        except Exception as e:
            print(f"❌ Claude error: {e}")
            return {"direction": "NO_TRADE", "confidence": 0, "ai": "Claude", "error": str(e)}
    
    async def analyze_with_gemini(self, market_data: dict) -> dict:
        prompt = f"""
You are a professional forex trader with 20+ years experience. Analyze this FOREX pair with STRICT technical analysis.

MARKET DATA:
{json.dumps(market_data, indent=2)}

ANALYZE LIKE A PRO:
1. Technical Indicators:
   - RSI(14): Overbought >70, Oversold <30, Neutral 40-60
   - MACD: Trend confirmation, signal crossovers
   - Bollinger Bands: Entry/exit zones, volatility assessment
   - Moving Averages: 20/50/200 crossovers, trend direction

2. Support & Resistance:
   - Key levels in data
   - How strong is price respecting them?
   - Are we bouncing or breaking through?

3. Price Action:
   - Candlestick patterns (pin bars, engulfing, dojis)
   - Trend strength (strong uptrend = more reliable)
   - Entry confirmation needed

4. Risk/Reward:
   - ONLY trade if Risk:Reward >= 1:2
   - Example: Risk $100 to make $200+

5. Volatility & Sessions:
   - Is volatility normal or extreme?
   - What trading session (London/NY overlap is best)

6. Final Signal Rules:
   - Confidence >= 90% only if ALL above confirm
   - Confidence 70-89% if 2-3 factors agree
   - Confidence <70% or NO_TRADE if mixed signals

RESPOND ONLY IN JSON (NO MARKDOWN):
{{
    "direction": "BUY|SELL|NO_TRADE",
    "confidence": 0-100,
    "entry_price": X.XXX,
    "stop_loss": X.XXX,
    "take_profit": X.XXX,
    "reasoning": "Technical analysis summary: RSI says..., MACD says..., Price action shows..., R:R is 1:X"
}}
"""
        try:
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text
            
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = {"direction": "NO_TRADE", "confidence": 0, "reasoning": "Parse error"}
            
            analysis["ai"] = "Gemini"
            return analysis
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return {"direction": "NO_TRADE", "confidence": 0, "ai": "Gemini", "error": str(e)}
    
    async def get_consensus(self, market_data: dict, min_confidence: int = 90) -> dict:
        print(f"\n🧠 Running AI Consensus Analysis (FOREX-OPTIMIZED)...")
        print(f"⏱️  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        claude_task = self.analyze_with_claude(market_data)
        gemini_task = self.analyze_with_gemini(market_data)
        
        claude_analysis, gemini_analysis = await asyncio.gather(claude_task, gemini_task)
        
        print(f"\n📊 Claude Analysis:")
        print(f"   Direction: {claude_analysis.get('direction', 'ERROR')}")
        print(f"   Confidence: {claude_analysis.get('confidence', 0)}%")
        print(f"   Reasoning: {claude_analysis.get('reasoning', 'N/A')}")
        
        print(f"\n📊 Gemini Analysis:")
        print(f"   Direction: {gemini_analysis.get('direction', 'ERROR')}")
        print(f"   Confidence: {gemini_analysis.get('confidence', 0)}%")
        print(f"   Reasoning: {gemini_analysis.get('reasoning', 'N/A')}")
        
        consensus = {
            "timestamp": datetime.now().isoformat(),
            "claude": claude_analysis,
            "gemini": gemini_analysis,
            "signal": "NO_TRADE",
            "confidence": 0,
            "agree": False
        }
        
        claude_dir = claude_analysis.get('direction', 'NO_TRADE')
        gemini_dir = gemini_analysis.get('direction', 'NO_TRADE')
        claude_conf = claude_analysis.get('confidence', 0)
        gemini_conf = gemini_analysis.get('confidence', 0)
        
        if claude_dir == gemini_dir and claude_dir != "NO_TRADE":
            if claude_conf >= min_confidence and gemini_conf >= min_confidence:
                consensus["agree"] = True
                consensus["signal"] = claude_dir
                consensus["confidence"] = min(claude_conf, gemini_conf)
                
                consensus["entry_price"] = (claude_analysis.get('entry_price', 0) + gemini_analysis.get('entry_price', 0)) / 2
                consensus["stop_loss"] = (claude_analysis.get('stop_loss', 0) + gemini_analysis.get('stop_loss', 0)) / 2
                consensus["take_profit"] = (claude_analysis.get('take_profit', 0) + gemini_analysis.get('take_profit', 0)) / 2
                
                print(f"\n✅ CONSENSUS REACHED!")
                print(f"   Signal: {consensus['signal']}")
                print(f"   Confidence: {consensus['confidence']}%")
                print(f"   Entry: {consensus['entry_price']:.5f}")
                print(f"   SL: {consensus['stop_loss']:.5f}")
                print(f"   TP: {consensus['take_profit']:.5f}")
            else:
                print(f"\n⚠️  Same direction but confidence too low (Claude: {claude_conf}%, Gemini: {gemini_conf}%)")
        else:
            print(f"\n❌ AIs DISAGREE - No trade signal")
            print(f"   Claude: {claude_dir} ({claude_conf}%)")
            print(f"   Gemini: {gemini_dir} ({gemini_conf}%)")
        
        return consensus
