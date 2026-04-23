import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from indicators import TechnicalIndicators
from trading_core import TradingCore

def test_red_dotted_line():
    """Simple test to verify red dotted line shows ACTUAL exit levels"""
    
    # Initialize MT5
    if not mt5.initialize():
        print("MT5 initialization failed")
        return
    
    symbol = "XAUUSD"
    
    # Setup chart
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 8))
    plt.show()
    
    print("Testing RED DOTTED LINE = ACTUAL EXIT LEVELS")
    print("Chart window should be open. Press Ctrl+C to stop.")
    print("\nWhat you should see:")
    print("- NO POSITION: Red dotted line = EMA 7 trend")
    print("- IN POSITION: Red dotted line = ACTIVE exit level (1pt SL or Trailing SL)")
    print("\n" + "="*60 + "\n")
    
    try:
        tick_count = 0
        while True:
            tick_count += 1
            
            # Get data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
            if rates is None:
                print("No data available")
                time.sleep(1)
                continue
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calculate EMA 7
            ema7 = TechnicalIndicators.calculate_ema7(df['close'])
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                time.sleep(1)
                continue
            
            # Get positions
            positions = mt5.positions_get(symbol=symbol)
            
            # Create display array
            display_array = ema7.values.copy()
            line_label = "EMA 7 Trend"
            
            # Show ACTUAL exit levels when in position
            if positions:
                pos = positions[0]
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                
                # Fixed 1pt SL (always active)
                if direction == "BUY":
                    fixed_sl = pos.price_open - 1.0
                else:
                    fixed_sl = pos.price_open + 1.0
                
                # Override last 10 points to show exit level clearly
                display_array[-10:] = fixed_sl
                line_label = f"ACTIVE EXIT: Fixed 1pt SL ({fixed_sl:.2f})"
            
            # Clear and plot
            ax.clear()
            
            # Plot price (blue line)
            x_range = range(len(df))
            ax.plot(x_range, df['close'], 'b-', linewidth=1.5, label='Price')
            
            # Plot RED DOTTED LINE (EMA 7 or ACTIVE EXIT LEVEL)
            ax.plot(x_range, display_array, 'r:', linewidth=3, label=line_label, alpha=0.9)
            
            # Current price marker
            current_price = df['close'].iloc[-1]
            ax.axhline(y=current_price, color='blue', linestyle='-', alpha=0.7, 
                      label=f'Current Price: {current_price:.2f}')
            
            # Position markers
            if positions:
                pos = positions[0]
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                color = 'green' if pos.type == mt5.POSITION_TYPE_BUY else 'red'
                
                # Entry line
                ax.axhline(y=pos.price_open, color=color, linestyle='-', alpha=0.5,
                          label=f'{direction} Entry: {pos.price_open:.2f}')
                
                # Exit level line
                exit_level = display_array[-1]
                ax.axhline(y=exit_level, color='red', linestyle='--', linewidth=2, alpha=0.8,
                          label=f'EXIT LEVEL: {exit_level:.2f}')
                
                # Calculate distance to exit
                if direction == "BUY":
                    distance_to_exit = tick.bid - exit_level
                    status = f"BUY: {distance_to_exit:.3f}pts above exit"
                else:
                    distance_to_exit = exit_level - tick.ask
                    status = f"SELL: {distance_to_exit:.3f}pts above exit"
                
                print(f"[TICK {tick_count}] IN POSITION: {status} | Exit={exit_level:.2f}")
            else:
                ema7_current = ema7.iloc[-1]
                print(f"[TICK {tick_count}] NO POSITION: Price={current_price:.2f}, EMA7={ema7_current:.2f}")
            
            ax.set_title(f'{symbol} - RED DOTTED LINE = ACTUAL EXIT LEVEL TEST')
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            plt.draw()
            plt.pause(0.1)
            
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    finally:
        mt5.shutdown()
        plt.close()

if __name__ == "__main__":
    test_red_dotted_line()