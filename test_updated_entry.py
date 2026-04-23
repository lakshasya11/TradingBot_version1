"""
Test updated entry conditions to verify they're working correctly
"""
import MetaTrader5 as mt5
import pandas as pd
from indicators import TechnicalIndicators
import os
from dotenv import load_dotenv

def test_updated_entry_conditions():
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
    # ema7 = TechnicalIndicators.calculate_ema7(close)
    # ema7_angle = TechnicalIndicators.calculate_ema7_angle(ema7, symbol)
    
    # Current candle analysis
    current_candle_color = 'GREEN' if current_close > current_open else 'RED'
    prev_candle_color = 'GREEN' if prev_close > prev_open else 'RED'
    
    # Price action analysis
    candle_range = current_high - current_low
    price_position = (current_close - current_low) / candle_range if candle_range > 0 else 0.5
    
    print("=== UPDATED ENTRY CONDITIONS TEST ===")
    print(f"Price: {current_close:.2f}")
    # print(f"EMA7: {ema7.iloc[-1]:.2f}")
    # print(f"EMA7 Angle: {ema7_angle:.2f}°")
    print(f"RSI: {rsi.iloc[-1]:.1f}")
    print(f"Current Candle: {current_candle_color} (Open: {current_open:.2f}, Close: {current_close:.2f})")
    print(f"Previous Candle: {prev_candle_color}")
    print(f"Price Position in Range: {price_position:.1%}")
    
    print(f"\n=== BUY ENTRY CONDITIONS CHECK ===")
    
    # Basic conditions
    # ema7_buy = current_close > ema7.iloc[-1]
    rsi_ok = rsi.iloc[-1] > 30
    # angle_ok = ema7_angle > 77.0
    
    # print(f"1. Price > EMA7: {ema7_buy} ({current_close:.2f} > {ema7.iloc[-1]:.2f})")
    print(f"2. RSI > 30: {rsi_ok} ({rsi.iloc[-1]:.1f} > 30)")
    # print(f"3. EMA7 Angle > +77°: {angle_ok} ({ema7_angle:.2f}° > 77°)")
    
    # BUY-side price action (current candle)
    price_above_open = current_close > current_open
    low_to_high_recovery = price_position > 0.6
    buy_side_valid = price_above_open or low_to_high_recovery
    
    print(f"4a. BUY-side: Price > Open: {price_above_open} ({current_close:.2f} > {current_open:.2f})")
    print(f"4b. BUY-side: Recovery (>60%): {low_to_high_recovery} ({price_position:.1%} > 60%)")
    print(f"4. BUY-side Valid: {buy_side_valid}")
    
    # SELL-side price action (current candle) + Previous RED
    price_below_open = current_close < current_open
    high_to_low_decline = price_position < 0.4
    sell_side_valid = (price_below_open or high_to_low_decline) and prev_candle_color == 'RED'
    
    print(f"5a. SELL-side: Price < Open: {price_below_open} ({current_close:.2f} < {current_open:.2f})")
    print(f"5b. SELL-side: Decline (<40%): {high_to_low_decline} ({price_position:.1%} < 40%)")
    print(f"5c. SELL-side: Prev Candle RED: {prev_candle_color == 'RED'} ({prev_candle_color})")
    print(f"5. SELL-side Valid: {sell_side_valid}")
    
    # BUY Final result
    buy_signal = ema7_buy and rsi_ok and angle_ok and buy_side_valid and sell_side_valid
    print(f"\nBUY SIGNAL: {buy_signal}")
    
    print(f"\n=== SELL ENTRY CONDITIONS CHECK ===")
    
    # Basic conditions
    # ema7_sell = current_close < ema7.iloc[-1]
    rsi_sell_ok = rsi.iloc[-1] < 70
    # angle_sell_ok = ema7_angle < -77.0
    
    # print(f"1. Price < EMA7: {ema7_sell} ({current_close:.2f} < {ema7.iloc[-1]:.2f})")
    print(f"2. RSI < 70: {rsi_sell_ok} ({rsi.iloc[-1]:.1f} < 70)")
    # print(f"3. EMA7 Angle < -77°: {angle_sell_ok} ({ema7_angle:.2f}° < -77°)")
    
    # SELL-side price action (current candle)
    sell_side_valid_sell = price_below_open or high_to_low_decline
    print(f"4. SELL-side Valid: {sell_side_valid_sell}")
    
    # BUY-side price action (current candle) + Previous GREEN
    buy_side_valid_sell = (price_above_open or low_to_high_recovery) and prev_candle_color == 'GREEN'
    print(f"5a. BUY-side: Price > Open OR Recovery: {price_above_open or low_to_high_recovery}")
    print(f"5b. BUY-side: Prev Candle GREEN: {prev_candle_color == 'GREEN'} ({prev_candle_color})")
    print(f"5. BUY-side Valid: {buy_side_valid_sell}")
    
    # SELL Final result
    sell_signal = ema7_sell and rsi_sell_ok and angle_sell_ok and sell_side_valid_sell and buy_side_valid_sell
    print(f"\nSELL SIGNAL: {sell_signal}")
    
    print(f"\n=== FINAL RESULT ===")
    if buy_signal:
        print("✅ BUY SIGNAL TRIGGERED!")
    elif sell_signal:
        print("✅ SELL SIGNAL TRIGGERED!")
    else:
        print("❌ NO SIGNAL - Missing conditions:")
        if not buy_signal:
            print("  BUY missing:")
            # if not ema7_buy: print("    - Price not above EMA7")
            if not rsi_ok: print("    - RSI not > 30")
            # if not angle_ok: print("    - EMA7 angle not > +77°")
            if not buy_side_valid: print("    - BUY-side price action not valid")
            if not sell_side_valid: print("    - SELL-side price action not valid (need current breakdown/decline + prev RED)")
        
        if not sell_signal:
            print("  SELL missing:")
            # if not ema7_sell: print("    - Price not below EMA7")
            if not rsi_sell_ok: print("    - RSI not < 70")
            # if not angle_sell_ok: print("    - EMA7 angle not < -77°")
            if not sell_side_valid_sell: print("    - SELL-side price action not valid")
            if not buy_side_valid_sell: print("    - BUY-side price action not valid (need current breakout/recovery + prev GREEN)")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_updated_entry_conditions()