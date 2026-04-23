
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from indicators import TechnicalIndicators
from ema7_config import *

def diagnostic():
    load_dotenv()
    if not mt5.initialize(
        path=os.getenv("MT5_PATH"),
        login=int(os.getenv("MT5_LOGIN")),
        password=os.getenv("MT5_PASSWORD"),
        server=os.getenv("MT5_SERVER")
    ):
        print("MT5 Init Failed")
        return

    symbol = "XAUUSD"
    timeframe = mt5.TIMEFRAME_M1
    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
    if rates is None:
        print("Failed to get rates")
        return
        
    df = pd.DataFrame(rates)
    close = df['close']
    ema7 = TechnicalIndicators.calculate_ema7(close)
    rsi = TechnicalIndicators.calculate_rsi(close, 14)
    angle = TechnicalIndicators.calculate_ema7_angle(ema7, symbol)
    
    curr_price = close.iloc[-1]
    curr_open = df['open'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    prev_open = df['open'].iloc[-2]
    
    ema7_val = ema7.iloc[-1]
    rsi_val = rsi.iloc[-1]
    
    curr_color = "GREEN" if curr_price > curr_open else "RED"
    prev_color = "GREEN" if prev_close > prev_open else "RED"
    
    print(f"--- DIAGNOSTIC FOR {symbol} ---")
    print(f"Price: {curr_price:.2f} | EMA7: {ema7_val:.2f}")
    print(f"RSI: {rsi_val:.2f} (Threshold: >30 for BUY, <70 for SELL)")
    print(f"Angle: {angle:.2f}° (Threshold: >77° for BUY, <-77° for SELL)")
    print(f"Current Candle: {curr_color} | Prev Candle: {prev_color}")
    
    # Check BUY
    buy_angle = angle > EMA7_ANGLE_BUY_THRESHOLD
    buy_rsi = rsi_val > RSI_BUY_THRESHOLD
    buy_ema = curr_price > ema7_val
    buy_pa = (curr_color == "GREEN") or (curr_color == "RED" and prev_color == "RED")
    
    print("\nBUY CONDITIONS:")
    print(f"- Price > EMA7: {buy_ema}")
    print(f"- RSI > {RSI_BUY_THRESHOLD}: {buy_rsi}")
    print(f"- Angle > {EMA7_ANGLE_BUY_THRESHOLD}°: {buy_angle}")
    print(f"- Price Action: {buy_pa}")
    
    # Check SELL
    sell_angle = angle < EMA7_ANGLE_SELL_THRESHOLD
    sell_rsi = rsi_val < RSI_SELL_THRESHOLD
    sell_ema = curr_price < ema7_val
    sell_pa = (curr_color == "RED") or (curr_color == "GREEN" and prev_color == "GREEN")
    
    print("\nSELL CONDITIONS:")
    print(f"- Price < EMA7: {sell_ema}")
    print(f"- RSI < {RSI_SELL_THRESHOLD}: {sell_rsi}")
    print(f"- Angle < {EMA7_ANGLE_SELL_THRESHOLD}°: {sell_angle}")
    print(f"- Price Action: {sell_pa}")
    
    # Sideways check
    is_sideways = TechnicalIndicators.is_sideways_market(ema7.values)
    print(f"\nSideways Market: {is_sideways}")
    
    mt5.shutdown()

if __name__ == "__main__":
    diagnostic()
