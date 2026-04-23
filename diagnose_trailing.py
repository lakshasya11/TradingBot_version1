#!/usr/bin/env python3
"""
Diagnostic script to identify why trailing stop isn't working
"""
import MetaTrader5 as mt5
from trading_core import TradingCore

def diagnose_trailing_issues():
    print("DIAGNOSING: Why Trailing Stop Isn't Working")
    print("=" * 60)
    
    # Check 1: Position data structure
    print("\n[CHECK 1] Position Data Structure")
    print("-" * 40)
    
    # Simulate how the bot creates position data
    entry_price = 4700.00000
    signal = "BUY"
    
    # This is how the bot creates position data in execute_entry()
    unified_pos_data = {
        'entry_price': entry_price,
        'reference_price': entry_price,  # CRITICAL: This should be entry price
        'direction': signal,
        'dollar_trail_active': False,   # Starts in Phase 1
        'dollar_trail_sl': None,        # Set when 0.01pt profit reached
        'phase_label': 'Fixed 1pt SL',
    }
    
    print(f"[PASS] Position data structure looks correct:")
    print(f"   entry_price: {unified_pos_data['entry_price']}")
    print(f"   reference_price: {unified_pos_data['reference_price']}")
    print(f"   dollar_trail_active: {unified_pos_data['dollar_trail_active']}")
    
    # Check 2: Profit calculation
    print("\n[CHECK 2] Profit Calculation")
    print("-" * 40)
    
    class MockPos:
        def __init__(self):
            self.ticket = 12345
            self.type = mt5.POSITION_TYPE_BUY
            self.price_open = entry_price
    
    class MockTick:
        def __init__(self, bid):
            self.bid = bid
            self.ask = bid + 0.001
    
    class MockSymbol:
        def __init__(self):
            self.digits = 5
    
    pos = MockPos()
    symbol_info = MockSymbol()
    
    # Test different profit scenarios
    test_prices = [4700.005, 4700.01, 4700.05, 4701.0, 4702.0]
    
    for price in test_prices:
        tick = MockTick(price)
        pos_data_copy = unified_pos_data.copy()
        
        trail_sl, active, label = TradingCore.calculate_trailing_stop_points(
            pos, tick, pos_data_copy, symbol_info, 0.01, 1.0
        )
        
        profit = tick.bid - entry_price
        print(f"   Price: {price:.3f} | Profit: {profit:.3f}pts | Active: {active}")
        
        if active:
            gap = tick.bid - trail_sl
            print(f"      Trail SL: {trail_sl:.5f} | Gap: {gap:.1f}")
    
    # Check 3: Common Issues
    print("\n[CHECK 3] Common Issues That Prevent Trailing")
    print("-" * 50)
    
    issues = [
        "[ISSUE] Position data missing from self.position_data",
        "[ISSUE] Reference price not set correctly", 
        "[ISSUE] Fixed SL exits position before trailing activates",
        "[ISSUE] Opposite candle exit triggers first",
        "[ISSUE] Position data gets corrupted/overwritten",
        "[ISSUE] Exception in trailing calculation",
        "[ISSUE] Broker SL conflicts with internal tracking"
    ]
    
    for issue in issues:
        print(f"   {issue}")
    
    # Check 4: Debug what to look for in logs
    print("\n[CHECK 4] What to Look For in Live Logs")
    print("-" * 45)
    
    print("[PASS] GOOD SIGNS:")
    print("   [TRAIL DEBUG] BUY #12345: Bid=4700.015, Ref=4700.000, Profit=0.015pts, Active=True")
    print("   [TRAIL ACTIVATED] BUY #12345: Profit=0.015pts >= 0.01pts")
    print("   [TRAIL RATCHET] BUY #12345: SL moves UP 4699.015 -> 4699.025")
    print("   [TRAILING ACTIVE] BUY #12345: Internal SL=4699.025")
    
    print("\n[FAIL] BAD SIGNS:")
    print("   [WARNING] Position #12345 has no stored data - skipping trailing stop")
    print("   [ERROR] Trailing stop calculation failed for #12345")
    print("   [WAITING TRAIL] BUY #12345: Need +0.005pts for trail (Current: 0.005pts)")
    print("   [FIXED SL EXIT] Position exits before trailing activates")
    
    # Check 5: Recommended fixes
    print("\n[CHECK 5] Recommended Debugging Steps")
    print("-" * 45)
    
    print("1. Add more debug logging in check_exit_conditions()")
    print("2. Verify position data is not getting lost")
    print("3. Check if fixed SL is triggering too early")
    print("4. Monitor reference_price preservation")
    print("5. Ensure no exceptions in trailing calculation")
    
    print(f"\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Run the bot and watch for the log messages above")
    print("2. If you see 'Position has no stored data', that's the main issue")
    print("3. If trailing never activates, check profit calculation")
    print("4. If it activates but doesn't exit, check exit trigger logic")

if __name__ == "__main__":
    diagnose_trailing_issues()