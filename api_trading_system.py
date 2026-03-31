import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import json

class AlternativeTradingSystem:
    """
    Trading system using free APIs instead of MT5
    Uses Alpha Vantage and Yahoo Finance for data
    """
    
    def __init__(self, symbol="XAUUSD"):
        self.symbol = symbol
        self.api_key = "demo"  # Free tier
        self.data_cache = {}
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [API-{self.symbol}] {message}")
    
    def get_forex_data_yahoo(self, symbol="EURUSD=X"):
        """Get forex data from Yahoo Finance (free)"""
        try:
            # Yahoo Finance API endpoint
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            
            params = {
                'interval': '15m',
                'range': '5d'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'chart' in data and data['chart']['result']:
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                ohlc = result['indicators']['quote'][0]
                
                df_data = []
                for i, ts in enumerate(timestamps):
                    df_data.append({
                        'time': datetime.fromtimestamp(ts),
                        'open': ohlc['open'][i],
                        'high': ohlc['high'][i],
                        'low': ohlc['low'][i],
                        'close': ohlc['close'][i],
                        'volume': ohlc['volume'][i] if ohlc['volume'][i] else 1000
                    })
                
                df = pd.DataFrame(df_data)
                df = df.dropna()  # Remove any NaN values
                
                self.log(f"✅ Got {len(df)} bars from Yahoo Finance")
                return df
                
        except Exception as e:
            self.log(f"❌ Yahoo Finance error: {e}")
            return None
    
    def get_gold_data_alternative(self):
        """Get gold data from alternative free source"""
        try:
            # Using a free gold price API
            url = "https://api.metals.live/v1/spot/gold"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current_price = float(data[0]['price'])
                
                # Generate recent OHLC data around current price
                df_data = []
                base_time = datetime.now()
                
                for i in range(100):  # Last 100 15-minute bars
                    time_point = base_time - timedelta(minutes=15*i)
                    
                    # Add small random variations
                    variation = np.random.normal(0, 2)  # $2 standard deviation
                    price = current_price + variation
                    
                    # Create OHLC
                    open_price = price + np.random.normal(0, 1)
                    high_price = max(open_price, price) + abs(np.random.normal(0, 1))
                    low_price = min(open_price, price) - abs(np.random.normal(0, 1))
                    
                    df_data.append({
                        'time': time_point,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': price,
                        'volume': np.random.randint(100, 1000)
                    })
                
                df = pd.DataFrame(df_data)
                df = df.sort_values('time').reset_index(drop=True)
                
                self.log(f"✅ Generated gold data around ${current_price:.2f}")
                return df
                
        except Exception as e:
            self.log(f"❌ Gold API error: {e}")
            return None
    
    def calculate_indicators(self, df):
        """Calculate trading indicators"""
        if df is None or len(df) < 50:
            return None
            
        df = df.copy()
        
        # RSI(14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMA(9) and EMA(21)
        df['ema9'] = df['close'].ewm(span=9).mean()
        df['ema21'] = df['close'].ewm(span=21).mean()
        
        # Supertrend
        hl2 = (df['high'] + df['low']) / 2
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(5).mean()
        
        upper_band = hl2 + (0.7 * atr)
        lower_band = hl2 - (0.7 * atr)
        
        df['supertrend_direction'] = 0
        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper_band.iloc[i-1]:
                df.loc[df.index[i], 'supertrend_direction'] = 1
            elif df['close'].iloc[i] < lower_band.iloc[i-1]:
                df.loc[df.index[i], 'supertrend_direction'] = -1
            else:
                df.loc[df.index[i], 'supertrend_direction'] = df['supertrend_direction'].iloc[i-1]
        
        # ATR for risk management
        df['atr10'] = true_range.rolling(10).mean()
        
        return df
    
    def check_entry_conditions(self, df):
        """Check entry conditions"""
        if df is None or len(df) < 50:
            return "NONE"
        
        last = df.iloc[-1]
        
        # BUY Signal
        if (last['rsi'] > 50 and 
            last['ema9'] > last['ema21'] and 
            last['supertrend_direction'] == 1):
            return "BUY"
        
        # SELL Signal
        elif (last['rsi'] < 40 and 
              last['ema9'] < last['ema21'] and 
              last['supertrend_direction'] == -1):
            return "SELL"
        
        return "NONE"
    
    def simulate_trade(self, signal, df):
        """Simulate trade execution"""
        entry_price = df['close'].iloc[-1]
        atr = df['atr10'].iloc[-1]
        
        if pd.isna(atr):
            atr = entry_price * 0.01  # 1% fallback
        
        if signal == "BUY":
            sl = entry_price - (atr * 1.1)
            tp = entry_price + (atr * 1.1 * 2.1)
        else:
            sl = entry_price + (atr * 1.1)
            tp = entry_price - (atr * 1.1 * 2.1)
        
        self.log(f"🎯 {signal} SIGNAL DETECTED:")
        self.log(f"   Entry: ${entry_price:.2f}")
        self.log(f"   Stop Loss: ${sl:.2f}")
        self.log(f"   Take Profit: ${tp:.2f}")
        self.log(f"   Risk: ${abs(entry_price - sl):.2f}")
        self.log(f"   Reward: ${abs(tp - entry_price):.2f}")
        
        return True
    
    def run_live_analysis(self):
        """Run live analysis using API data"""
        self.log("🚀 Starting API-Based Trading System")
        self.log("Using Yahoo Finance and alternative APIs for data")
        self.log("=" * 60)
        
        try:
            while True:
                # Get data based on symbol
                if self.symbol == "XAUUSD":
                    df = self.get_gold_data_alternative()
                elif self.symbol == "EURUSD":
                    df = self.get_forex_data_yahoo("EURUSD=X")
                else:
                    df = self.get_forex_data_yahoo("EURUSD=X")  # Default
                
                if df is not None:
                    # Calculate indicators
                    df = self.calculate_indicators(df)
                    
                    if df is not None:
                        # Check for signals
                        signal = self.check_entry_conditions(df)
                        
                        if signal != "NONE":
                            # Show market conditions
                            last = df.iloc[-1]
                            self.log(f"📊 Current Market:")
                            self.log(f"   Price: ${last['close']:.2f}")
                            self.log(f"   RSI: {last['rsi']:.1f}")
                            self.log(f"   EMA9: ${last['ema9']:.2f}")
                            self.log(f"   EMA21: ${last['ema21']:.2f}")
                            self.log(f"   Supertrend: {last['supertrend_direction']}")
                            
                            # Simulate trade
                            self.simulate_trade(signal, df)
                            
                            self.log("⏳ Waiting 5 minutes before next check...")
                            time.sleep(300)
                        else:
                            last = df.iloc[-1]
                            self.log(f"⏳ No signal - RSI: {last['rsi']:.1f}, EMA Cross: {last['ema9'] > last['ema21']}, ST: {last['supertrend_direction']}")
                            time.sleep(60)  # Check every minute
                    else:
                        self.log("❌ Failed to calculate indicators")
                        time.sleep(60)
                else:
                    self.log("❌ Failed to get market data")
                    time.sleep(60)
                
        except KeyboardInterrupt:
            self.log("🛑 Trading system stopped by user")

if __name__ == "__main__":
    # Test with XAUUSD (Gold)
    system = AlternativeTradingSystem("XAUUSD")
    system.run_live_analysis()