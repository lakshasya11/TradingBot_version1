#!/usr/bin/env python3
"""
Debug script to trace trailing stop issues in live bot
"""
import MetaTrader5 as mt5
from datetime import datetime
from trading_core import TradingCore

def debug_trailing_stop_live():
    """Debug the actual trailing stop logic step by step"""
    print("[DEBUG] TRACING TRAILING STOP ISSUES")
    print("=" * 60)
    
    # Mock a real scenario that should activate trailing
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
    
    # Simulate a BUY position that should have trailing active
    entry_price = 2000.00000
    current_bid = 2000.05000  # 5 points profit (way above 0.01 threshold)
    
    pos = MockPos(12345, entry_price, mt5.POSITION_TYPE_BUY)
    tick = MockTick(current_bid, current_bid + 0.001)
    symbol_info = MockSymbolInfo()
    
    print(f"[SETUP] BUY Position:")
    print(f"  Entry Price: {entry_price:.5f}")
    print(f"  Current Bid: {current_bid:.5f}")
    print(f"  Expected Profit: {current_bid - entry_price:.5f} points")
    print(f"  Should Activate: {(current_bid - entry_price) >= 0.01}")
    
    # Test different reference price scenarios
    scenarios = [
        {"name": "Wrong Reference (Current Bid)", "ref_price": current_bid},
        {"name": "Correct Reference (Entry Price)", "ref_price": entry_price},
        {"name": "No Reference (None)", "ref_price": None}
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[SCENARIO {i}] {scenario['name']}")
        print("-" * 40)
        
        pos_data = {}
        if scenario['ref_price'] is not None:
            pos_data['reference_price'] = scenario['ref_price']
        
        try:
            trail_sl, active, label = TradingCore.calculate_trailing_stop_points(
                pos, tick, pos_data, symbol_info, 0.01, 1.0
            )
            
            ref_used = pos_data.get('reference_price', 'Not Set')
            if scenario['ref_price'] is None:
                profit = current_bid - ref_used if ref_used != 'Not Set' else 0
            else:
                profit = current_bid - scenario['ref_price']
            
            print(f"  Reference Used: {ref_used}")
            print(f"  Calculated Profit: {profit:.5f} points")
            print(f"  Trail Active: {active}")
            print(f"  Trail SL: {trail_sl}")
            print(f"  Status: {label}")
            
            if active:
                print(f"  [PASS] WORKING: Trailing activated!")
            else:
                print(f"  [FAIL] BROKEN: Trailing not activated")
                
        except Exception as e:
            print(f"  [ERROR] ERROR: {e}")
    
    # Test the actual bot's position data structure
    print(f"\n[BOT SIMULATION] Testing Bot's Position Data Structure")
    print("-" * 50)
    
    # Simulate how the bot creates position data
    signal = "BUY"
    tick_at_entry = MockTick(2000.00000, 2000.00100)  # Entry tick
    
    # OLD WAY (broken)
    old_pos_data = {
        'entry_price': entry_price,
        'reference_price': tick_at_entry.bid,  # This was the bug!
        'direction': signal
    }
    
    # NEW WAY (fixed)
    new_pos_data = {
        'entry_price': entry_price,
        'reference_price': entry_price,  # This is the fix!
        'direction': signal
    }
    
    current_tick = MockTick(2000.05000, 2000.05100)  # Much later tick
    
    print(f"Entry Tick Bid: {tick_at_entry.bid:.5f}")
    print(f"Current Tick Bid: {current_tick.bid:.5f}")
    print(f"Entry Price: {entry_price:.5f}")
    
    for method, data in [("OLD (Broken)", old_pos_data), ("NEW (Fixed)", new_pos_data)]:
        print(f"\n[{method}] Method:")
        
        trail_sl, active, label = TradingCore.calculate_trailing_stop_points(
            pos, current_tick, data.copy(), symbol_info, 0.01, 1.0
        )
        
        ref_price = data['reference_price']
        profit = current_tick.bid - ref_price
        
        print(f"  Reference Price: {ref_price:.5f}")
        print(f"  Current Bid: {current_tick.bid:.5f}")
        print(f"  Profit: {profit:.5f} points")
        print(f"  Trail Active: {active}")
        
        if active:
            print(f"  [PASS] SUCCESS: This method works!")
        else:
            print(f"  [FAIL] FAILED: This method is broken")

if __name__ == "__main__":
    debug_trailing_stop_live()