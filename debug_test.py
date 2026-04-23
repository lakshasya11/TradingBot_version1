#!/usr/bin/env python3
"""
Debug script to identify the issue in cross-side price action confirmation logic
"""

def debug_entry_check(analysis):
    """Debug version with detailed logging"""
    
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
    
    print(f"   DEBUG: RSI={rsi}, EMA7_Buy={ema7_buy}, EMA7_Sell={ema7_sell}")
    print(f"   DEBUG: EMA7_Angle={ema7_angle}, Current_Candle={candle_color}, Prev_Candle={prev_candle_color}")
    print(f"   DEBUG: Price={current_price}, Open={open_price}, High={high_price}, Low={low_price}")
    
    # Calculate price position in candle range
    candle_range = high_price - low_price
    if candle_range > 0:
        price_position = (current_price - low_price) / candle_range
    else:
        price_position = 0.5  # Default to middle if no range
    
    print(f"   DEBUG: Candle_Range={candle_range}, Price_Position={price_position:.2f}")
    
    # BUY ENTRY LOGIC: EMA7 + RSI + Angle + DUAL Price Action + GREEN CANDLE
    if ema7_buy and rsi > 30 and ema7_angle > 77.0 and candle_color == 'GREEN':
        print("   DEBUG: BUY basic conditions met, checking price action...")
        
        # BUY-side price action confirmation
        price_above_open = current_price > open_price
        low_to_high_recovery = price_position > 0.6  # Price in upper 60%
        buy_side_valid = price_above_open or low_to_high_recovery
        
        print(f"   DEBUG: BUY-side: price_above_open={price_above_open}, low_to_high_recovery={low_to_high_recovery}, buy_side_valid={buy_side_valid}")
        
        # SELL-side price action confirmation (NEW) + previous candle must be RED
        price_below_open = current_price < open_price
        high_to_low_decline = price_position < 0.4  # Price in lower 40%
        sell_side_valid = (price_below_open or high_to_low_decline) and prev_candle_color == 'RED'
        
        print(f"   DEBUG: SELL-side: price_below_open={price_below_open}, high_to_low_decline={high_to_low_decline}, prev_red={prev_candle_color == 'RED'}, sell_side_valid={sell_side_valid}")
        
        if buy_side_valid and sell_side_valid:
            buy_action = "Breakout" if price_above_open else "Low-to-High Recovery"
            sell_action = "Breakdown" if price_below_open else "High-to-Low Decline"
            print(f"   DEBUG: BOTH SIDES VALID - BUY:{buy_action}, SELL:{sell_action}")
            return "BUY"
        else:
            print(f"   DEBUG: CONDITIONS NOT MET - buy_side_valid={buy_side_valid}, sell_side_valid={sell_side_valid}")
    
    # SELL ENTRY LOGIC: EMA7 + RSI + Angle + DUAL Price Action + RED CANDLE
    elif ema7_sell and rsi < 70 and ema7_angle < -77.0 and candle_color == 'RED':
        print("   DEBUG: SELL basic conditions met, checking price action...")
        
        # SELL-side price action confirmation
        price_below_open = current_price < open_price
        high_to_low_decline = price_position < 0.4  # Price in lower 40%
        sell_side_valid = price_below_open or high_to_low_decline
        
        print(f"   DEBUG: SELL-side: price_below_open={price_below_open}, high_to_low_decline={high_to_low_decline}, sell_side_valid={sell_side_valid}")
        
        # BUY-side price action confirmation (NEW) + previous candle must be GREEN
        price_above_open = current_price > open_price
        low_to_high_recovery = price_position > 0.6  # Price in upper 60%
        buy_side_valid = (price_above_open or low_to_high_recovery) and prev_candle_color == 'GREEN'
        
        print(f"   DEBUG: BUY-side: price_above_open={price_above_open}, low_to_high_recovery={low_to_high_recovery}, prev_green={prev_candle_color == 'GREEN'}, buy_side_valid={buy_side_valid}")
        
        if sell_side_valid and buy_side_valid:
            sell_action = "Breakdown" if price_below_open else "High-to-Low Decline"
            buy_action = "Breakout" if price_above_open else "Low-to-High Recovery"
            print(f"   DEBUG: BOTH SIDES VALID - SELL:{sell_action}, BUY:{buy_action}")
            return "SELL"
        else:
            print(f"   DEBUG: CONDITIONS NOT MET - sell_side_valid={sell_side_valid}, buy_side_valid={buy_side_valid}")
    else:
        print("   DEBUG: Basic entry conditions not met")
    
    return "NONE"

def test_debug():
    """Test with debug output"""
    
    print("DEBUG TEST: BUY Signal")
    print("-" * 30)
    analysis_buy = {
        'ema7_buy': True,
        'rsi': 35,
        'ema7_angle': 80.0,
        'candle_color': 'GREEN',
        'completed_candle_color': 'RED',
        'close': 2650.50,
        'open': 2650.00,  # price > open = breakout
        'high': 2650.60,
        'low': 2649.90
    }
    
    result = debug_entry_check(analysis_buy)
    print(f"   FINAL RESULT: {result}")
    
    print("\nDEBUG TEST: SELL Signal")
    print("-" * 30)
    analysis_sell = {
        'ema7_sell': True,
        'rsi': 65,
        'ema7_angle': -80.0,
        'candle_color': 'RED',
        'completed_candle_color': 'GREEN',
        'close': 2649.50,
        'open': 2650.00,  # price < open = breakdown
        'high': 2650.10,
        'low': 2649.40
    }
    
    result = debug_entry_check(analysis_sell)
    print(f"   FINAL RESULT: {result}")

if __name__ == "__main__":
    test_debug()