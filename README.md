# UT Bot Trading Strategy

An automated MetaTrader 5 trading bot using UT Bot ATR Trailing Stop, RSI, and candle color confirmation for forex and gold trading.

## Features

- **UT Bot ATR Trailing Stop**: Key_Value=2.0, ATR_Period=1 (single candle range) for dynamic trend detection
- **RSI Filter**: 14-period RSI (Wilder's smoothing) for momentum confirmation
- **Candle Color Confirmation**: Green/Red candle required to confirm entry direction
- **ATR-Based Stop Loss**: 1.5x ATR(20) or UT Trail — whichever is closer to entry price
- **Trailing Stop**: Activates after +1.0 points move, trails 1.0 points behind price
- **UT Trail Live Exit**: Position closed if price crosses back through the live UT trail

---

## How the Bot Works

The bot runs in a continuous loop (every 1 second) and performs the following on each cycle:

1. Fetches the latest OHLCV candle data from MT5 (M1 timeframe by default)
2. Calculates RSI(14), ATR(20), and UT Bot ATR Trailing Stop
3. Evaluates entry conditions against the latest candle
4. If a signal is found and no position is open, executes a market order
5. Monitors open positions and applies trailing stop + UT trail live exit logic

---

## Entry Conditions

### BUY Signal
All 3 conditions must be true:
- Price is **above** UT Bot trailing stop (`ut_buy = True`)
- RSI(14) **> 50**
- Current candle is **Green** (close > open)

### SELL Signal
All 3 conditions must be true:
- Price is **below** UT Bot trailing stop (`ut_sell = True`)
- RSI(14) **< 50**
- Current candle is **Red** (close < open)

> Only one position per symbol is allowed at a time.

---

## UT Bot ATR Trailing Stop Calculation

- ATR Period = 1 (single candle high-low range)
- Key Value = 2.0 (multiplier)
- `n_loss = 2.0 × |high - low|`
- Trail ratchets up in uptrend, down in downtrend
- `ut_buy` = price > trail | `ut_sell` = price < trail

---

## Exit Conditions

### Stop Loss
- Uses the **tighter** of:
  - ATR SL: `1.5 × ATR(20)` from entry price
  - UT Trail value at entry
- BUY: `max(entry - ATR_SL, ut_trail)` → higher value = closer to entry
- SELL: `min(entry + ATR_SL, ut_trail)` → lower value = closer to entry

### Take Profit
- Fixed at **10.0 points** distance from entry price
- BUY: `entry + 10.0 pts`
- SELL: `entry - 10.0 pts`

### Trailing Stop
- Activates after price moves **+1.0 points** from entry (bid-to-bid for BUY, ask-to-ask for SELL)
- Trails **1.0 points** behind the current price
- BUY: `current bid - 1.0 pts` (only moves up)
- SELL: `current ask + 1.0 pts` (only moves down)

### UT Trail Live Exit
- BUY position: closed if `tick.bid < live UT trail`
- SELL position: closed if `tick.ask > live UT trail`

### ATR SL Safety Net
- Manual price check as backup if broker SL fails
- BUY: closed if `tick.bid <= entry - (1.5 × ATR)`
- SELL: closed if `tick.ask >= entry + (1.5 × ATR)`

---

## Live Log Format

Each tick outputs a single compact line:
```
[HH:MM:SS.mmm] Tick#N | Price: X | UTTrail: X | RSI: X | Candle: GREEN/RED | UT_Buy: T/F | UT_Sell: T/F | Move: Xpts | Trail: ACTIVE/need Xmore | TrailSL: X | BrokerSL: X | Status: IN_TRADE/SIGNAL/WAITING
```

---

## Setup Instructions

### 1. Prerequisites
- MetaTrader 5 installed and running
- Python 3.8 or higher
- Active MT5 account

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file with your MT5 credentials:
```
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

### 4. Run the Bot
```bash
python enhanced_strategy.py
```

---

## Key Parameters (in `__init__`)

| Parameter | Value | Description |
|---|---|---|
| `atr_sl_multiplier` | 1.5 | ATR stop loss distance multiplier |
| `tp_points` | 10.0 | Take profit in points |
| `trailing_points` | 1.0 | Points move needed to activate trailing stop |
| `trailing_gap` | 1.0 | Points trail behind current price |

## UT Bot Parameters

| Parameter | Value | Description |
|---|---|---|
| `key_value` | 2.0 | UT Bot ATR multiplier |
| `atr_period` | 1 | ATR period (single candle range) |
| `rsi_period` | 14 | RSI calculation period |
| `atr_sl_period` | 20 | ATR period for stop loss calculation |

---

## File Structure

```
TradingBot_EMA_version-2/
├── enhanced_strategy.py        # Main bot (UT Bot + RSI + ATR strategy)
├── trade_backend/
│   ├── triple_strategy.py      # Multi-timeframe consensus strategy
│   ├── mt5_api_bridge.py       # MT5 API bridge
│   └── run_bot.py              # Bot runner
├── requirements.txt
├── .env                        # MT5 credentials (not committed)
└── README.md
```

## Trading Symbols

Configured for:
- **XAUUSD** (Gold)
- **EURUSD** (Euro/Dollar)

## Disclaimer

This bot is for educational and research purposes. Trading forex and CFDs involves significant risk. Always test on a demo account before live trading.
