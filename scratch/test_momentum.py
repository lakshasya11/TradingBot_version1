
import pandas as pd
import numpy as np
from enhanced_strategy import EnhancedTradingStrategy

def test_momentum_logic():
    print("=== TESTING MOMENTUM ENTRY CONDITION ===")
    
    # Mock analysis data
    # Scenario: BUY indicators met, but Price <= Prev Close
    analysis_fail = {
        'ema7_buy': True,
        'ema7_sell': False,
        'rsi': 45,
        'ema7_angle': 80.0,
        'completed_candle_color': 'GREEN',
        'prev_close': 2350.00,
        'close': 2349.50, # Price is BELOW prev close -> Should FAIL
        'open': 2349.00,
    }
    
    # Scenario: BUY indicators met, and Price > Prev Close
    analysis_pass = {
        'ema7_buy': True,
        'ema7_sell': False,
        'rsi': 45,
        'ema7_angle': 80.0,
        'completed_candle_color': 'GREEN',
        'prev_close': 2350.00,
        'close': 2350.50, # Price is ABOVE prev close -> Should PASS
        'open': 2350.10,
    }
    
    strategy = EnhancedTradingStrategy("XAUUSD", "M1")
    
    print("\nTest 1: Price <= Prev Close (Should return NONE)")
    result1 = strategy.check_entry_conditions(analysis_fail)
    print(f"Result: {result1}")
    
    print("\nTest 2: Price > Prev Close (Should return BUY)")
    result2 = strategy.check_entry_conditions(analysis_pass)
    print(f"Result: {result2}")

    # SELL tests
    analysis_sell_fail = {
        'ema7_buy': False,
        'ema7_sell': True,
        'rsi': 55,
        'ema7_angle': -80.0,
        'completed_candle_color': 'RED',
        'prev_close': 2350.00,
        'close': 2350.50, # Price is ABOVE prev close -> Should FAIL
        'open': 2351.00,
    }
    
    analysis_sell_pass = {
        'ema7_buy': False,
        'ema7_sell': True,
        'rsi': 55,
        'ema7_angle': -80.0,
        'completed_candle_color': 'RED',
        'prev_close': 2350.00,
        'close': 2349.50, # Price is BELOW prev close -> Should PASS
        'open': 2349.80,
    }
    
    print("\nTest 3: Price >= Prev Close for SELL (Should return NONE)")
    result3 = strategy.check_entry_conditions(analysis_sell_fail)
    print(f"Result: {result3}")
    
    print("\nTest 4: Price < Prev Close for SELL (Should return SELL)")
    result4 = strategy.check_entry_conditions(analysis_sell_pass)
    print(f"Result: {result4}")

if __name__ == "__main__":
    test_momentum_logic()
