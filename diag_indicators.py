import MetaTrader5 as mt5
import pandas as pd
import os
from dotenv import load_dotenv
from enhanced_strategy import EnhancedTradingStrategy
from datetime import datetime

def diagnostic_check():
    load_dotenv()
    
    # Connection details
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    # Initialize MT5
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"❌ MT5 Initialization failed: {mt5.last_error()}")
        return

    print("✅ MT5 Connected Successfully")
    
    symbol = "XAUUSD"
    timeframe = "M1"
    strategy = EnhancedTradingStrategy(symbol, timeframe)
    
    # Fetch and calculate indicators
    analysis = strategy.analyze_timeframe(timeframe)
    
    if not analysis:
        print(f"❌ Failed to fetch data for {symbol}")
        mt5.shutdown()
        return

    print(f"\n--- Diagnostic for {symbol} ({timeframe}) ---")
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current Price: {analysis.get('close'):.5f}")
    
    # Check RSI (14, Wilder's)
    rsi = analysis.get('rsi')
    print(f"RSI (14): {rsi:.2f} {'(OK)' if rsi else '(FAIL)'}")
    
    # --- EMA checks commented out (replaced by UT Bot) ---
    # ema9 = analysis.get('ema9')
    # ema21 = analysis.get('ema21')
    # print(f"EMA 9: {ema9:.5f}")
    # print(f"EMA 21: {ema21:.5f}")
    # print(f"EMA Trend: {'BULLISH' if ema9 > ema21 else 'BEARISH'}")
    # ema_angle = analysis.get('ema_angle')
    # print(f"EMA 9 Angle: {ema_angle:.2f}°")
    # st_val = analysis.get('supertrend_value')
    # st_dir = analysis.get('supertrend_direction')
    # st_dir_text = "BULLISH" if st_dir == 1 else "BEARISH"
    # print(f"SuperTrend (10, 0.9): {st_val:.5f} ({st_dir_text})")

    # --- UT Bot diagnostics ---
    trail_stop = analysis.get('trail_stop')
    ut_buy     = analysis.get('ut_buy')
    ut_sell    = analysis.get('ut_sell')
    print(f"UT Trail Stop: {trail_stop:.5f}")
    print(f"UT Buy Signal:  {ut_buy}")
    print(f"UT Sell Signal: {ut_sell}")
    
    # Check Signal Logic
    signal = strategy.check_entry_conditions(analysis)
    print(f"\nFinal Entry Signal: {signal}")
    
    mt5.shutdown()

if __name__ == "__main__":
    diagnostic_check()
