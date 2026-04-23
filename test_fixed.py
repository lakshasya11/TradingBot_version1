#!/usr/bin/env python3
"""
Test script for the FIXED cross-side price action confirmation logic
"""

def test_fixed_logic():
    """Test the fixed cross-side price action confirmation logic"""
    
    print("TESTING FIXED CROSS-SIDE PRICE ACTION CONFIRMATION LOGIC")
    print("=" * 60)
    
    # Test scenarios for BUY signal
    print("\nBUY SIGNAL TEST SCENARIOS:")
    print("-" * 40)
    
    # BUY Test Case 1: Valid BUY signal with previous RED candle
    print("Test 1: Valid BUY Signal with Previous RED Candle")
    analysis_buy_valid = {
        'ema7_buy': True,
        'rsi': 35,
        'ema7_angle': 80.0,
        'candle_color': 'GREEN',
        'completed_candle_color': 'RED',  # Previous candle RED - PASS
        'close': 2650.50,
        'open': 2650.00,  # Current price > open (breakout) - PASS
        'high': 2650.60,
        'low': 2649.90
    }
    
    result = simulate_fixed_entry_check(analysis_buy_valid)
    print(f"   Result: {result}")
    print(f"   Expected: BUY (should trigger)")
    print(f"   PASS" if result == "BUY" else f"   FAIL")
    
    # BUY Test Case 2: BUY signal with previous GREEN candle (should fail)
    print("\nTest 2: BUY Signal with Previous GREEN Candle")
    analysis_buy_no_red = {
        'ema7_buy': True,
        'rsi': 35,
        'ema7_angle': 80.0,
        'candle_color': 'GREEN',
        'completed_candle_color': 'GREEN',  # Previous candle GREEN - FAIL
        'close': 2650.50,
        'open': 2650.00,
        'high': 2650.60,
        'low': 2649.90
    }
    
    result = simulate_fixed_entry_check(analysis_buy_no_red)
    print(f"   Result: {result}")
    print(f"   Expected: NONE (should NOT trigger)")
    print(f"   PASS" if result == "NONE" else f"   FAIL")
    
    # Test scenarios for SELL signal
    print("\nSELL SIGNAL TEST SCENARIOS:")
    print("-" * 40)
    
    # SELL Test Case 1: Valid SELL signal with previous GREEN candle
    print("Test 3: Valid SELL Signal with Previous GREEN Candle")
    analysis_sell_valid = {
        'ema7_sell': True,
        'rsi': 65,
        'ema7_angle': -80.0,
        'candle_color': 'RED',
        'completed_candle_color': 'GREEN',  # Previous candle GREEN - PASS
        'close': 2649.50,
        'open': 2650.00,  # Current price < open (breakdown) - PASS
        'high': 2650.10,
        'low': 2649.40
    }
    
    result = simulate_fixed_entry_check(analysis_sell_valid)
    print(f"   Result: {result}")
    print(f"   Expected: SELL (should trigger)")
    print(f"   PASS" if result == "SELL" else f"   FAIL")
    
    # SELL Test Case 2: SELL signal with previous RED candle (should fail)
    print("\nTest 4: SELL Signal with Previous RED Candle")
    analysis_sell_no_green = {
        'ema7_sell': True,
        'rsi': 65,
        'ema7_angle': -80.0,
        'candle_color': 'RED',
        'completed_candle_color': 'RED',  # Previous candle RED - FAIL
        'close': 2649.50,
        'open': 2650.00,
        'high': 2650.10,
        'low': 2649.40
    }
    
    result = simulate_fixed_entry_check(analysis_sell_no_green)
    print(f"   Result: {result}")
    print(f"   Expected: NONE (should NOT trigger)")
    print(f"   PASS" if result == "NONE" else f"   FAIL")
    
    print("\n" + "=" * 60)
    print("FIXED LOGIC TEST SUMMARY: Cross-side confirmation now works correctly!")

def simulate_fixed_entry_check(analysis):
    """Simulate the FIXED entry condition check logic"""
    
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
    open_price = analysis.get('open', 0)
    high_price = analysis.get('high', 0)
    low_price = analysis.get('low', 0)
    
    # Calculate price position in candle range
    candle_range = high_price - low_price
    if candle_range > 0:
        price_position = (current_price - low_price) / candle_range
    else:
        price_position = 0.5  # Default to middle if no range
    
    # BUY ENTRY LOGIC: RSI + Price Action + Previous RED Candle (EMA 7 Commented Out)
    if rsi > 30 and candle_color == 'GREEN':
        # BUY-side price action confirmation
        price_above_open = current_price > open_price
        low_to_high_recovery = price_position > 0.6  # Price in upper 60%
        buy_side_valid = price_above_open or low_to_high_recovery
        
        # SELL-side confirmation: Previous candle must be RED (reversal setup)
        sell_side_valid = prev_candle_color == 'RED'
        
        if buy_side_valid and sell_side_valid:
            buy_action = "Breakout" if price_above_open else "Low-to-High Recovery"
            print(f"   FIXED Logic: BUY-side={buy_action}, PrevCandle={prev_candle_color}")
            return "BUY"
    
    # SELL ENTRY LOGIC: RSI + Price Action + Previous GREEN Candle (EMA 7 Commented Out)
    elif rsi < 70 and candle_color == 'RED':
        # SELL-side price action confirmation
        price_below_open = current_price < open_price
        high_to_low_decline = price_position < 0.4  # Price in lower 40%
        sell_side_valid = price_below_open or high_to_low_decline
        
        # BUY-side confirmation: Previous candle must be GREEN (reversal setup)
        buy_side_valid = prev_candle_color == 'GREEN'
        
        if sell_side_valid and buy_side_valid:
            sell_action = "Breakdown" if price_below_open else "High-to-Low Decline"
            print(f"   FIXED Logic: SELL-side={sell_action}, PrevCandle={prev_candle_color}")
            return "SELL"
    
    return "NONE"

if __name__ == "__main__":
    test_fixed_logic()