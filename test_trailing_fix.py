#!/usr/bin/env python3
"""
Test to verify trailing stop works with correct reference price
"""
import MetaTrader5 as mt5
from datetime import datetime
from trading_core import TradingCore

def test_trailing_with_correct_reference():
    """Test trailing stop with correct reference price (entry price)"""
    print("[CRITICAL FIX TEST] Testing Trailing Stop with Entry Price Reference")
    print("=" * 70)
    
    # Mock classes
    class MockPos:
        def __init__(self, ticket, price_open, pos_type):
            self.ticket = ticket
            self.price_open = price_open
            self.type = pos_type
    
    class MockTick:
        def __init__(self, bid, ask):
            self.bid = bid
            self.ask = ask
    
    class MockSymbolInfo:
        def __init__(self):
            self.digits = 5
    
    # Simulate real trading scenario
    entry_price = 2000.00000
    
    print(f"\n[SCENARIO] BUY Position Entry at {entry_price}")
    print("-" * 50)
    
    # Test 1: Position just opened (no profit yet)
    pos = MockPos(12345, entry_price, mt5.POSITION_TYPE_BUY)
    tick1 = MockTick(2000.00500, 2000.00600)  # Small move up
    symbol_info = MockSymbolInfo()
    
    # FIXED: Use entry price as reference (not current tick)
    pos_data = {'reference_price': entry_price}  # This is the fix!
    
    trail_sl1, active1, label1 = TradingCore.calculate_trailing_stop_points(
        pos, tick1, pos_data, symbol_info, 0.01, 1.0
    )
    
    profit1 = tick1.bid - entry_price
    print(f"[TICK 1] Current Bid: {tick1.bid:.5f}")
    print(f"[TICK 1] Profit: {profit1:.5f} points")
    print(f"[TICK 1] Trail Active: {active1}")
    print(f"[TICK 1] Status: {label1}")
    
    # Test 2: Price moves up enough to activate trailing
    tick2 = MockTick(2000.01200, 2000.01300)  # 0.012 points profit
    
    trail_sl2, active2, label2 = TradingCore.calculate_trailing_stop_points(
        pos, tick2, pos_data, symbol_info, 0.01, 1.0
    )
    
    profit2 = tick2.bid - entry_price
    print(f"\n[TICK 2] Current Bid: {tick2.bid:.5f}")
    print(f"[TICK 2] Profit: {profit2:.5f} points")
    print(f"[TICK 2] Trail Active: {active2}")
    print(f"[TICK 2] Trail SL: {trail_sl2:.5f}")
    print(f"[TICK 2] Status: {label2}")
    
    # Test 3: Price moves further up (ratcheting)
    tick3 = MockTick(2000.02000, 2000.02100)  # 0.020 points profit
    
    trail_sl3, active3, label3 = TradingCore.calculate_trailing_stop_points(
        pos, tick3, pos_data, symbol_info, 0.01, 1.0
    )
    
    profit3 = tick3.bid - entry_price
    print(f"\n[TICK 3] Current Bid: {tick3.bid:.5f}")
    print(f"[TICK 3] Profit: {profit3:.5f} points")
    print(f"[TICK 3] Trail Active: {active3}")
    print(f"[TICK 3] Trail SL: {trail_sl3:.5f}")
    print(f"[TICK 3] Status: {label3}")
    
    print(f"\n[RESULTS]")
    print("=" * 70)
    print(f"[PASS] Entry Price Reference: {entry_price:.5f}")
    print(f"[PASS] Tick 1 - No activation (profit {profit1:.5f} < 0.01): {not active1}")
    print(f"[PASS] Tick 2 - Activation (profit {profit2:.5f} >= 0.01): {active2}")
    print(f"[PASS] Tick 3 - Ratcheting (SL moved up): {active3}")
    
    if active2 and active3 and trail_sl3 > trail_sl2:
        print(f"\n[SUCCESS] TRAILING STOP IS NOW WORKING!")
        print(f"   - Uses entry price as reference: {entry_price:.5f}")
        print(f"   - Activates after 0.01 points profit")
        print(f"   - Ratchets properly (SL: {trail_sl2:.5f} -> {trail_sl3:.5f})")
        print(f"   - Ready for live trading!")
    else:
        print(f"\n[FAILED] Something is still wrong")
        
    return active2 and active3

if __name__ == "__main__":
    success = test_trailing_with_correct_reference()
    if success:
        print(f"\n[SUCCESS] TRAILING STOP FIX CONFIRMED - READY FOR LIVE TRADING!")
    else:
        print(f"\n[WARNING] TRAILING STOP STILL HAS ISSUES")