import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import traceback
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
import threading
from collections import deque
import os
from dotenv import load_dotenv

# --- Trading Bot Class ---
class TradingBot:
    def __init__(self, symbol, inputs, log_queue):
        self.symbol = symbol
        self.inputs = inputs
        self.log_queue = log_queue
        self.unique_magic = self.inputs['magic_number_base'] + sum(ord(c) for c in self.symbol)
        self.primary_tf = "M15"
        self.initialized = False
        self.timeframes = {
            "M1": mt5.TIMEFRAME_M1, 
            "M5": mt5.TIMEFRAME_M5, 
            "M15": mt5.TIMEFRAME_M15, 
            "H1": mt5.TIMEFRAME_H1, 
            "H4": mt5.TIMEFRAME_H4
        }
        self.rates = {tf: pd.DataFrame() for tf in self.timeframes}
        self.analysis = {}
        self.initialized = self.initialize_mt5()

    def log(self, message):
        log_msg = f"{datetime.now().strftime('%H:%M:%S')} | [{self.symbol}] {message}"
        self.log_queue.append(log_msg)
        print(log_msg)

    def initialize_mt5(self):
        try:
            if not mt5.symbol_select(self.symbol, True):
                self.log("Failed to select symbol.")
                return False

            self.symbol_info = mt5.symbol_info(self.symbol)
            if self.symbol_info:
                self.point = self.symbol_info.point
                self.digits = self.symbol_info.digits
                self.log("Initialized successfully.")
                return True
            else:
                self.log("Failed to get symbol info.")
                return False
        except Exception as e:
            self.log(f"Init error: {e}")
        return False

    def run_all_analysis(self):
        self.fetch_all_timeframes_data()
        self.analyze_ema_crossover(self.primary_tf)

    def fetch_all_timeframes_data(self):
        for tf_name, tf_const in self.timeframes.items():
            try:
                rates = mt5.copy_rates_from_pos(self.symbol, tf_const, 0, 300)
                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df.set_index('time', inplace=True)
                    df.rename(columns={
                        'open': 'Open', 'high': 'High', 
                        'low': 'Low', 'close': 'Close'
                    }, inplace=True)
                    self.rates[tf_name] = df
            except Exception:
                pass

    def analyze_ema_crossover(self, tf_name):
        rates = self.rates.get(tf_name)
        if rates is None or len(rates) < 22:
            return
        
        # Simple EMA calculation
        ema9 = rates['Close'].ewm(span=9).mean()
        ema21 = rates['Close'].ewm(span=21).mean()
        
        signal = 'NONE'
        if len(ema9) > 1 and len(ema21) > 1:
            if ema9.iloc[-2] < ema21.iloc[-2] and ema9.iloc[-1] > ema21.iloc[-1]:
                signal = 'EMA_BUY'
            elif ema9.iloc[-2] > ema21.iloc[-2] and ema9.iloc[-1] < ema21.iloc[-1]:
                signal = 'EMA_SELL'
        
        self.analysis['ema'] = {
            'ema9': ema9.iloc[-1] if len(ema9) > 0 else 0,
            'ema21': ema21.iloc[-1] if len(ema21) > 0 else 0,
            'signal': signal
        }

    def get_trade_signals(self):
        signals = []
        if self.analysis.get('ema', {}).get('signal') != 'NONE':
            signals.append(self.analysis['ema']['signal'])
        return signals

    def get_open_positions(self):
        try:
            pos = mt5.positions_get(symbol=self.symbol)
            return [p for p in pos if p.magic == self.unique_magic] if pos else []
        except Exception:
            return []

    def execute_trade(self, signal):
        direction = "BUY" if "BUY" in signal else "SELL"
        
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if not tick:
                self.log("Failed to get tick data")
                return

            price = tick.ask if direction == "BUY" else tick.bid
            
            # Simple stop loss calculation
            sl_distance = 0.001  # 10 pips for major pairs
            volume = self.inputs['min_volume']
            
            if direction == "BUY":
                sl = round(price - sl_distance, self.digits)
                tp = round(price + (sl_distance * 2), self.digits)
                order_type = mt5.ORDER_TYPE_BUY
            else:
                sl = round(price + sl_distance, self.digits)
                tp = round(price - (sl_distance * 2), self.digits)
                order_type = mt5.ORDER_TYPE_SELL

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "magic": self.unique_magic,
                "comment": signal[:31],
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log(f"✅ ORDER EXECUTED: {signal}")
            else:
                self.log(f"❌ ORDER FAILED: {result.comment if result else 'Unknown error'}")

        except Exception as e:
            self.log(f"❌ Error in execute_trade: {e}")

    def manage_open_positions(self):
        # Simple position management - just log open positions
        positions = self.get_open_positions()
        if positions:
            self.log(f"Managing {len(positions)} open positions")

