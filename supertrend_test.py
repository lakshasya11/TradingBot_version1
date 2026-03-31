import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os

def calculate_supertrend_proper(df, period=5, multiplier=0.7):
    """Proper Supertrend calculation with debugging"""
    
    # Calculate True Range and ATR
    high = df['high']
    low = df['low'] 
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # Calculate basic bands
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Initialize final bands
    final_upper_band = upper_band.copy()
    final_lower_band = lower_band.copy()
    
    # Calculate final bands
    for i in range(1, len(df)):
        # Final upper band
        if upper_band.iloc[i] < final_upper_band.iloc[i-1] or close.iloc[i-1] > final_upper_band.iloc[i-1]:
            final_upper_band.iloc[i] = upper_band.iloc[i]
        else:
            final_upper_band.iloc[i] = final_upper_band.iloc[i-1]
            
        # Final lower band
        if lower_band.iloc[i] > final_lower_band.iloc[i-1] or close.iloc[i-1] < final_lower_band.iloc[i-1]:
            final_lower_band.iloc[i] = lower_band.iloc[i]
        else:
            final_lower_band.iloc[i] = final_lower_band.iloc[i-1]
    
    # Calculate Supertrend
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    
    # Initialize
    supertrend.iloc[0] = final_upper_band.iloc[0]
    direction.iloc[0] = -1
    
    for i in range(1, len(df)):
        prev_supertrend = supertrend.iloc[i-1]
        prev_direction = direction.iloc[i-1]
        
        if prev_direction == -1:  # Was bearish
            if close.iloc[i] > final_upper_band.iloc[i]:
                supertrend.iloc[i] = final_lower_band.iloc[i]
                direction.iloc[i] = 1  # Turn bullish
            else:
                supertrend.iloc[i] = final_upper_band.iloc[i]
                direction.iloc[i] = -1  # Stay bearish
        else:  # Was bullish
            if close.iloc[i] < final_lower_band.iloc[i]:
                supertrend.iloc[i] = final_upper_band.iloc[i]
                direction.iloc[i] = -1  # Turn bearish
            else:
                supertrend.iloc[i] = final_lower_band.iloc[i]
                direction.iloc[i] = 1  # Stay bullish
    
    return {
        'supertrend': supertrend,
        'direction': direction,
        'upper_band': final_upper_band,
        'lower_band': final_lower_band,
        'atr': atr
    }

def test_supertrend():
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    # Fetch data
    symbol = "XAUUSD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    
    if rates is not None:
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Calculate Supertrend
        st_result = calculate_supertrend_proper(df, period=5, multiplier=0.7)
        
        # Show last 10 values for verification
        print("SUPERTREND VERIFICATION:")
        print("=" * 80)
        print(f"{'Time':<20} {'Close':<10} {'ST':<10} {'Dir':<5} {'Upper':<10} {'Lower':<10}")
        print("=" * 80)
        
        for i in range(-10, 0):
            time_str = df['time'].iloc[i].strftime('%H:%M:%S')
            close_val = df['close'].iloc[i]
            st_val = st_result['supertrend'].iloc[i]
            dir_val = st_result['direction'].iloc[i]
            upper_val = st_result['upper_band'].iloc[i]
            lower_val = st_result['lower_band'].iloc[i]
            
            print(f"{time_str:<20} {close_val:<10.2f} {st_val:<10.2f} {dir_val:<5} {upper_val:<10.2f} {lower_val:<10.2f}")
        
        # Current values
        current_close = df['close'].iloc[-1]
        current_st = st_result['supertrend'].iloc[-1]
        current_dir = st_result['direction'].iloc[-1]
        
        print("=" * 80)
        print(f"CURRENT STATUS:")
        print(f"Close Price: {current_close:.2f}")
        print(f"Supertrend: {current_st:.2f}")
        print(f"Direction: {current_dir} ({'BULLISH' if current_dir == 1 else 'BEARISH'})")
        
        if current_dir == 1:
            print(f"✅ Price {current_close:.2f} is ABOVE Supertrend {current_st:.2f} = BULLISH")
        else:
            print(f"❌ Price {current_close:.2f} is BELOW Supertrend {current_st:.2f} = BEARISH")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_supertrend()