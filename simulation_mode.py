import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

class SimulatedTradingSystem:
    """
    Simulated version of the trading system for testing without MT5
    """
    
    def __init__(self, symbol="XAUUSD"):
        self.symbol = symbol
        self.current_price = 2650.0  # Starting price for XAUUSD
        self.is_running = False
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [SIM-{self.symbol}] {message}")
    
    def generate_realistic_data(self, bars=100):
        """Generate realistic OHLC data for testing"""
        np.random.seed(42)  # For consistent results
        
        # Generate price movements
        returns = np.random.normal(0, 0.001, bars)  # Small random movements
        prices = [self.current_price]
        
        for i in range(bars-1):
            new_price = prices[-1] * (1 + returns[i])
            prices.append(new_price)
        
        # Create OHLC data
        data = []
        for i, close in enumerate(prices):
            high = close * (1 + abs(np.random.normal(0, 0.0005)))
            low = close * (1 - abs(np.random.normal(0, 0.0005)))
            open_price = prices[i-1] if i > 0 else close
            
            data.append({
                'time': datetime.now() - timedelta(minutes=(bars-i)*15),
                'open': open_price,
                'high': max(open_price, high, close),
                'low': min(open_price, low, close),
                'close': close,
                'tick_volume': np.random.randint(100, 1000)
            })
        
        return pd.DataFrame(data)
    
    def calculate_indicators(self, df):
        """Same indicator calculation as real system"""
        df = df.copy()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMA
        df['ema9'] = df['close'].ewm(span=9).mean()
        df['ema21'] = df['close'].ewm(span=21).mean()
        
        # Simple Supertrend
        hl2 = (df['high'] + df['low']) / 2
        atr = (df['high'] - df['low']).rolling(5).mean()
        upper = hl2 + (0.7 * atr)
        lower = hl2 - (0.7 * atr)
        
        df['supertrend_direction'] = np.where(df['close'] > upper.shift(1), 1, 
                                            np.where(df['close'] < lower.shift(1), -1, 0))
        
        # ATR for risk management
        df['atr10'] = atr.rolling(10).mean()
        
        return df
    
    def check_entry_conditions(self, df):
        """Check entry conditions"""
        if len(df) < 50:
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
        
        if signal == "BUY":
            sl = entry_price - (atr * 1.1)
            tp = entry_price + (atr * 1.1 * 2.1)
        else:
            sl = entry_price + (atr * 1.1)
            tp = entry_price - (atr * 1.1 * 2.1)
        
        self.log(f"🎯 SIMULATED {signal} TRADE:")
        self.log(f"   Entry: {entry_price:.2f}")
        self.log(f"   Stop Loss: {sl:.2f}")
        self.log(f"   Take Profit: {tp:.2f}")
        self.log(f"   Risk: {abs(entry_price - sl):.2f}")
        self.log(f"   Reward: {abs(tp - entry_price):.2f}")
        
        return True
    
    def run_simulation(self):
        """Run the complete simulation"""
        self.log("🚀 Starting SIMULATION MODE")
        self.log("This simulates your trading system without MT5 connection")
        self.log("=" * 60)
        
        try:
            while True:
                # Generate new data
                df = self.generate_realistic_data(100)
                df = self.calculate_indicators(df)
                
                # Check for signals
                signal = self.check_entry_conditions(df)
                
                if signal != "NONE":
                    self.log(f"✅ Signal detected: {signal}")
                    
                    # Show current market conditions
                    last = df.iloc[-1]
                    self.log(f"📊 Market Data:")
                    self.log(f"   Price: {last['close']:.2f}")
                    self.log(f"   RSI: {last['rsi']:.1f}")
                    self.log(f"   EMA9: {last['ema9']:.2f}")
                    self.log(f"   EMA21: {last['ema21']:.2f}")
                    self.log(f"   Supertrend: {last['supertrend_direction']}")
                    
                    # Simulate trade
                    self.simulate_trade(signal, df)
                    
                    self.log("⏳ Waiting 30 seconds before next check...")
                    time.sleep(30)
                else:
                    self.log(f"⏳ No signal - Current conditions:")
                    last = df.iloc[-1]
                    self.log(f"   RSI: {last['rsi']:.1f}, EMA9>21: {last['ema9'] > last['ema21']}, ST: {last['supertrend_direction']}")
                    time.sleep(10)
                
        except KeyboardInterrupt:
            self.log("🛑 Simulation stopped by user")

if __name__ == "__main__":
    sim = SimulatedTradingSystem("XAUUSD")
    sim.run_simulation()