# --- GUI Class ---
class TradingBotGUI(tk.Toplevel):
    def __init__(self, bots_dict, log_queue):
        super().__init__()
        self.bots_dict = bots_dict
        self.log_queue = log_queue
        self.title("Trading Dashboard")
        self.geometry("1200x800")
        self.is_running = True

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Log tab
        self.tab_log = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_log, text="Live Log")
        
        self.log_text = tk.Text(self.tab_log, wrap=tk.WORD, state='disabled', font=("Courier", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(1000, self.auto_refresh)

    def on_closing(self):
        self.is_running = False
        self.destroy()

    def auto_refresh(self):
        if self.is_running:
            self.update_log_tab()
            self.after(3000, self.auto_refresh)

    def update_log_tab(self):
        try:
            content = "\n".join(list(self.log_queue)[-100:])
            self.log_text.config(state='normal')
            self.log_text.delete('1.0', tk.END)
            self.log_text.insert('1.0', content)
            self.log_text.config(state='disabled')
        except Exception:
            pass

# --- Main Trading Thread ---
def trading_bot_thread(bots_dict, log_queue, gui):
    time.sleep(5)
    while gui.is_running:
        try:
            for symbol, bot in bots_dict.items():
                if not bot.initialized:
                    continue
                    
                bot.run_all_analysis()
                potential_signals = bot.get_trade_signals()
                
                if potential_signals:
                    signal = potential_signals[0]
                    if len(bot.get_open_positions()) < bot.inputs['max_concurrent_trades']:
                        bot.log(f"Executing trade: {signal}")
                        bot.execute_trade(signal)
                
                bot.manage_open_positions()
            
            time.sleep(10)
        except Exception:
            log_queue.append(f"CRITICAL ERROR:\n{traceback.format_exc()}")
            time.sleep(60)

def main():
    try:
        load_dotenv()
        mt5_login = os.getenv("MT5_LOGIN")
        mt5_pass = os.getenv("MT5_PASSWORD")
        mt5_server = os.getenv("MT5_SERVER")
        mt5_path = os.getenv("MT5_PATH")
        
        if not all([mt5_login, mt5_pass, mt5_server, mt5_path]):
            print("CRITICAL: .env file is missing variables.")
            return
            
        if not mt5.initialize():
            print("MT5.initialize() failed, error code =", mt5.last_error())
            return
            
        print("Global MT5 connection established.")

        common_inputs = {
            'magic_number_base': 123456,
            'max_concurrent_trades': 1,
            'min_volume': 0.01,
            'max_volume': 1.0
        }

        symbol_configs = {'XAUUSD': {}, 'EURUSD': {}}
        log_queue = deque(maxlen=200)
        bots_dict = {}

        for symbol in symbol_configs:
            bots_dict[symbol] = TradingBot(symbol, common_inputs, log_queue)

        root = tk.Tk()
        root.withdraw()
        gui = TradingBotGUI(bots_dict, log_queue)

        trader_thread = threading.Thread(
            target=trading_bot_thread, 
            args=(bots_dict, log_queue, gui), 
            daemon=True
        )
        trader_thread.start()

        gui.mainloop()
        mt5.shutdown()
        print("MT5 connection terminated.")
        
    except Exception as e:
        print(f"Main function error: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()