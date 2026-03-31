import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import time
import os
from dotenv import load_dotenv
from enhanced_strategy import EnhancedTradingStrategy

def monitor_strict_conditions():
    """Monitor how close we are to satisfying the original strict conditions"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    strategy = EnhancedTradingStrategy("XAUUSD", "M1")
    
    print("📊 STRICT CONDITIONS MONITOR")
    print("=" * 60)
    print("Monitoring how close we are to original strict conditions")
    print("BUY: RSI>50 + EMA9>EMA21 + Supertrend=1")
    print("SELL: RSI<40 + EMA9<EMA21 + Supertrend=-1")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    closest_to_buy = {"rsi_diff": 999, "time": ""}
    closest_to_sell = {"rsi_diff": 999, "time": ""}
    
    try:
        while True:
            symbol = "XAUUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
            tick = mt5.symbol_info_tick(symbol)
            
            if rates is not None and len(rates) > 0 and tick:
                analysis = strategy.analyze_timeframe("M1")
                
                if analysis:
                    rsi = analysis.get('rsi', 50)
                    ema9 = analysis.get('ema9', 0)
                    ema21 = analysis.get('ema21', 0)
                    st_dir = analysis.get('supertrend_direction', 0)
                    current_price = tick.bid
                    
                    # UTC time
                    utc_time = datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)
                    time_display = utc_time.strftime("%H:%M:%S")
                    
                    # Check individual conditions
                    buy_rsi = rsi > 50
                    buy_ema = ema9 > ema21
                    buy_st = st_dir == 1
                    
                    sell_rsi = rsi < 40
                    sell_ema = ema9 < ema21
                    sell_st = st_dir == -1
                    
                    # Calculate how close we are
                    rsi_to_buy = max(0, 50 - rsi)  # How much RSI needs to rise for BUY
                    rsi_to_sell = max(0, rsi - 40)  # How much RSI needs to fall for SELL
                    
                    print(f"\n[{time_display} UTC] Price: {current_price:.2f}")
                    print(f"RSI: {rsi:.1f} | EMA9: {ema9:.2f} | EMA21: {ema21:.2f} | ST: {st_dir}")
                    
                    # BUY Analysis
                    buy_score = sum([buy_rsi, buy_ema, buy_st])
                    print(f"BUY CONDITIONS ({buy_score}/3): RSI>50={buy_rsi} | EMA9>EMA21={buy_ema} | ST=1={buy_st}")
                    if buy_score == 3:
                        print("🎆 BUY SIGNAL ACTIVE!")
                    elif buy_score == 2:
                        missing = []
                        if not buy_rsi: missing.append(f"RSI needs +{rsi_to_buy:.1f}")
                        if not buy_ema: missing.append("EMA crossover needed")
                        if not buy_st: missing.append("Supertrend turn bullish")
                        print(f"🟡 BUY CLOSE: Missing {', '.join(missing)}")
                    else:
                        print(f"🔴 BUY FAR: {3-buy_score} conditions missing")
                    
                    # SELL Analysis  
                    sell_score = sum([sell_rsi, sell_ema, sell_st])
                    print(f"SELL CONDITIONS ({sell_score}/3): RSI<40={sell_rsi} | EMA9<EMA21={sell_ema} | ST=-1={sell_st}")
                    if sell_score == 3:
                        print("🎆 SELL SIGNAL ACTIVE!")
                    elif sell_score == 2:
                        missing = []
                        if not sell_rsi: missing.append(f"RSI needs -{rsi_to_sell:.1f}")
                        if not sell_ema: missing.append("EMA crossover needed")
                        if not sell_st: missing.append("Supertrend turn bearish")
                        print(f"🟡 SELL CLOSE: Missing {', '.join(missing)}")
                    else:
                        print(f"🔴 SELL FAR: {3-sell_score} conditions missing")
                    
                    # Track closest approaches
                    if buy_score == 2 and rsi_to_buy < closest_to_buy["rsi_diff"]:
                        closest_to_buy = {"rsi_diff": rsi_to_buy, "time": time_display}
                    
                    if sell_score == 2 and rsi_to_sell < closest_to_sell["rsi_diff"]:
                        closest_to_sell = {"rsi_diff": rsi_to_sell, "time": time_display}
                    
                    # Show progress
                    if buy_score >= 2 or sell_score >= 2:
                        print("⚡ GETTING CLOSE TO SIGNAL!")
                    
                    print("-" * 60)
                
            time.sleep(3)  # Check every 3 seconds
            
    except KeyboardInterrupt:
        print(f"\n📈 SESSION SUMMARY")
        print("=" * 40)
        if closest_to_buy["time"]:
            print(f"Closest to BUY: RSI needed {closest_to_buy['rsi_diff']:.1f} more at {closest_to_buy['time']}")
        if closest_to_sell["time"]:
            print(f"Closest to SELL: RSI needed {closest_to_sell['rsi_diff']:.1f} less at {closest_to_sell['time']}")
        print("💡 Wait for market conditions to align with strict requirements")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    monitor_strict_conditions()