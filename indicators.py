"""
Technical Indicators Module - Consolidated Calculations
Eliminates duplicate indicator code across strategy files
"""
import pandas as pd
import numpy as np
import math
import MetaTrader5 as mt5
# from ema7_config import EMA7_ANGLE_BUY_THRESHOLD, EMA7_ANGLE_SELL_THRESHOLD

class TechnicalIndicators:
    """Technical indicator calculations used across all strategies"""
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR using Wilder's smoothing (RMA)"""
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - df['close'].shift()).abs()
        tr3 = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1.0/period, adjust=False).mean()
        return atr

    @staticmethod
    def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI using Wilder's smoothing"""
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        alpha = 1.0 / period
        avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_ema(close: pd.Series, period: int) -> pd.Series:
        """Calculate EMA indicator"""
        return close.ewm(span=period, adjust=False).mean()

    # @staticmethod
    # def calculate_ema7(close: pd.Series) -> pd.Series:
    #     """Calculate EMA 7 specifically"""
    #     return close.ewm(span=7, adjust=False).mean()

    # @staticmethod
    # def calculate_ema7_angle(ema7_series: pd.Series, symbol: str) -> float:
    #     """Calculate live EMA 7 angle by blending current tick with candle EMA"""
    #     try:
    #         if len(ema7_series) < 2:
    #             return 0.0
    #             
    #         tick = mt5.symbol_info_tick(symbol)
    #         if not tick:
    #             return 0.0
    #             
    #         prev_ema7 = ema7_series.iloc[-2]
    #         last_ema7 = ema7_series.iloc[-1]
    #         
    #         # Debug: Check if values are valid
    #         if pd.isna(prev_ema7) or pd.isna(last_ema7) or prev_ema7 == 0:
    #             return 0.0
    #         
    #         # Blend tick price into EMA 7
    #         multiplier = 2 / (7 + 1)  # 0.25 for EMA 7
    #         curr_ema7 = (tick.bid * multiplier) + (last_ema7 * (1 - multiplier))
    #         
    #         # Calculate slope normalized by price - INCREASED FOR ±77° THRESHOLD
    #         slope = ((curr_ema7 - prev_ema7) / prev_ema7) * 200000  # Increased from 50000 to 200000 for ±77°
    #         
    #         # Convert to degrees
    #         ema7_angle = round(math.degrees(math.atan(slope)), 2)
    #         
    #         # TEMPORARY DEBUG: Check if we can reach ±77°
    #         # if abs(ema7_angle) > 70:  # Log when we get close to 77°
    #         #     print(f"[HIGH ANGLE] {ema7_angle:.2f}° | slope={slope:.6f}")
    #         
    #         return ema7_angle
    #         
    #     except Exception as e:
    #         print(f"[ERROR] Error calculating EMA7 angle: {e}")
    #         return 0.0

    @staticmethod
    def calculate_ut_trail(df: pd.DataFrame, key_value: float = 1.0) -> np.ndarray:
        """UT Bot ATR trailing stop calculation"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        n = len(close)
        
        # n_loss = key_value * |high - low|
        atr_1 = np.abs(high - low)
        trail = np.zeros(n)
        trail[0] = close[0]
        
        for i in range(1, n):
            n_loss = key_value * atr_1[i]
            prev_stop = trail[i - 1]
            prev_close = close[i - 1]
            
            if close[i] > prev_stop and prev_close > prev_stop:
                # Uptrend: trail moves up only
                trail[i] = max(prev_stop, close[i] - n_loss)
            elif close[i] < prev_stop and prev_close < prev_stop:
                # Downtrend: trail moves down only
                trail[i] = min(prev_stop, close[i] + n_loss)
            elif close[i] > prev_stop:
                # Initial uptrend
                trail[i] = close[i] - n_loss
            else:
                # Initial downtrend
                trail[i] = close[i] + n_loss
        
        return trail

    @staticmethod
    def is_sideways_market(trail_array, lookback: int = 10, threshold: float = 0.3) -> bool:
        """Detect sideways market based on trail range < threshold points over lookback candles"""
        if len(trail_array) < lookback:
            return False
        
        # Check trail range over last lookback candles
        recent_trail = trail_array[-lookback:]
        trail_range = max(recent_trail) - min(recent_trail)
        
        return trail_range < threshold  # Block if trail range < threshold points (sideways)

    @staticmethod
    def analyze_basic_timeframe(symbol: str, timeframe, bars: int = 100) -> dict:
        """Basic timeframe analysis with common indicators"""
        # Fetch data
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) < 50:
            return {}
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        close = df['close']
        
        # Calculate indicators
        rsi = TechnicalIndicators.calculate_rsi(close, 14)
        atr = TechnicalIndicators.calculate_atr(df, 20)
        # EMA 7 Calculations Commented Out
        # ema7 = TechnicalIndicators.calculate_ema7(close)
        
        # EMA 7 signals
        # ema7_buy = bool(close_current > ema7_current)
        # ema7_sell = bool(close_current < ema7_current)
        
        # EMA 7 angle
        # ema7_angle = TechnicalIndicators.calculate_ema7_angle(ema7, symbol)
        
        return {
            'rsi': rsi.iloc[-1] if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]) else 50,
            'atr': atr.iloc[-1] if len(atr) > 0 and not pd.isna(atr.iloc[-1]) else 0.01,
            'close': close.iloc[-1],
            'open': df['open'].iloc[-1],
            'low': df['low'].iloc[-1],
            'high': df['high'].iloc[-1],
            'candle_color': candle_color,
            # 'ema7_buy': ema7_buy,
            # 'ema7_sell': ema7_sell,
            # 'ema7_angle': ema7_angle,
            # 'ema7_value': ema7_current,
            'df': df
        }