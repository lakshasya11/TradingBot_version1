#!/usr/bin/env python3
"""
Test what happens when trailing stop is hit in live trading
"""
from trading_core import TradingCore
import MetaTrader5 as mt5

class MockPos:
    def __init__(self):
        self.ticket = 12345
        self.type = mt5.POSITION_TYPE_BUY
        self.price_open = 4700.00000
        self.volume = 0.01
        self.symbol = "XAUUSD"

class MockTick:
    def __init__(self, bid, ask):
        self.bid = bid
        self.ask = ask

class MockSymbol:
    def __init__(self):
        self.digits = 5

def simulate_live_trailing():
    print("SIMULATING: Live Trailing Stop Scenario")
    print("=" * 50)
    
    pos = MockPos()
    symbol_info = MockSymbol()
    pos_data = {'reference_price': 4700.00000}
    
    print("SCENARIO: BUY position at 4700.00")
    print("-" * 30)
    
    # Step 1: Price moves up, trailing activates
    print("\n[STEP 1] Price moves to 4701.50 (+1.5pts)")
    tick1 = MockTick(4701.50000, 4701.51000)
    trail_sl1, active1, label1 = TradingCore.calculate_trailing_stop_points(
        pos, tick1, pos_data, symbol_info, 0.01, 1.0
    )
    
    profit1 = tick1.bid - 4700.00000
    gap1 = TradingCore.calculate_dynamic_gap(profit1)
    
    print(f"  Profit: {profit1:.3f}pts")
    print(f"  Trail Active: {active1}")
    print(f"  Trail SL: {trail_sl1:.5f}")
    print(f"  Gap: {gap1:.1f} (dynamic)")
    print(f"  Status: Trailing is protecting {profit1 - gap1:.1f}pts profit")
    
    # Step 2: Price moves up more, trailing ratchets
    print("\n[STEP 2] Price moves to 4702.50 (+2.5pts)")
    tick2 = MockTick(4702.50000, 4702.51000)
    trail_sl2, active2, label2 = TradingCore.calculate_trailing_stop_points(
        pos, tick2, pos_data, symbol_info, 0.01, 1.0
    )
    
    profit2 = tick2.bid - 4700.00000
    gap2 = TradingCore.calculate_dynamic_gap(profit2)
    
    print(f"  Profit: {profit2:.3f}pts")
    print(f"  Trail Active: {active2}")
    print(f"  Trail SL: {trail_sl2:.5f}")
    print(f"  Gap: {gap2:.1f} (tightened!)")
    print(f"  Ratcheted: {trail_sl1:.5f} -> {trail_sl2:.5f}")
    print(f"  Status: Trailing is protecting {profit2 - gap2:.1f}pts profit")
    
    # Step 3: Price reverses and hits trailing stop
    print("\n[STEP 3] Price reverses to 4701.90 (hits trailing SL)")
    tick3 = MockTick(4701.90000, 4701.91000)
    
    # Check if trailing SL would be hit
    current_trail_sl = pos_data.get('dollar_trail_sl', trail_sl2)
    should_exit = tick3.bid <= current_trail_sl
    
    print(f"  Current Price: {tick3.bid:.5f}")
    print(f"  Trail SL Level: {current_trail_sl:.5f}")
    print(f"  Should Exit: {should_exit} ({tick3.bid:.5f} <= {current_trail_sl:.5f})")
    
    if should_exit:
        exit_profit = tick3.bid - 4700.00000
        print(f"  EXIT TRIGGERED!")
        print(f"  Exit Price: {tick3.bid:.5f}")
        print(f"  Final Profit: {exit_profit:.3f}pts")
        print(f"  Profit Protected: Trail saved {exit_profit:.1f}pts instead of losing more")
    
    print(f"\n" + "=" * 50)
    print("TRAILING STOP SUMMARY:")
    print(f"- Entry: 4700.00000")
    print(f"- Peak: 4702.50000 (+2.5pts)")
    print(f"- Exit: 4701.90000 (+1.9pts)")
    print(f"- Protected: 1.9pts profit vs potential loss")
    print(f"- Gap tightened: 1.0 -> 0.6 as profit increased")

if __name__ == "__main__":
    simulate_live_trailing()