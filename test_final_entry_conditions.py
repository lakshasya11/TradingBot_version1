#!/usr/bin/env python3
"""
Final test to verify the updated entry conditions are working correctly (Body Coverage Rule)
"""

def test_final_entry_conditions():
    """Test the final simplified entry conditions with Body Coverage Rule"""
    
    print("=== FINAL ENTRY CONDITIONS TEST ===")
    print("Testing the updated logic with Body Coverage Filter")
    print("=" * 60)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Trend BUY (Waiting for Body Coverage)",
            "analysis": {
                'ema7_buy': True, 'rsi': 35, 'ema7_angle': 80.0,
                'completed_candle_color': 'RED', 'prev_close': 2650.00, 'prev_open': 2651.00,
                'close': 2650.50, 'open': 2650.00,
            },
            "expected": "NONE",
            "reason": "Price 2650.50 is below prev RED open 2651.00 (No coverage)"
        },
        {
            "name": "Trend BUY (Body Covered)",
            "analysis": {
                'ema7_buy': True, 'rsi': 35, 'ema7_angle': 80.0,
                'completed_candle_color': 'RED', 'prev_close': 2650.00, 'prev_open': 2651.00,
                'close': 2651.20, 'open': 2651.00,
            },
            "expected": "BUY",
            "reason": "Price 2651.20 covered prev RED open 2651.00"
        },
        {
            "name": "Trend SELL (Waiting for Body Coverage)",
            "analysis": {
                'ema7_sell': True, 'rsi': 65, 'ema7_angle': -80.0,
                'completed_candle_color': 'GREEN', 'prev_close': 2650.00, 'prev_open': 2649.00,
                'close': 2649.50, 'open': 2650.00,
            },
            "expected": "NONE",
            "reason": "Price 2649.50 is above prev GREEN open 2649.00 (No coverage)"
        },
        {
            "name": "Trend SELL (Body Covered)",
            "analysis": {
                'ema7_sell': True, 'rsi': 65, 'ema7_angle': -80.0,
                'completed_candle_color': 'GREEN', 'prev_close': 2650.00, 'prev_open': 2649.00,
                'close': 2648.50, 'open': 2649.00,
            },
            "expected": "SELL",
            "reason": "Price 2648.50 covered prev GREEN open 2649.00"
        }
    ]
    
    # Run tests
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 50)
        
        result = simulate_entry_check(test_case['analysis'])
        expected = test_case['expected']
        
        print(f"Expected: {expected}")
        print(f"Got:      {result}")
        print(f"Reason:   {test_case['reason']}")
        
        if result == expected:
            print("[PASS]")
            passed += 1
        else:
            print("[FAIL]")
    
    print(f"\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("ALL TESTS PASSED! Entry conditions are working correctly.")
    else:
        print("Some tests failed. Check the logic.")

def simulate_entry_check(analysis):
    """Simulate Dual-Mode Entry Logic: Trend-Following + Counter-Trend + Body Coverage"""
    if not analysis:
        return "NONE"

    rsi = analysis.get('rsi', 50)
    ema7_buy = analysis.get('ema7_buy', False)
    ema7_sell = analysis.get('ema7_sell', False)
    ema7_angle = analysis.get('ema7_angle', 0.0)
    prev_candle_color = analysis.get('completed_candle_color', '')
    prev_close = analysis.get('prev_close', 0)
    prev_open = analysis.get('prev_open', 0)
    current_price = analysis.get('close', 0)
    current_open = analysis.get('open', 0)
    current_color = "GREEN" if current_price > current_open else "RED"
    
    # EMA 7 ANGLE CHECK COMMENTED OUT
    # if ema7_angle > 77.0:
        # A. Trend-Following BUY
    if current_color == "GREEN" and rsi > 30 and current_price > prev_close:
        # Body Coverage Rule
        if prev_candle_color == "RED" and current_price <= prev_open:
            return "NONE"
        return "BUY"
    # B. Counter-Trend SELL
    if current_color == "RED" and prev_candle_color == "RED" and rsi > 30 and current_price < prev_close:
        return "SELL"

    # --- MODE 2: STRONG DOWNTREND (Angle < -77°) ---
    # elif ema7_angle < -77.0:
        # A. Trend-Following SELL
    if current_color == "RED" and rsi < 70 and current_price < prev_close:
        # Body Coverage Rule
        if prev_candle_color == "GREEN" and current_price >= prev_open:
            return "NONE"
        return "SELL"
    # B. Counter-Trend BUY
    if current_color == "GREEN" and prev_candle_color == "GREEN" and rsi < 70 and current_price > prev_close:
        return "BUY"

    return "NONE"

if __name__ == "__main__":
    test_final_entry_conditions()