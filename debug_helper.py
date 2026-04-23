#!/usr/bin/env python3
"""
Debug version to identify why trailing stop isn't working in live trading
Add this to your check_exit_conditions method for debugging
"""

def debug_check_exit_conditions(self, tick, analysis):
    """Enhanced debug version of check_exit_conditions"""
    positions = mt5.positions_get(symbol=self.symbol)
    if not positions:
        return

    symbol_info = mt5.symbol_info(self.symbol)
    if not symbol_info:
        return

    for pos in positions:
        ticket = pos.ticket
        direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
        
        print(f"\n[DEBUG] === CHECKING POSITION #{ticket} ===")
        print(f"[DEBUG] Direction: {direction}")
        print(f"[DEBUG] Entry Price: {pos.price_open:.5f}")
        print(f"[DEBUG] Current Price: {tick.bid if direction == 'BUY' else tick.ask:.5f}")
        
        # Check if position data exists
        pos_data = self.position_data.get(ticket, {})
        if not pos_data:
            print(f"[DEBUG] ❌ CRITICAL: Position #{ticket} has NO stored data!")
            print(f"[DEBUG] Available tickets in position_data: {list(self.position_data.keys())}")
            print(f"[DEBUG] This is why trailing stop isn't working!")
            continue
        else:
            print(f"[DEBUG] ✅ Position data found")
            print(f"[DEBUG] Reference Price: {pos_data.get('reference_price', 'MISSING')}")
            print(f"[DEBUG] Trail Active: {pos_data.get('dollar_trail_active', 'MISSING')}")
        
        # Calculate current profit
        reference_price = pos_data.get('reference_price')
        if reference_price:
            if direction == "BUY":
                current_profit = tick.bid - reference_price
            else:
                current_profit = reference_price - tick.ask
            print(f"[DEBUG] Current Profit: {current_profit:.5f} points")
            print(f"[DEBUG] Threshold: 0.01000 points")
            print(f"[DEBUG] Should Activate: {current_profit >= 0.01}")
        else:
            print(f"[DEBUG] ❌ Reference price missing!")
        
        # Test trailing calculation
        try:
            dollar_trail_sl, trail_active, phase_label = TradingCore.calculate_trailing_stop_points(
                pos, tick, pos_data, symbol_info, 0.01, 1.0
            )
            
            print(f"[DEBUG] Trailing Result:")
            print(f"[DEBUG]   Active: {trail_active}")
            print(f"[DEBUG]   SL Level: {dollar_trail_sl}")
            print(f"[DEBUG]   Phase: {phase_label}")
            
            if trail_active and dollar_trail_sl:
                # Check exit condition
                should_exit = False
                if direction == "BUY" and tick.bid <= dollar_trail_sl:
                    should_exit = True
                    print(f"[DEBUG] 🚨 SHOULD EXIT: {tick.bid:.5f} <= {dollar_trail_sl:.5f}")
                elif direction == "SELL" and tick.ask >= dollar_trail_sl:
                    should_exit = True
                    print(f"[DEBUG] 🚨 SHOULD EXIT: {tick.ask:.5f} >= {dollar_trail_sl:.5f}")
                else:
                    print(f"[DEBUG] ✅ No exit needed yet")
                    
        except Exception as e:
            print(f"[DEBUG] ❌ ERROR in trailing calculation: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[DEBUG] === END POSITION #{ticket} ===\n")

# Instructions for use:
print("""
DEBUGGING INSTRUCTIONS:
======================

1. Replace your check_exit_conditions method with this debug version temporarily
2. Run the bot and enter a position
3. Watch the debug output to see:
   - If position data exists
   - If reference price is correct
   - If profit calculation works
   - If trailing activates
   - If exit conditions trigger

4. Look for these specific issues:
   - "Position has NO stored data" = Main problem
   - "Reference price missing" = Profit calculation broken
   - "ERROR in trailing calculation" = Exception in logic
   - "SHOULD EXIT" but position doesn't close = Exit execution problem

5. Common fixes:
   - Position data lost: Check if position_data dict is being cleared
   - Reference price wrong: Verify it's set to entry_price, not current tick
   - Trailing not activating: Check if profit >= 0.01 points
   - Exit not working: Check if close order is being sent properly
""")

if __name__ == "__main__":
    print("This is a debug helper script.")
    print("Copy the debug_check_exit_conditions function into your main bot file.")
    print("Replace check_exit_conditions temporarily to debug the issue.")