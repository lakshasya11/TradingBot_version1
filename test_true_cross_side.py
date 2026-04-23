#!/usr/bin/env python3
"""
Test script for TRUE cross-side price action confirmation logic
"""
import pandas as pd

def test_true_cross_side_logic():
    """Test the true cross-side price action confirmation logic"""
    
    print("TESTING TRUE CROSS-SIDE PRICE ACTION CONFIRMATION LOGIC")
    print("=" * 65)
    
    # Test scenarios for BUY signal
    print("\nBUY SIGNAL TEST SCENARIOS:")
    print("-" * 45)
    
    # BUY Test Case 1: Valid BUY signal
    print("Test 1: Valid BUY Signal")
    print("  Current: GREEN candle, price > open (breakout)")
    print("  Previous: RED candle, price < open (breakdown)")
    
    # Create mock dataframe with previous candle data
    df_buy_valid = pd.DataFrame({
        'close': [2649.50, 2650.50],    # Previous: 2649.50, Current: 2650.50
        'open':  [2650.00, 2650.00],    # Previous: 2650.00, Current: 2650.00
        'high':  [2650.10, 2650.60],    # Previous: 2650.10, Current: 2650.60
        'low':   [2649.40, 2649.90]     # Previous: 2649.40, Current: 2649.90
    })
    
    analysis_buy_valid = {
        'ema7_buy': True,
        'rsi': 35,
        'ema7_angle': 80.0,
        'candle_color': 'GREEN',           # Current candle GREEN
        'completed_candle_color': 'RED',   # Previous candle RED
        'close': 2650.50,                  # Current close > current open (breakout)
        'open': 2650.00,
        'high': 2650.60,
        'low': 2649.90,
        'df': df_buy_valid
    }
    
    result = simulate_true_cross_side_check(analysis_buy_valid)
    print(f"   Result: {result}")
    print(f"   Expected: BUY (should trigger)")
    print(f"   PASS" if result == "BUY" else f"   FAIL")
    
    # BUY Test Case 2: Missing previous breakdown
    print("\nTest 2: BUY Signal - Missing Previous Breakdown")
    print("  Current: GREEN candle, price > open (breakout)")
    print("  Previous: RED candle, price > open (NO breakdown)")
    
    df_buy_no_breakdown = pd.DataFrame({
        'close': [2650.50, 2650.50],    # Previous: 2650.50 > 2650.00 (NO breakdown)
        'open':  [2650.00, 2650.00],
        'high':  [2650.60, 2650.60],
        'low':   [2649.90, 2649.90]
    })
    
    analysis_buy_no_breakdown = {
        'ema7_buy': True,
        'rsi': 35,
        'ema7_angle': 80.0,
        'candle_color': 'GREEN',
        'completed_candle_color': 'RED',
        'close': 2650.50,
        'open': 2650.00,
        'high': 2650.60,
        'low': 2649.90,
        'df': df_buy_no_breakdown
    }
    
    result = simulate_true_cross_side_check(analysis_buy_no_breakdown)
    print(f"   Result: {result}")
    print(f"   Expected: NONE (should NOT trigger)")
    print(f"   PASS" if result == "NONE" else f"   FAIL")
    
    # Test scenarios for SELL signal
    print("\nSELL SIGNAL TEST SCENARIOS:")
    print("-" * 45)
    
    # SELL Test Case 1: Valid SELL signal
    print("Test 3: Valid SELL Signal")
    print("  Current: RED candle, price < open (breakdown)")
    print("  Previous: GREEN candle, price > open (breakout)")
    
    df_sell_valid = pd.DataFrame({
        'close': [2650.50, 2649.50],    # Previous: 2650.50, Current: 2649.50
        'open':  [2650.00, 2650.00],    # Previous: 2650.00, Current: 2650.00
        'high':  [2650.60, 2650.10],    # Previous: 2650.60, Current: 2650.10
        'low':   [2649.90, 2649.40]     # Previous: 2649.90, Current: 2649.40
    })
    
    analysis_sell_valid = {
        'ema7_sell': True,
        'rsi': 65,
        'ema7_angle': -80.0,
        'candle_color': 'RED',             # Current candle RED
        'completed_candle_color': 'GREEN', # Previous candle GREEN
        'close': 2649.50,                  # Current close < current open (breakdown)
        'open': 2650.00,
        'high': 2650.10,
        'low': 2649.40,
        'df': df_sell_valid
    }
    
    result = simulate_true_cross_side_check(analysis_sell_valid)
    print(f"   Result: {result}")
    print(f"   Expected: SELL (should trigger)")
    print(f"   PASS" if result == "SELL" else f"   FAIL")
    
    # SELL Test Case 2: Missing previous breakout
    print("\nTest 4: SELL Signal - Missing Previous Breakout")
    print("  Current: RED candle, price < open (breakdown)")
    print("  Previous: GREEN candle, price < open (NO breakout)")
    
    df_sell_no_breakout = pd.DataFrame({
        'close': [2649.50, 2649.50],    # Previous: 2649.50 < 2650.00 (NO breakout)
        'open':  [2650.00, 2650.00],
        'high':  [2650.10, 2650.10],
        'low':   [2649.40, 2649.40]
    })
    
    analysis_sell_no_breakout = {
        'ema7_sell': True,
        'rsi': 65,
        'ema7_angle': -80.0,
        'candle_color': 'RED',
        'completed_candle_color': 'GREEN',
        'close': 2649.50,
        'open': 2650.00,
        'high': 2650.10,
        'low': 2649.40,
        'df': df_sell_no_breakout
    }
    
    result = simulate_true_cross_side_check(analysis_sell_no_breakout)
    print(f"   Result: {result}")
    print(f"   Expected: NONE (should NOT trigger)")
    print(f"   PASS" if result == "NONE" else f"   FAIL")
    
    print("\n" + "=" * 65)
    print("TRUE CROSS-SIDE LOGIC TEST SUMMARY: Both current AND previous price action required!")

