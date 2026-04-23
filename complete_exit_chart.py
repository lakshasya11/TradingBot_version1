import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime

def show_all_exit_levels():
    """Chart showing BOTH 1-point SL AND trailing SL levels"""
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return
    
    symbol = "XAUUSD"
    
    # Setup chart
    plt.ion()
    fig, ax = plt.subplots(figsize=(16, 10))
    plt.show()
    
    print("🔴 COMPLETE EXIT LEVELS CHART")
    print("=" * 70)
    print("This chart shows ALL exit conditions:")
    print("• Blue line = Price movement")
    print("• RED DOTTED LINE = Fixed 1-point stop loss (ALWAYS ACTIVE)")
    print("• ORANGE DOTTED LINE = Dynamic trailing stop (when active)")
    print("• Green/Red horizontal = Entry price")
    print("• Thick dashed lines = Active exit levels")
    print("=" * 70)
    print("Press Ctrl+C to stop")
    print()
    
    # Simulate position data for trailing SL calculation
    position_data = {}
    
    try:
        tick_count = 0
        while True:
            tick_count += 1
            
            # Get price data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
            if rates is None:
                print("❌ No price data available")
                time.sleep(2)
                continue
            
            df = pd.DataFrame(rates)
            current_price = df['close'].iloc[-1]
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                print("❌ No tick data available")
                time.sleep(2)
                continue
            
            # Get positions
            positions = mt5.positions_get(symbol=symbol)
            
            # Clear and plot
            ax.clear()
            
            # Plot price (blue line)
            x_range = range(len(df))
            price_array = df['close'].values
            ax.plot(x_range, price_array, 'b-', linewidth=2, label=f'Price: {current_price:.2f}', alpha=0.8)
            
            if positions:
                pos = positions[0]
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                ticket = pos.ticket
                
                # Initialize position data if new position
                if ticket not in position_data:
                    position_data[ticket] = {
                        'entry_price': pos.price_open,
                        'reference_price': tick.bid if direction == "BUY" else tick.ask,
                        'trailing_active': False,
                        'trailing_sl': None
                    }
                
                pos_data = position_data[ticket]
                
                # Calculate 1-POINT STOP LOSS (ALWAYS ACTIVE)\n                if direction == "BUY":
                    fixed_1pt_sl = pos.price_open - 1.0
                    current_distance_fixed = tick.bid - fixed_1pt_sl
                else:
                    fixed_1pt_sl = pos.price_open + 1.0
                    current_distance_fixed = fixed_1pt_sl - tick.ask
                
                # Calculate profit for trailing SL activation
                reference_price = pos_data['reference_price']
                if direction == "BUY":
                    profit_points = tick.bid - reference_price
                else:
                    profit_points = reference_price - tick.ask
                
                # TRAILING SL LOGIC (activates after 0.01 points profit)
                trailing_sl = None
                trailing_active = False
                
                if profit_points >= 0.01:  # 0.01 points profit threshold
                    trailing_active = True
                    
                    # Calculate dynamic gap based on profit
                    if profit_points >= 3.0:
                        dynamic_gap = 0.4
                    elif profit_points >= 2.0:
                        dynamic_gap = 0.6
                    elif profit_points >= 1.0:
                        dynamic_gap = 0.8
                    else:
                        dynamic_gap = 1.0
                    
                    # Calculate trailing SL
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
                    
                    trailing_sl = pos_data['trailing_sl']
                    pos_data['trailing_active'] = True
                
                # Create exit level arrays
                fixed_sl_array = [fixed_1pt_sl] * len(df)
                
                # Plot FIXED 1-POINT STOP LOSS (RED DOTTED LINE)
                ax.plot(x_range, fixed_sl_array, 'r:', linewidth=4, 
                       label=f'🔴 FIXED 1pt SL: {fixed_1pt_sl:.2f} (ALWAYS ACTIVE)', alpha=1.0)
                
                # Plot TRAILING STOP LOSS (ORANGE DOTTED LINE) if active
                if trailing_active and trailing_sl:
                    trailing_sl_array = [trailing_sl] * len(df)
                    ax.plot(x_range, trailing_sl_array, color='orange', linestyle=':', linewidth=4, 
                           label=f'🟠 TRAILING SL: {trailing_sl:.2f} (Gap: {dynamic_gap:.1f})', alpha=1.0)
                    
                    # Distance to trailing SL
                    if direction == "BUY":
                        distance_trailing = tick.bid - trailing_sl
                    else:
                        distance_trailing = trailing_sl - tick.ask
                else:
                    distance_trailing = None
                
                # Entry line
                entry_color = 'green' if direction == "BUY" else 'red'
                ax.axhline(y=pos.price_open, color=entry_color, linestyle='-', linewidth=2, alpha=0.7,
                          label=f'{direction} Entry: {pos.price_open:.2f}')
                
                # Current price line
                current_tick_price = tick.bid if direction == "BUY" else tick.ask
                ax.axhline(y=current_tick_price, color='blue', linestyle='-', linewidth=1, alpha=0.6,
                          label=f'Current {direction} Price: {current_tick_price:.2f}')
                
                # Exit level confirmation lines
                ax.axhline(y=fixed_1pt_sl, color='red', linestyle='--', linewidth=2, alpha=0.8,
                          label=f'Fixed SL Trigger: {fixed_1pt_sl:.2f}')
                
                if trailing_active and trailing_sl:
                    ax.axhline(y=trailing_sl, color='orange', linestyle='--', linewidth=2, alpha=0.8,
                              label=f'Trailing SL Trigger: {trailing_sl:.2f}')
                
                # Status output
                fixed_status = f"Fixed 1pt SL: {current_distance_fixed:+.3f}pts"
                if trailing_active and distance_trailing is not None:
                    trailing_status = f"Trailing SL: {distance_trailing:+.3f}pts"
                    print(f"[TICK {tick_count:3d}] {direction} | Profit: {profit_points:.3f}pts | {fixed_status} | {trailing_status}")
                else:
                    print(f"[TICK {tick_count:3d}] {direction} | Profit: {profit_points:.3f}pts | {fixed_status} | Trailing: Need {0.01-profit_points:.3f}pts more")
                
                chart_title = f'{symbol} - IN POSITION: RED=Fixed 1pt SL, ORANGE=Trailing SL'
                
                # Set y-axis range around position
                y_center = pos.price_open
                y_range = 3.0
                ax.set_ylim(y_center - y_range, y_center + y_range)
                
            else:
                # No position
                print(f"[TICK {tick_count:3d}] NO POSITION | Price: {current_price:.2f} | Waiting for entry...")
                chart_title = f'{symbol} - NO POSITION: Waiting for Entry'
                position_data.clear()  # Clear position data when no positions
            
            # Chart formatting
            ax.set_title(chart_title, fontsize=14, fontweight='bold')
            ax.legend(loc='upper left', fontsize=9)
            ax.grid(True, alpha=0.3)
            
            # Update display
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
        print("Chart window will close...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        mt5.shutdown()
        plt.close()

if __name__ == "__main__":
    show_all_exit_levels()