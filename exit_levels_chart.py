import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime

def show_exit_levels_only():
    """Chart that ONLY shows 1-point SL and trailing SL exit levels"""
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return
    
    symbol = "XAUUSD"
    
    # Setup chart
    plt.ion()
    fig, ax = plt.subplots(figsize=(14, 10))
    plt.show()
    
    print("🔴 EXIT LEVELS CHART - RED DOTTED LINE TEST")
    print("=" * 60)
    print("This chart ONLY shows:")
    print("• Blue line = Price")
    print("• RED DOTTED LINE = Active exit level (1pt SL or Trailing SL)")
    print("• Green/Red horizontal = Entry price")
    print("• Red dashed = Exit level confirmation")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print()
    
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
            
            # Create exit level array
            price_array = df['close'].values
            exit_level_array = price_array.copy()  # Start with price as base
            
            # CRITICAL: Show ACTUAL exit levels
            if positions:
                pos = positions[0]
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                
                # Calculate 1-point stop loss
                if direction == "BUY":
                    fixed_1pt_sl = pos.price_open - 1.0
                    current_distance = tick.bid - fixed_1pt_sl
                else:
                    fixed_1pt_sl = pos.price_open + 1.0
                    current_distance = fixed_1pt_sl - tick.ask
                
                # Override ENTIRE red line with exit level for maximum visibility
                exit_level_array[:] = fixed_1pt_sl
                
                # Status
                if current_distance > 0:
                    status = f"✅ SAFE: {current_distance:.3f}pts above exit"
                else:
                    status = f"⚠️ DANGER: {abs(current_distance):.3f}pts below exit"
                
                print(f"[TICK {tick_count:3d}] {direction} POSITION | Entry: {pos.price_open:.2f} | 1pt SL: {fixed_1pt_sl:.2f} | {status}")
            else:
                # No position - show current price level
                exit_level_array[:] = current_price
                print(f"[TICK {tick_count:3d}] NO POSITION | Price: {current_price:.2f} | Waiting for entry...")
            
            # Clear and plot
            ax.clear()
            
            # Plot price (blue line)
            x_range = range(len(df))
            ax.plot(x_range, price_array, 'b-', linewidth=2, label=f'Price: {current_price:.2f}', alpha=0.8)
            
            # Plot EXIT LEVEL (RED DOTTED LINE) - THICK AND VISIBLE
            if positions:
                exit_level = exit_level_array[0]  # All points are the same
                ax.plot(x_range, exit_level_array, 'r:', linewidth=4, 
                       label=f'🔴 1-POINT STOP LOSS: {exit_level:.2f}', alpha=1.0)
                
                # Position markers
                pos = positions[0]
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                entry_color = 'green' if direction == "BUY" else 'red'
                
                # Entry line
                ax.axhline(y=pos.price_open, color=entry_color, linestyle='-', linewidth=2, alpha=0.7,
                          label=f'{direction} Entry: {pos.price_open:.2f}')
                
                # Exit level confirmation line
                ax.axhline(y=exit_level, color='red', linestyle='--', linewidth=3, alpha=0.9,
                          label=f'EXIT TRIGGER: {exit_level:.2f}')
                
                # Current price line
                current_tick_price = tick.bid if direction == "BUY" else tick.ask
                ax.axhline(y=current_tick_price, color='blue', linestyle='-', linewidth=1, alpha=0.6,
                          label=f'Current {direction} Price: {current_tick_price:.2f}')
                
                chart_title = f'{symbol} - IN POSITION: RED LINE = 1-POINT STOP LOSS EXIT'
            else:
                ax.plot(x_range, exit_level_array, 'r:', linewidth=2, 
                       label='🔴 No Exit Level (No Position)', alpha=0.5)
                chart_title = f'{symbol} - NO POSITION: Waiting for Entry'
            
            # Chart formatting
            ax.set_title(chart_title, fontsize=14, fontweight='bold')
            ax.legend(loc='upper left', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # Set y-axis range for better visibility
            if positions:
                pos = positions[0]
                y_center = pos.price_open
                y_range = 5.0  # Show ±5 points around entry
                ax.set_ylim(y_center - y_range, y_center + y_range)
            
            # Update display
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
        print("Chart window will close...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        mt5.shutdown()
        plt.close()

if __name__ == "__main__":
    show_exit_levels_only()