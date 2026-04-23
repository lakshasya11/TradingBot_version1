"""
Test the new conflicted candle entry conditions
"""
import MetaTrader5 as mt5
import pandas as pd
from indicators import TechnicalIndicators
import os
from dotenv import load_dotenv

def test_conflicted_candle_logic():
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    symbol = "XAUUSD"
    
    # Fetch current data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
    if rates is None:
        print("Failed to get rates")
        return
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Get current and previous candle data
    current_close = df['close'].iloc[-1]
    current_open = df['open'].iloc[-1]
    current_high = df['high'].iloc[-1]
    current_low = df['low'].iloc[-1]
    
    prev_close = df['close'].iloc[-2]
    prev_open = df['open'].iloc[-2]
    
    # Calculate indicators
    close = df['close']
    rsi = TechnicalIndicators.calculate_rsi(close, 14)
    ema7 = TechnicalIndicators.calculate_ema7(close)
    ema7_angle = TechnicalIndicators.calculate_ema7_angle(ema7, symbol)
    
    # Current candle analysis
    current_candle_color = 'GREEN' if current_close > current_open else 'RED'
    prev_candle_color = 'GREEN' if prev_close > prev_open else 'RED'
    
    print("=== CONFLICTED CANDLE LOGIC TEST ===")
    print(f"Price: {current_close:.2f}")
    print(f"EMA7: {ema7.iloc[-1]:.2f}")
    print(f"EMA7 Angle: {ema7_angle:.2f}°")
    print(f"RSI: {rsi.iloc[-1]:.1f}")
    print(f"Current Candle: {current_candle_color} (O:{current_open:.2f}, H:{current_high:.2f}, L:{current_low:.2f}, C:{current_close:.2f})")
    print(f"Previous Candle: {prev_candle_color}")
    
    # Calculate wick sizes
    upper_wick = current_high - max(current_open, current_close)
    lower_wick = min(current_open, current_close) - current_low
    body_size = abs(current_close - current_open)
    
    print(f"\nCandle Analysis:")
    print(f"Upper Wick: {upper_wick:.3f}")
    print(f"Lower Wick: {lower_wick:.3f}")
    print(f"Body Size: {body_size:.3f}")
    
    print(f"\n=== BUY ENTRY CONDITIONS CHECK ===")
    
    # Basic conditions
    ema7_buy = current_close > ema7.iloc[-1]
    rsi_ok = rsi.iloc[-1] > 30
    angle_ok = ema7_angle > 77.0
    prev_red = prev_candle_color == 'RED'
    
    print(f"1. Price > EMA7: {ema7_buy} ({current_close:.2f} > {ema7.iloc[-1]:.2f})")
    print(f"2. RSI > 30: {rsi_ok} ({rsi.iloc[-1]:.1f} > 30)")
    print(f"3. EMA7 Angle > +77°: {angle_ok} ({ema7_angle:.2f}° > 77°)")
    print(f"4. Previous RED: {prev_red} ({prev_candle_color})")
    
    # Conflicted candle analysis for BUY
    has_bullish_breakout = current_close > current_open
    has_bearish_element = upper_wick > lower_wick  # Upper wick > lower wick (rejection)
    conflicted_candle_buy = has_bullish_breakout and has_bearish_element
    
    print(f"5a. Bullish Close: {has_bullish_breakout} ({current_close:.2f} > {current_open:.2f})")
    print(f"5b. Bearish Rejection: {has_bearish_element} (Upper wick {upper_wick:.3f} > Lower wick {lower_wick:.3f})")
    print(f"5. Conflicted Candle (BUY): {conflicted_candle_buy}")
    
    # BUY Final result
    buy_signal = ema7_buy and rsi_ok and angle_ok and prev_red and conflicted_candle_buy
    print(f"\nBUY SIGNAL: {buy_signal}")
    
    print(f"\n=== SELL ENTRY CONDITIONS CHECK ===")
    
    # Basic conditions
    ema7_sell = current_close < ema7.iloc[-1]
    rsi_sell_ok = rsi.iloc[-1] < 70
    angle_sell_ok = ema7_angle < -77.0
    prev_green = prev_candle_color == 'GREEN'
    
    print(f"1. Price < EMA7: {ema7_sell} ({current_close:.2f} < {ema7.iloc[-1]:.2f})")
    print(f"2. RSI < 70: {rsi_sell_ok} ({rsi.iloc[-1]:.1f} < 70)")
    print(f"3. EMA7 Angle < -77°: {angle_sell_ok} ({ema7_angle:.2f}° < -77°)")
    print(f"4. Previous GREEN: {prev_green} ({prev_candle_color})")
    
    # Conflicted candle analysis for SELL
    has_bearish_breakdown = current_close < current_open
    has_bullish_element = lower_wick > upper_wick  # Lower wick > upper wick (support)
    conflicted_candle_sell = has_bearish_breakdown and has_bullish_element
    
    print(f"5a. Bearish Close: {has_bearish_breakdown} ({current_close:.2f} < {current_open:.2f})")
    print(f"5b. Bullish Support: {has_bullish_element} (Lower wick {lower_wick:.3f} > Upper wick {upper_wick:.3f})")
    print(f"5. Conflicted Candle (SELL): {conflicted_candle_sell}")
    
    # SELL Final result
    sell_signal = ema7_sell and rsi_sell_ok and angle_sell_ok and prev_green and conflicted_candle_sell
    print(f"\nSELL SIGNAL: {sell_signal}")
    
    print(f"\n=== FINAL RESULT ===")
    if buy_signal:
        print("✅ BUY SIGNAL TRIGGERED!")
        print("   - Bullish close with bearish rejection after previous RED candle")
    elif sell_signal:
        print("✅ SELL SIGNAL TRIGGERED!")
        print("   - Bearish close with bullish support after previous GREEN candle")
    else:
        print("❌ NO SIGNAL - Missing conditions:")
        if not buy_signal:
            print("  BUY missing:")
            if not ema7_buy: print("    - Price not above EMA7")
            if not rsi_ok: print("    - RSI not > 30")
            if not angle_ok: print("    - EMA7 angle not > +77°")
            if not prev_red: print("    - Previous candle not RED")
            if not conflicted_candle_buy: print("    - Not a conflicted candle (need bullish close + bearish rejection)")
        
        if not sell_signal:
            print("  SELL missing:")
            if not ema7_sell: print("    - Price not below EMA7")
            if not rsi_sell_ok: print("    - RSI not < 70")
            if not angle_sell_ok: print("    - EMA7 angle not < -77°")
            if not prev_green: print("    - Previous candle not GREEN")
            if not conflicted_candle_sell: print("    - Not a conflicted candle (need bearish close + bullish support)")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_conflicted_candle_logic()