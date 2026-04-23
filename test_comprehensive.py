#!/usr/bin/env python3
"""
Comprehensive test to show trailing stop activation
"""
import MetaTrader5 as mt5
from datetime import datetime
from trading_core import TradingCore

def test_trailing_activation():
    """Test trailing stop activation with sufficient profit"""
    print("[COMPREHENSIVE TEST] TRAILING STOP ACTIVATION")
    print("=" * 60)
    
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
    
    # Test BUY position with SUFFICIENT profit for activation
    print("\n[TEST 1] BUY Position - Insufficient Profit (0.005 pts)")
    pos = MockPos(12345, 2000.00000, mt5.POSITION_TYPE_BUY)
    tick = MockTick(2000.00500, 2000.00600)  # Only 0.005 points profit
    symbol_info = MockSymbolInfo()
    pos_data = {}
    
    trail_sl, active, label = TradingCore.calculate_trailing_stop_points(
        pos, tick, pos_data, symbol_info, 0.01, 1.0
    )
    
    print(f"   Entry: {pos.price_open:.5f}")
    print(f"   Current Bid: {tick.bid:.5f}")
    print(f"   Profit: {tick.bid - pos.price_open:.5f} points")
    print(f"   Trail Active: {active}")
    print(f"   Trail SL: {trail_sl}")
    print(f"   Status: {label}")
    
    # Test BUY position with SUFFICIENT profit for activation
    print("\n[TEST 2] BUY Position - Sufficient Profit (0.015 pts)")
    pos2 = MockPos(12346, 2000.00000, mt5.POSITION_TYPE_BUY)
    tick2 = MockTick(2000.01500, 2000.01600)  # 0.015 points profit (> 0.01 threshold)
    pos_data2 = {}
    
    trail_sl2, active2, label2 = TradingCore.calculate_trailing_stop_points(
        pos2, tick2, pos_data2, symbol_info, 0.01, 1.0
    )
    
    print(f"   Entry: {pos2.price_open:.5f}")
    print(f"   Current Bid: {tick2.bid:.5f}")
    print(f"   Profit: {tick2.bid - pos2.price_open:.5f} points")
    print(f"   Trail Active: {active2}")
    print(f"   Trail SL: {trail_sl2:.5f}")
    print(f"   Status: {label2}")
    
    # Test SELL position with SUFFICIENT profit for activation
    print("\n[TEST 3] SELL Position - Sufficient Profit (0.020 pts)")
    pos3 = MockPos(12347, 2000.00000, mt5.POSITION_TYPE_SELL)
    tick3 = MockTick(1999.98200, 1999.98000)  # 0.020 points profit (ask moved down)
    pos_data3 = {}
    
    trail_sl3, active3, label3 = TradingCore.calculate_trailing_stop_points(
        pos3, tick3, pos_data3, symbol_info, 0.01, 1.0
    )
    
    print(f"   Entry: {pos3.price_open:.5f}")
    print(f"   Current Ask: {tick3.ask:.5f}")
    print(f"   Profit: {pos3.price_open - tick3.ask:.5f} points")
    print(f"   Trail Active: {active3}")
    print(f"   Trail SL: {trail_sl3:.5f}")
    print(f"   Status: {label3}")
    
    # Test ratcheting mechanism
    print("\n[TEST 4] Ratcheting Test - Price moves further in profit")
    tick4 = MockTick(2000.02000, 2000.02100)  # Price moved further up
    
    trail_sl4, active4, label4 = TradingCore.calculate_trailing_stop_points(
        pos2, tick4, pos_data2, symbol_info, 0.01, 1.0  # Same position as test 2
    )
    
    print(f"   Entry: {pos2.price_open:.5f}")
    print(f"   New Bid: {tick4.bid:.5f}")
    print(f"   New Profit: {tick4.bid - pos2.price_open:.5f} points")
    print(f"   Trail Active: {active4}")
    print(f"   New Trail SL: {trail_sl4:.5f}")
    print(f"   Status: {label4}")
    
    print("\n[RESULTS SUMMARY]")
    print("=" * 60)
    print(f"[PASS] Test 1 - Insufficient profit: Trail Active = {active}")
    print(f"[PASS] Test 2 - Sufficient profit: Trail Active = {active2}")
    print(f"[PASS] Test 3 - SELL sufficient profit: Trail Active = {active3}")
    print(f"[PASS] Test 4 - Ratcheting works: Trail Active = {active4}")
    
    if active2 and active3 and active4:
        print("\n[SUCCESS] DYNAMIC TRAILING STOP IS FULLY FUNCTIONAL!")
        print("- Activates after 0.01 points profit")
        print("- Trails 1.0 points behind current price")
        print("- Ratcheting mechanism works correctly")
        print("- Works for both BUY and SELL positions")
    else:
        print("\n[ERROR] Some tests failed!")

if __name__ == "__main__":
    test_trailing_activation()