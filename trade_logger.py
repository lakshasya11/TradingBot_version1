import csv
import os
from datetime import datetime

class TradeLogger:
    def __init__(self, log_file="trade_log.csv"):
        self.log_file = log_file
        self.setup_log_file()
    
    def setup_log_file(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'Timestamp', 'Signal', 'Price', 'RSI',
                    # 'EMA9', 'EMA21',  # commented out
                    'Trail_Stop', 'UT_Buy', 'UT_Sell',
                    'Step1', 'Step2', 'Step3', 'Step4', 'Final_Decision',
                    'Entry_Price', 'Stop_Loss', 'Take_Profit', 'Volume',
                    'Candle_Color', 'Breakout_Valid', 'Volume_Check',
                    'Acceleration_Check', 'Momentum_Check'
                ])
    
    def log_trade_decision(self, data):
        """Log trade decision to CSV"""
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data.get('signal', ''),
                data.get('price', 0),
                data.get('rsi', 0),
                # data.get('ema9', 0),   # commented out
                # data.get('ema21', 0),  # commented out
                data.get('trail_stop', 0),
                data.get('ut_buy', False),
                data.get('ut_sell', False),
                data.get('step1', False),
                data.get('step2', False),
                data.get('step3', False),
                data.get('step4', False),
                data.get('final_decision', ''),
                data.get('entry_price', 0),
                data.get('stop_loss', 0),
                data.get('take_profit', 0),
                data.get('volume', 0),
                data.get('candle_color', ''),
                data.get('breakout_valid', False),
                data.get('volume_check', False),
                data.get('acceleration_check', False),
                data.get('momentum_check', False)
            ])
    
    def get_stats(self):
        """Get basic statistics from log"""
        if not os.path.exists(self.log_file):
            return "No log file found"
        
        with open(self.log_file, 'r') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        if not rows:
            return "No data in log"
        
        total_signals = len(rows)
        execute_signals = len([r for r in rows if r['Final_Decision'] == 'EXECUTE'])
        buy_signals = len([r for r in rows if r['Signal'] == 'BUY'])
        sell_signals = len([r for r in rows if r['Signal'] == 'SELL'])
        
        return f"""
TRADE LOG STATISTICS:
Total Analyses: {total_signals}
Execute Signals: {execute_signals} ({execute_signals/total_signals*100:.1f}%)
BUY Signals: {buy_signals} ({buy_signals/total_signals*100:.1f}%)
SELL Signals: {sell_signals} ({sell_signals/total_signals*100:.1f}%)
        """