import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import time
import os
from dotenv import load_dotenv
from enhanced_strategy import EnhancedTradingStrategy

def check_current_signals():
    """Quick check of what signals are being generated"""
    
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
    
    print("🔍 CURRENT MARKET SIGNALS")
    print("=" * 50)
    
    try:
        for i in range(5):  # Check 5 times
            symbol = "XAUUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
            tick = mt5.symbol_info_tick(symbol)
            
            if rates is not None and len(rates) > 0 and tick:
                # Get analysis
                analysis = strategy.analyze_timeframe("M1")
                signal = strategy.check_entry_conditions(analysis)
                
                # UTC time
                utc_time = datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)
                time_display = utc_time.strftime("%H:%M:%S")
                
                if analysis:
                    rsi = analysis.get('rsi', 0)
                    ema9 = analysis.get('ema9', 0)
                    ema21 = analysis.get('ema21', 0)
                    st_dir = analysis.get('supertrend_direction', 0)
                    
                    print(f"\n[{time_display} UTC] Price: {tick.bid:.2f}")
                    print(f"RSI: {rsi:.1f} | EMA9: {ema9:.2f} | EMA21: {ema21:.2f} | ST: {st_dir}")
                    
                    # Check BUY conditions
                    buy_rsi = rsi > 50
                    buy_ema = ema9 > ema21
                    buy_st = st_dir == 1
                    buy_signal = buy_rsi and buy_ema and buy_st
                    
                    # Check SELL conditions  
                    sell_rsi = rsi < 40
                    sell_ema = ema9 < ema21
                    sell_st = st_dir == -1
                    sell_signal = sell_rsi and sell_ema and sell_st
                    
                    print(f"BUY: RSI>50={buy_rsi} | EMA9>EMA21={buy_ema} | ST=1={buy_st} → {buy_signal}")
                    print(f"SELL: RSI<40={sell_rsi} | EMA9<EMA21={sell_ema} | ST=-1={sell_st} → {sell_signal}")
                    print(f"FINAL SIGNAL: {signal}")
                    
                    if signal == "NONE":
                        print("❌ NO SIGNAL - Market conditions don't meet strict requirements")
                        if not sell_signal and ema9 < ema21:
                            print("💡 Market is falling but RSI not low enough or Supertrend not bearish")
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        pass
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    check_current_signals()