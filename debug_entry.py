"""
Debug script to check why entry conditions are not being met
"""
import MetaTrader5 as mt5
import pandas as pd
from indicators import TechnicalIndicators
import os
from dotenv import load_dotenv

def debug_entry_conditions():
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
    prev_high = df['high'].iloc[-2]
    prev_low = df['low'].iloc[-2]
    
    # Calculate indicators
    close = df['close']
    rsi = TechnicalIndicators.calculate_rsi(close, 14)
    ema7 = TechnicalIndicators.calculate_ema7(close)
    ema7_angle = TechnicalIndicators.calculate_ema7_angle(ema7, symbol)
    
    # Current candle analysis
    current_candle_color = 'GREEN' if current_close > current_open else 'RED'
    prev_candle_color = 'GREEN' if prev_close > prev_open else 'RED'
    
    # Price action analysis
    candle_range = current_high - current_low
    price_position = (current_close - current_low) / candle_range if candle_range > 0 else 0.5
    
    prev_candle_range = prev_high - prev_low
    prev_price_position = (prev_close - prev_low) / prev_candle_range if prev_candle_range > 0 else 0.5
    
    print("=== CURRENT MARKET CONDITIONS ===")
    print(f"Price: {current_close:.2f}")
    print(f"EMA7: {ema7.iloc[-1]:.2f}")
    print(f"EMA7 Angle: {ema7_angle:.2f}°")
    print(f"RSI: {rsi.iloc[-1]:.1f}")
    
    print(f"\n=== CURRENT CANDLE ===")
    print(f"Open: {current_open:.2f}")
    print(f"Close: {current_close:.2f}")
    print(f"High: {current_high:.2f}")
    print(f"Low: {current_low:.2f}")
    print(f"Color: {current_candle_color}")
    print(f"Price Position in Range: {price_position:.1%}")
    
    print(f"\n=== PREVIOUS CANDLE ===")
    print(f"Open: {prev_open:.2f}")
    print(f"Close: {prev_close:.2f}")
    print(f"High: {prev_high:.2f}")
    print(f"Low: {prev_low:.2f}")
    print(f"Color: {prev_candle_color}")
    print(f"Price Position in Range: {prev_price_position:.1%}")
    
    print(f"\n=== BUY ENTRY CONDITIONS CHECK ===")
    
    # Check each condition
    ema7_buy = current_close > ema7.iloc[-1]
    rsi_ok = rsi.iloc[-1] > 30
    angle_ok = ema7_angle > 77.0
    candle_ok = current_candle_color == 'GREEN'
    
    print(f"1. Price > EMA7: {ema7_buy} ({current_close:.2f} > {ema7.iloc[-1]:.2f})")
    print(f"2. RSI > 30: {rsi_ok} ({rsi.iloc[-1]:.1f} > 30)")
    print(f"3. EMA7 Angle > +77°: {angle_ok} ({ema7_angle:.2f}° > 77°)")
    print(f"4. Current Candle GREEN: {candle_ok} ({current_candle_color})")
    
    # BUY-side price action
    price_above_open = current_close > current_open
    low_to_high_recovery = price_position > 0.6
    buy_side_valid = price_above_open or low_to_high_recovery
    
    print(f"5a. BUY-side: Price > Open: {price_above_open} ({current_close:.2f} > {current_open:.2f})")
    print(f"5b. BUY-side: Recovery (>60%): {low_to_high_recovery} ({price_position:.1%} > 60%)")
    print(f"5. BUY-side Valid: {buy_side_valid}")
    
    # SELL-side price action (previous candle)
    prev_price_below_open = prev_close < prev_open
    prev_high_to_low_decline = prev_price_position < 0.4
    sell_side_valid = (prev_price_below_open or prev_high_to_low_decline) and prev_candle_color == 'RED'
    
    print(f"6a. SELL-side: Prev Price < Prev Open: {prev_price_below_open} ({prev_close:.2f} < {prev_open:.2f})")
    print(f"6b. SELL-side: Prev Decline (<40%): {prev_high_to_low_decline} ({prev_price_position:.1%} < 40%)")
    print(f"6c. SELL-side: Prev Candle RED: {prev_candle_color == 'RED'} ({prev_candle_color})")
    print(f"6. SELL-side Valid: {sell_side_valid}")
    
    # Final result
    all_conditions = ema7_buy and rsi_ok and angle_ok and candle_ok and buy_side_valid and sell_side_valid
    print(f"\n=== FINAL RESULT ===")
    print(f"ALL CONDITIONS MET: {all_conditions}")
    
    if not all_conditions:
        print("\n❌ MISSING CONDITIONS:")
        if not ema7_buy: print("- Price not above EMA7")
        if not rsi_ok: print("- RSI not > 30")
        if not angle_ok: print("- EMA7 angle not > +77°")
        if not candle_ok: print("- Current candle not GREEN")
        if not buy_side_valid: print("- BUY-side price action not valid")
        if not sell_side_valid: print("- SELL-side price action not valid (need previous RED candle with breakdown)")
    
    mt5.shutdown()

if __name__ == "__main__":
    debug_entry_conditions()