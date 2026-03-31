from advanced_entry_logic import CandleStructureValidator

def test_candle_validation():
    """Test the candle structure validation with sample data"""
    
    validator = CandleStructureValidator()
    
    print("🔍 TESTING CANDLE STRUCTURE VALIDATION")
    print("=" * 50)
    
    # Test Case 1: Strong Green Candle (Should PASS)
    strong_candle = {
        'open': 100.0,
        'close': 101.5,  # 1.5% body
        'high': 102.0,
        'low': 99.5,
        'time': '2024-01-01 10:00:00'
    }
    
    current_price = 101.8  # Price in top 60% of range
    
    is_valid, message = validator.validate_strong_green_candle(strong_candle, current_price)
    strength_score = validator.get_candle_strength_score(strong_candle, current_price)
    
    print(f"TEST 1 - Strong Green Candle:")
    print(f"  Data: Open={strong_candle['open']}, Current={current_price}, High={strong_candle['high']}, Low={strong_candle['low']}")
    print(f"  Result: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print(f"  Message: {message}")
    print(f"  Strength Score: {strength_score:.1f}/100")
    print()
    
    # Test Case 2: Weak Candle (Should FAIL)
    weak_candle = {
        'open': 100.0,
        'close': 100.1,  # Only 0.1% body
        'high': 101.0,
        'low': 99.0,
        'time': '2024-01-01 10:05:00'
    }
    
    is_valid2, message2 = validator.validate_strong_green_candle(weak_candle)
    strength_score2 = validator.get_candle_strength_score(weak_candle)
    
    print(f"TEST 2 - Weak Green Candle:")
    print(f"  Data: Open={weak_candle['open']}, Close={weak_candle['close']}, High={weak_candle['high']}, Low={weak_candle['low']}")
    print(f"  Result: {'✅ PASS' if is_valid2 else '❌ FAIL'}")
    print(f"  Message: {message2}")
    print(f"  Strength Score: {strength_score2:.1f}/100")
    print()
    
    # Test Case 3: Breakout Structure Test
    prev_red_candle = {
        'open': 100.0,
        'close': 99.0,  # Red candle
        'high': 100.5,
        'low': 98.5
    }
    
    current_breakout = {
        'open': 99.2,
        'close': 101.0,
        'high': 101.2,  # Breaks above prev high (100.5)
        'low': 99.0
    }
    
    breakout_valid, breakout_msg = validator.validate_breakout_structure(current_breakout, prev_red_candle)
    
    print(f"TEST 3 - Breakout Structure (Red → Green):")
    print(f"  Previous: Red candle High={prev_red_candle['high']}")
    print(f"  Current: High={current_breakout['high']}")
    print(f"  Result: {'✅ PASS' if breakout_valid else '❌ FAIL'}")
    print(f"  Message: {breakout_msg}")
    print()
    
    print("=" * 50)
    print("✅ Candle validation testing complete!")

if __name__ == "__main__":
    test_candle_validation()