def simulate_true_cross_side_check(analysis):
    """Simulate the TRUE cross-side entry condition check logic"""
    
    if not analysis:
        return "NONE"

    # Get EMA 7 signals, RSI, angle, and candle colors
    rsi = analysis.get('rsi', 50)
    ema7_buy = analysis.get('ema7_buy', False)
    ema7_sell = analysis.get('ema7_sell', False)
    ema7_angle = analysis.get('ema7_angle', 0.0)
    candle_color = analysis.get('candle_color', '')  # Current candle
    prev_candle_color = analysis.get('completed_candle_color', '')  # Previous completed candle
    
    # Get current candle OHLC for price action confirmation
    current_price = analysis.get('close', 0)
    current_open = analysis.get('open', 0)
    high_price = analysis.get('high', 0)
    low_price = analysis.get('low', 0)
    
    # Get previous candle OHLC from dataframe
    df = analysis.get('df')
    if df is None or len(df) < 2:
        return "NONE"  # Need at least 2 candles
    
    prev_close = df['close'].iloc[-2]
    prev_open = df['open'].iloc[-2]
    prev_high = df['high'].iloc[-2]
    prev_low = df['low'].iloc[-2]
    
    print(f"   DEBUG: Current - Close={current_price}, Open={current_open}")
    print(f"   DEBUG: Previous - Close={prev_close}, Open={prev_open}, Color={prev_candle_color}")
    
    # Calculate price position in candle range for recovery/decline detection
    candle_range = high_price - low_price
    if candle_range > 0:
        price_position = (current_price - low_price) / candle_range
    else:
        price_position = 0.5  # Default to middle if no range
    
    # BUY ENTRY LOGIC: RSI + DUAL Price Action + GREEN CANDLE (EMA 7 Commented Out)
    if rsi > 30 and candle_color == 'GREEN':
        # BUY-side price action: Current price > Current open (breakout)
        price_above_open = current_price > current_open
        low_to_high_recovery = price_position > 0.6  # Price in upper 60%
        buy_side_valid = price_above_open or low_to_high_recovery
        
        # SELL-side price action: Previous price < Previous open (breakdown) + RED candle
        prev_price_below_open = prev_close < prev_open
        prev_candle_range = prev_high - prev_low
        if prev_candle_range > 0:
            prev_price_position = (prev_close - prev_low) / prev_candle_range
            prev_high_to_low_decline = prev_price_position < 0.4  # Price in lower 40%
        else:
            prev_high_to_low_decline = False
        
        sell_side_valid = (prev_price_below_open or prev_high_to_low_decline) and prev_candle_color == 'RED'
        
        print(f"   DEBUG: BUY-side valid={buy_side_valid} (current {current_price} > {current_open})")
        print(f"   DEBUG: SELL-side valid={sell_side_valid} (prev {prev_close} < {prev_open} + RED)")
        
        if buy_side_valid and sell_side_valid:
            buy_action = "Breakout" if price_above_open else "Low-to-High Recovery"
            sell_action = "Prev Breakdown" if prev_price_below_open else "Prev High-to-Low Decline"
            print(f"   LOGIC: BUY:{buy_action} + SELL:{sell_action}")
            return "BUY"
    
    # SELL ENTRY LOGIC: RSI + DUAL Price Action + RED CANDLE (EMA 7 Commented Out)
    elif rsi < 70 and candle_color == 'RED':
        # SELL-side price action: Current price < Current open (breakdown)
        price_below_open = current_price < current_open
        high_to_low_decline = price_position < 0.4  # Price in lower 40%
        sell_side_valid = price_below_open or high_to_low_decline
        
        # BUY-side price action: Previous price > Previous open (breakout) + GREEN candle
        prev_price_above_open = prev_close > prev_open
        prev_candle_range = prev_high - prev_low
        if prev_candle_range > 0:
            prev_price_position = (prev_close - prev_low) / prev_candle_range
            prev_low_to_high_recovery = prev_price_position > 0.6  # Price in upper 60%
        else:
            prev_low_to_high_recovery = False
        
        buy_side_valid = (prev_price_above_open or prev_low_to_high_recovery) and prev_candle_color == 'GREEN'
        
        print(f"   DEBUG: SELL-side valid={sell_side_valid} (current {current_price} < {current_open})")
        print(f"   DEBUG: BUY-side valid={buy_side_valid} (prev {prev_close} > {prev_open} + GREEN)")
        
        if sell_side_valid and buy_side_valid:
            sell_action = "Breakdown" if price_below_open else "High-to-Low Decline"
            buy_action = "Prev Breakout" if prev_price_above_open else "Prev Low-to-High Recovery"
            print(f"   LOGIC: SELL:{sell_action} + BUY:{buy_action}")
            return "SELL"
    
    return "NONE"

if __name__ == "__main__":
    test_true_cross_side_logic()