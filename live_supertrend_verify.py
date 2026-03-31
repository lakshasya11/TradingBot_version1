import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
from dotenv import load_dotenv

def calculate_supertrend_live(df, period=3, multiplier=0.5):
    """Live Supertrend calculation with corrected direction"""
    high = df['high']
    low = df['low'] 
    close = df['close']
    
    # Calculate True Range and ATR
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period, min_periods=period).mean()
    
    # Calculate basic bands
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Initialize final bands
    final_upper = upper_band.copy()
    final_lower = lower_band.copy()
    
    # Calculate final bands
    for i in range(1, len(df)):
        # Final upper band
        if upper_band.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1]:
            final_upper.iloc[i] = upper_band.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i-1]
            
        # Final lower band
        if lower_band.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1]:
            final_lower.iloc[i] = lower_band.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i-1]
    
    # Calculate Supertrend and direction
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    
    # Initialize
    supertrend.iloc[0] = final_lower.iloc[0]
    direction.iloc[0] = 1
    
    for i in range(1, len(df)):
        prev_direction = direction.iloc[i-1]
        
        if prev_direction == 1:  # Was bullish
            if close.iloc[i] < final_lower.iloc[i-1]:  # Price breaks below lower band
                supertrend.iloc[i] = final_upper.iloc[i]
                direction.iloc[i] = -1  # Turn bearish
            else:
                supertrend.iloc[i] = final_lower.iloc[i]
                direction.iloc[i] = 1  # Stay bullish
        else:  # Was bearish
            if close.iloc[i] > final_upper.iloc[i-1]:  # Price breaks above upper band
                supertrend.iloc[i] = final_lower.iloc[i]
                direction.iloc[i] = 1  # Turn bullish
            else:
                supertrend.iloc[i] = final_upper.iloc[i]
                direction.iloc[i] = -1  # Stay bearish
    
    return {
        'supertrend': supertrend,
        'direction': direction,
        'upper_band': final_upper,
        'lower_band': final_lower
    }

def live_verification():
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("🔴 LIVE SUPERTREND VERIFICATION")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        while True:
            # Fetch live data
            symbol = "XAUUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
            
            if rates is not None and len(rates) > 10:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
                # Calculate Supertrend
                st_result = calculate_supertrend_live(df)
                
                # Current values
                current_close = df['close'].iloc[-1]
                current_st = st_result['supertrend'].iloc[-1]
                current_dir = st_result['direction'].iloc[-1]
                current_upper = st_result['upper_band'].iloc[-1]
                current_lower = st_result['lower_band'].iloc[-1]
                
                # Get current time
                now = datetime.now().strftime("%H:%M:%S")
                
                # Clear screen and show status
                print(f"\r[{now}] Price: {current_close:.2f} | ST: {current_st:.2f} | Dir: {current_dir} | Upper: {current_upper:.2f} | Lower: {current_lower:.2f}", end="")
                
                # Show direction status
                if current_dir == 1:
                    status = "🟢 BULLISH"
                else:
                    status = "🔴 BEARISH"
                
                print(f" | {status}", end="", flush=True)
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nVerification stopped by user")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    live_verification()