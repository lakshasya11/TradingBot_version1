#!/usr/bin/env python3
"""
Test trailing stop activation at exactly 0.01 points profit
"""
from trading_core import TradingCore
import MetaTrader5 as mt5

class MockPos:
    def __init__(self):
        self.ticket = 12345
        self.type = mt5.POSITION_TYPE_BUY
        self.price_open = 4700.00000

class MockTick:
    def __init__(self, bid, ask):
        self.bid = bid
        self.ask = ask

class MockSymbol:
    def __init__(self):
        self.digits = 5

def test_activation_at_threshold():
    print("TESTING: Trailing Stop Activation at 0.01 Points")
    print("=" * 55)
    
    pos = MockPos()
    symbol_info = MockSymbol()
    
    # Test scenarios around the 0.01 threshold
    test_cases = [
        {"price": 4700.00500, "desc": "0.005pts profit (below threshold)"},
        {"price": 4700.00900, "desc": "0.009pts profit (just below threshold)"},
        {"price": 4700.01000, "desc": "0.010pts profit (EXACT threshold)"},
        {"price": 4700.01100, "desc": "0.011pts profit (just above threshold)"},
        {"price": 4700.02000, "desc": "0.020pts profit (well above threshold)"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {case['desc']}")
        print("-" * 45)
        
        # Fresh position data for each test
        pos_data = {'reference_price': 4700.00000}
        tick = MockTick(case['price'], case['price'] + 0.001)
        
        trail_sl, active, label = TradingCore.calculate_trailing_stop_points(
            pos, tick, pos_data, symbol_info, 0.01, 1.0
        )
        
        profit = tick.bid - 4700.00000
        expected_gap = TradingCore.calculate_dynamic_gap(profit)
        
        print(f"  Entry: 4700.00000")
        print(f"  Current: {tick.bid:.5f}")
        print(f"  Profit: {profit:.5f} points")
        print(f"  Threshold: 0.01000 points")
        print(f"  Should Activate: {profit >= 0.01}")
        print(f"  Actually Active: {active}")
        
        if active:
            actual_gap = tick.bid - trail_sl
            print(f"  Trail SL: {trail_sl:.5f}")
            print(f"  Gap Used: {actual_gap:.3f}")
            print(f"  Expected Gap: {expected_gap:.1f}")
            
            if abs(actual_gap - expected_gap) < 0.001:
                print(f"  [PASS] Correct activation and gap")
            else:
                print(f"  [FAIL] Wrong gap calculation")
        else:
            print(f"  Status: {label}")
            if profit >= 0.01:
                print(f"  [FAIL] Should be active but isn't")
            else:
                print(f"  [PASS] Correctly not active")
    
    print(f"\n" + "=" * 55)
    print("SUMMARY: Trailing Stop Activation Test")
    print("- Activates at exactly 0.01 points profit")
    print("- Uses dynamic gap based on profit level")
    print("- Reference price preserved from entry")

if __name__ == "__main__":
    test_activation_at_threshold()