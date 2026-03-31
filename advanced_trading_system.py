import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
import time

class AdvancedTradingSystem:
    """
    Complete 4-Method Trading System:
    1) Entry Conditions with Multi-timeframe Analysis
    2) Entry Logic with Candle Structure Validation
    3) Entry Trading with Breakout Logic
    4) Order Placement with Market Depth Analysis
    """
    
    TIMEFRAMES = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30,
        'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1
    }
    
    def __init__(self, symbol: str, default_timeframe: str = 'M15'):
        self.symbol = symbol
        self.default_tf = default_timeframe
        self.tf_data: Dict[str, pd.DataFrame] = {}
        self.is_running = False
        
        # Trading Parameters
        self.rsi_period = 14
        self.ema_fast = 9
        self.ema_slow = 21
        self.st_period = 5
        self.st_multiplier = 0.7
        self.atr_period = 10
        self.atr_sl_multiplier = 1.1
        self.risk_reward_ratio = 2.1
        
    def log(self, message: str):
        """Enhanced logging with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{self.symbol}] {message}")
    
    # ==================== METHOD 1: ENTRY CONDITIONS ====================
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all required indicators"""
        df = df.copy()
        
        # RSI(14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMA(9) and EMA(21)
        df['ema9'] = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
        df['ema21'] = df['close'].ewm(span=self.ema_slow, adjust=False).mean()
        
        # Supertrend (period=5, multiplier=0.7)
        hl2 = (df['high'] + df['low']) / 2
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(self.st_period).mean()
        
        upper_band = hl2 + (self.st_multiplier * atr)
        lower_band = hl2 - (self.st_multiplier * atr)
        
        # Supertrend direction
        df['supertrend_direction'] = 0
        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper_band.iloc[i-1]:
                df.loc[df.index[i], 'supertrend_direction'] = 1
            elif df['close'].iloc[i] < lower_band.iloc[i-1]:
                df.loc[df.index[i], 'supertrend_direction'] = -1
            else:
                df.loc[df.index[i], 'supertrend_direction'] = df['supertrend_direction'].iloc[i-1]
        
        # ATR(10) for risk management
        df['atr10'] = true_range.rolling(self.atr_period).mean()
        
        return df
    
    def fetch_realtime_data(self):
        """Fetch real-time data for all timeframes"""
        self.log("Fetching real-time multi-timeframe data...")
        
        for tf_name, tf_value in self.TIMEFRAMES.items():
            try:
                rates = mt5.copy_rates_from_pos(self.symbol, tf_value, 0, 500)
                if rates is not None and len(rates) > 50:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df = self.calculate_indicators(df)
                    self.tf_data[tf_name] = df
                    self.log(f"✅ {tf_name} data loaded ({len(df)} bars)")
                else:
                    self.log(f"⚠️ Failed to load {tf_name} data")
            except Exception as e:
                self.log(f"❌ Error loading {tf_name}: {e}")
    
    def check_entry_conditions(self) -> str:
        """
        Check entry conditions with single timeframe concession capacity
        Returns: BUY, SELL, or NONE
        """
        if self.default_tf not in self.tf_data:
            return "NONE"
        
        df = self.tf_data[self.default_tf]
        if len(df) < 50:
            return "NONE"
        
        last = df.iloc[-1]
        
        # BUY Signal: RSI>50, EMA9>EMA21, Supertrend=1
        buy_conditions = (
            last['rsi'] > 50 and
            last['ema9'] > last['ema21'] and
            last['supertrend_direction'] == 1
        )
        
        # SELL Signal: RSI<40, EMA9<EMA21, Supertrend=-1
        sell_conditions = (
            last['rsi'] < 40 and
            last['ema9'] < last['ema21'] and
            last['supertrend_direction'] == -1
        )
        
        if buy_conditions:
            return "BUY"
        elif sell_conditions:
            return "SELL"
        else:
            return "NONE"
    
    # ==================== METHOD 2: ENTRY LOGIC ====================
    
    def validate_candle_structure(self, current_candle: Dict, current_price: float) -> Tuple[bool, str]:
        """
        Candle Structure Validation:
        - Strong green candle (price > open)
        - Minimum 0.3% body requirement
        - Price in top 60% of candle range
        """
        open_price = current_candle['open']
        high_price = current_candle['high']
        low_price = current_candle['low']
        
        # Must be green candle
        if current_price <= open_price:
            return False, "Not a green candle"
        
        # 0.3% body requirement
        body_percent = ((current_price - open_price) / open_price) * 100
        if body_percent < 0.3:
            return False, f"Body too small: {body_percent:.2f}%"
        
        # Price in top 60% of range
        candle_range = high_price - low_price
        price_position = (current_price - low_price) / candle_range
        if price_position < 0.6:
            return False, f"Price not in top 60%: {price_position:.1%}"
        
        return True, f"Valid structure: {body_percent:.2f}% body, {price_position:.1%} range"
    
    def validate_breakout_structure(self, current_candle: Dict, previous_candle: Dict) -> Tuple[bool, str]:
        """Validate breakout structure with previous candle"""
        prev_close = previous_candle['close']
        prev_open = previous_candle['open']
        curr_high = current_candle['high']
        
        # Check if previous candle was red or green
        prev_was_red = prev_close < prev_open
        
        if prev_was_red:
            # Break above previous high
            if curr_high > previous_candle['high']:
                return True, "Breakout above previous red candle high"
        else:
            # Break above previous close
            if curr_high > prev_close:
                return True, "Breakout above previous green candle close"
        
        return False, "No valid breakout structure"
    
    def validate_momentum(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Momentum validation - requires 2 out of 3 checks:
        1. Price actively rising
        2. Price accelerating
        3. Volume increasing (if available)
        """
        if len(df) < 5:
            return False, "Insufficient data for momentum"
        
        recent_closes = df['close'].tail(5)
        checks_passed = 0
        details = []
        
        # Check 1: Price actively rising
        if recent_closes.iloc[-1] > recent_closes.iloc[-3]:
            checks_passed += 1
            details.append("✅ Rising")
        else:
            details.append("❌ Not rising")
        
        # Check 2: Price accelerating
        recent_changes = recent_closes.diff().tail(3)
        if recent_changes.iloc[-1] > recent_changes.iloc[-2]:
            checks_passed += 1
            details.append("✅ Accelerating")
        else:
            details.append("❌ Not accelerating")
        
        # Check 3: ATR expansion (proxy for volume)
        recent_atr = df['atr10'].tail(3)
        if recent_atr.iloc[-1] > recent_atr.iloc[-2]:
            checks_passed += 1
            details.append("✅ ATR expanding")
        else:
            details.append("❌ ATR contracting")
        
        passed = checks_passed >= 2
        return passed, f"Momentum: {checks_passed}/3 - {', '.join(details)}"
    
    # ==================== METHOD 3: ENTRY TRADING ====================
    
    def check_breakout_logic(self, signal: str) -> Tuple[bool, str]:
        """
        Breakout Logic:
        - If previous candle red: break above previous high
        - If previous candle green: break above previous close
        - New candle conditions for entry timing
        """
        if self.default_tf not in self.tf_data:
            return False, "No data available"
        
        df = self.tf_data[self.default_tf]
        if len(df) < 2:
            return False, "Insufficient candle data"
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Get current price
        tick = mt5.symbol_info_tick(self.symbol)
        if not tick:
            return False, "No tick data"
        
        current_price = tick.bid if signal == "SELL" else tick.ask
        
        # Check breakout conditions
        prev_was_red = previous['close'] < previous['open']
        
        if signal == "BUY":
            if prev_was_red:
                # Break above previous high
                if current_price > previous['high']:
                    return True, f"BUY breakout above red candle high: {previous['high']:.5f}"
            else:
                # Break above previous close
                if current_price > previous['close']:
                    return True, f"BUY breakout above green candle close: {previous['close']:.5f}"
        
        elif signal == "SELL":
            if prev_was_red:
                # Break below previous low
                if current_price < previous['low']:
                    return True, f"SELL breakout below red candle low: {previous['low']:.5f}"
            else:
                # Break below previous close
                if current_price < previous['close']:
                    return True, f"SELL breakout below green candle close: {previous['close']:.5f}"
        
        return False, "No breakout condition met"
    
    # ==================== METHOD 4: ORDER PLACEMENT ====================
    
    def get_market_depth(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Get market depth for optimal order placement
        Returns: (best_bid_plus_tick, best_ask_plus_tick)
        """
        try:
            # Get symbol info for tick size
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                return None, None
            
            tick_size = symbol_info.point
            
            # Get current tick
            tick = mt5.symbol_info_tick(self.symbol)
            if not tick:
                return None, None
            
            # Calculate optimal prices (best + tick for better execution)
            optimal_buy_price = tick.ask + tick_size
            optimal_sell_price = tick.bid - tick_size
            
            return optimal_sell_price, optimal_buy_price
            
        except Exception as e:
            self.log(f"Error getting market depth: {e}")
            return None, None
    
    def calculate_risk_management(self, signal: str, entry_price: float) -> Tuple[float, float]:
        """
        ATR-based risk management:
        - Stop Loss: Entry ± ATR * 1.1
        - Take Profit: 2.1 risk-reward ratio
        """
        if self.default_tf not in self.tf_data:
            return 0, 0
        
        df = self.tf_data[self.default_tf]
        current_atr = df['atr10'].iloc[-1]
        
        # Stop loss calculation
        sl_distance = current_atr * self.atr_sl_multiplier
        
        if signal == "BUY":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + (sl_distance * self.risk_reward_ratio)
        else:  # SELL
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - (sl_distance * self.risk_reward_ratio)
        
        return stop_loss, take_profit
    
    def place_order(self, signal: str) -> bool:
        """
        Place order with optimal pricing and risk management
        """
        try:
            # Get optimal pricing from market depth
            optimal_sell, optimal_buy = self.get_market_depth()
            if not optimal_sell or not optimal_buy:
                self.log("Failed to get market depth")
                return False
            
            # Determine entry price
            entry_price = optimal_buy if signal == "BUY" else optimal_sell
            
            # Calculate risk management
            stop_loss, take_profit = self.calculate_risk_management(signal, entry_price)
            
            # Get symbol info for proper rounding
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                self.log("Failed to get symbol info")
                return False
            
            digits = symbol_info.digits
            stop_loss = round(stop_loss, digits)
            take_profit = round(take_profit, digits)
            entry_price = round(entry_price, digits)
            
            # Prepare order request
            order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": 0.01,
                "type": order_type,
                "price": entry_price,
                "sl": stop_loss,
                "tp": take_profit,
                "magic": 123456,
                "comment": f"4Method_{signal}",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Execute order
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                self.log(f"✅ ORDER EXECUTED: {signal}")
                self.log(f"   Entry: {entry_price} | SL: {stop_loss} | TP: {take_profit}")
                self.log(f"   Risk: {risk:.5f} | Reward: {reward:.5f} | RR: {reward/risk:.1f}")
                return True
            else:
                error_msg = result.comment if result else "Unknown error"
                self.log(f"❌ ORDER FAILED: {error_msg}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error placing order: {e}")
            return False
    
    # ==================== MAIN TRADING LOOP ====================
    
    def run_complete_analysis(self) -> bool:
        """
        Run complete 4-method analysis and execute trade if conditions met
        """
        self.log("=== Starting Complete 4-Method Analysis ===")
        
        # Method 1: Check entry conditions
        signal = self.check_entry_conditions()
        if signal == "NONE":
            self.log("❌ Method 1: No entry signal")
            return False
        
        self.log(f"✅ Method 1: {signal} signal detected")
        
        # Method 2: Validate entry logic
        if self.default_tf not in self.tf_data:
            self.log("❌ Method 2: No data for validation")
            return False
        
        df = self.tf_data[self.default_tf]
        current_candle = {
            'open': df.iloc[-1]['open'],
            'high': df.iloc[-1]['high'],
            'low': df.iloc[-1]['low'],
            'close': df.iloc[-1]['close']
        }
        
        tick = mt5.symbol_info_tick(self.symbol)
        if not tick:
            self.log("❌ Method 2: No tick data")
            return False
        
        current_price = tick.ask if signal == "BUY" else tick.bid
        
        # Candle structure validation
        candle_valid, candle_msg = self.validate_candle_structure(current_candle, current_price)
        if not candle_valid:
            self.log(f"❌ Method 2: Candle validation failed - {candle_msg}")
            return False
        
        self.log(f"✅ Method 2: Candle validation passed - {candle_msg}")
        
        # Momentum validation
        momentum_valid, momentum_msg = self.validate_momentum(df)
        if not momentum_valid:
            self.log(f"❌ Method 2: Momentum validation failed - {momentum_msg}")
            return False
        
        self.log(f"✅ Method 2: Momentum validation passed - {momentum_msg}")
        
        # Method 3: Check breakout logic
        breakout_valid, breakout_msg = self.check_breakout_logic(signal)
        if not breakout_valid:
            self.log(f"❌ Method 3: Breakout validation failed - {breakout_msg}")
            return False
        
        self.log(f"✅ Method 3: Breakout validation passed - {breakout_msg}")
        
        # Method 4: Place order
        order_success = self.place_order(signal)
        if not order_success:
            self.log("❌ Method 4: Order placement failed")
            return False
        
        self.log("✅ Method 4: Order placed successfully")
        self.log("=== Complete 4-Method Analysis SUCCESSFUL ===")
        return True
    
    def start_trading(self):
        """Start the complete trading system"""
        self.log("Starting Advanced 4-Method Trading System...")
        self.is_running = True
        
        try:
            while self.is_running:
                # Fetch real-time data
                self.fetch_realtime_data()
                
                # Run complete analysis
                trade_executed = self.run_complete_analysis()
                
                if trade_executed:
                    self.log("Trade executed - waiting 5 minutes before next analysis")
                    time.sleep(300)  # Wait 5 minutes after trade
                else:
                    self.log("No trade - waiting 30 seconds for next check")
                    time.sleep(30)  # Check every 30 seconds
                    
        except KeyboardInterrupt:
            self.log("Trading stopped by user")
        except Exception as e:
            self.log(f"Critical error: {e}")
        finally:
            self.is_running = False

def main():
    """Initialize and run the trading system"""
    # Initialize MT5 connection to already running MT5
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("✅ MT5 connected successfully")
    
    # Create and start trading system
    trading_system = AdvancedTradingSystem("XAUUSD", "M15")
    
    try:
        trading_system.start_trading()
    finally:
        mt5.shutdown()
        print("MT5 connection closed")

if __name__ == "__main__":
    main()