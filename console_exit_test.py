import MetaTrader5 as mt5
import time
from datetime import datetime

def test_exit_levels_console():
    """Console-only test to verify 1-point SL and trailing SL calculations"""
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        print("Make sure MetaTrader 5 is running and logged in")
        return
    
    symbol = "XAUUSD"
    
    print("🔴 EXIT LEVELS CONSOLE TEST")
    print("=" * 60)
    print("This test shows exit level calculations in console:")
    print("• Fixed 1-point stop loss (always active)")
    print("• Dynamic trailing stop (after 0.01pts profit)")
    print("• No chart needed - pure calculation test")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print()
    
    # Position tracking
    position_data = {}
    
    try:
        tick_count = 0
        while True:
            tick_count += 1
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                print("❌ No tick data available")
                time.sleep(2)
                continue
            
            # Get positions
            positions = mt5.positions_get(symbol=symbol)
            
            if positions:
                pos = positions[0]
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                ticket = pos.ticket
                
                # Initialize position data if new
                if ticket not in position_data:
                    position_data[ticket] = {
                        'entry_price': pos.price_open,
                        'reference_price': tick.bid if direction == "BUY" else tick.ask,
                        'trailing_sl': None,
                        'trailing_active': False
                    }
                    print(f"🆕 NEW POSITION DETECTED: {direction} #{ticket} at {pos.price_open:.2f}")
                
                pos_data = position_data[ticket]
                
                # CALCULATE 1-POINT STOP LOSS (ALWAYS ACTIVE)
                if direction == "BUY":
                    fixed_1pt_sl = pos.price_open - 1.0
                    current_price = tick.bid
                    distance_to_fixed_sl = current_price - fixed_1pt_sl
                else:
                    fixed_1pt_sl = pos.price_open + 1.0
                    current_price = tick.ask
                    distance_to_fixed_sl = fixed_1pt_sl - current_price
                
                # CALCULATE PROFIT FOR TRAILING SL
                reference_price = pos_data['reference_price']
                if direction == "BUY":
                    profit_points = tick.bid - reference_price
                else:
                    profit_points = reference_price - tick.ask
                
                # TRAILING SL LOGIC
                trailing_info = ""
                if profit_points >= 0.01:  # Activation threshold
                    # Calculate dynamic gap
                    if profit_points >= 3.0:
                        dynamic_gap = 0.4
                    elif profit_points >= 2.0:
                        dynamic_gap = 0.6
                    elif profit_points >= 1.0:
                        dynamic_gap = 0.8
                    else:
                        dynamic_gap = 1.0
                    
                    # Calculate new trailing SL
                    if direction == "BUY":
                        new_trailing_sl = tick.bid - dynamic_gap
                        # Ratcheting: only move up
                        if pos_data['trailing_sl'] is None or new_trailing_sl > pos_data['trailing_sl']:
                            pos_data['trailing_sl'] = new_trailing_sl
                    else:
                        new_trailing_sl = tick.ask + dynamic_gap
                        # Ratcheting: only move down
                        if pos_data['trailing_sl'] is None or new_trailing_sl < pos_data['trailing_sl']:
                            pos_data['trailing_sl'] = new_trailing_sl
                    
                    pos_data['trailing_active'] = True
                    trailing_sl = pos_data['trailing_sl']
                    
                    # Distance to trailing SL
                    if direction == "BUY":
                        distance_to_trailing_sl = tick.bid - trailing_sl
                    else:
                        distance_to_trailing_sl = trailing_sl - tick.ask
                    
                    trailing_info = f"| 🟠 Trailing SL: {trailing_sl:.2f} ({distance_to_trailing_sl:+.3f}pts, Gap:{dynamic_gap:.1f})"
                else:
                    needed_profit = 0.01 - profit_points
                    trailing_info = f"| ⏳ Trailing: Need {needed_profit:.3f}pts more"
                
                # STATUS OUTPUT
                status_icon = "✅" if distance_to_fixed_sl > 0 else "⚠️"
                print(f"[{tick_count:3d}] {direction} #{ticket} | Price: {current_price:.2f} | "
                      f"🔴 Fixed 1pt SL: {fixed_1pt_sl:.2f} ({distance_to_fixed_sl:+.3f}pts) {status_icon} | "
                      f"Profit: {profit_points:+.3f}pts {trailing_info}")
                
                # CHECK EXIT CONDITIONS
                exit_triggered = False
                exit_reason = ""
                
                # Check fixed 1pt SL
                if distance_to_fixed_sl <= 0:
                    exit_triggered = True
                    exit_reason = f"🔴 FIXED 1PT SL HIT: {current_price:.2f} hit {fixed_1pt_sl:.2f}"
                
                # Check trailing SL (if active)
                elif pos_data['trailing_active'] and pos_data['trailing_sl']:
                    trailing_sl = pos_data['trailing_sl']
                    if direction == "BUY" and tick.bid <= trailing_sl:
                        exit_triggered = True
                        exit_reason = f"🟠 TRAILING SL HIT: {tick.bid:.2f} hit {trailing_sl:.2f}"
                    elif direction == "SELL" and tick.ask >= trailing_sl:
                        exit_triggered = True
                        exit_reason = f"🟠 TRAILING SL HIT: {tick.ask:.2f} hit {trailing_sl:.2f}"
                
                if exit_triggered:
                    print(f"🚨 EXIT CONDITION TRIGGERED: {exit_reason}")
                    print("   (In real trading, position would be closed here)")
                
            else:
                # No positions
                print(f"[{tick_count:3d}] NO POSITION | Current Price: {tick.bid:.2f} | Waiting for entry...")
                position_data.clear()
            
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    test_exit_levels_console()