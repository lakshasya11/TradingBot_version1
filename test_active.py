#!/usr/bin/env python3
"""
Quick test to verify dynamic trailing stop is active
"""
from trading_core import TradingCore
import MetaTrader5 as mt5

# Mock classes
class MockPos:
    def __init__(self):
        self.ticket = 12345
        self.type = mt5.POSITION_TYPE_BUY
        self.price_open = 4700.0

class MockTick:
    def __init__(self, bid, ask):
        self.bid = bid
        self.ask = ask

class MockSymbol:
    def __init__(self):
        self.digits = 5

def test_dynamic_trailing_active():
    print("TESTING: Is Dynamic Trailing Stop Active?")
    print("=" * 50)
    
    pos = MockPos()
    symbol_info = MockSymbol()
    pos_data = {'reference_price': 4700.0}
    
    # Test with 1.5 points profit (should use 0.8 gap)
    tick = MockTick(4701.5, 4701.6)
    
    trail_sl, active, label = TradingCore.calculate_trailing_stop_points(
        pos, tick, pos_data, symbol_info, 0.01, 1.0
    )
    
    profit = tick.bid - 4700.0
    expected_gap = TradingCore.calculate_dynamic_gap(profit)
    actual_gap = tick.bid - trail_sl if trail_sl else 0
    
    print(f"Entry Price: 4700.0")
    print(f"Current Price: {tick.bid}")
    print(f"Profit: {profit:.3f} points")
    print(f"Expected Gap: {expected_gap:.1f}")
    print(f"Trail Active: {active}")
    print(f"Trail SL: {trail_sl}")
    print(f"Actual Gap: {actual_gap:.1f}")
    
    if active and abs(actual_gap - expected_gap) < 0.01:
        print("\n[SUCCESS] DYNAMIC TRAILING STOP IS ACTIVE!")
        print(f"[SUCCESS] Using correct dynamic gap: {actual_gap:.1f}")
        return True
    else:
        print("\n[FAIL] DYNAMIC TRAILING STOP NOT WORKING")
        return False

if __name__ == "__main__":
    test_dynamic_trailing_active()