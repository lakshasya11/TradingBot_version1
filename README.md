# ML-Enhanced Trading Bot

An advanced MetaTrader 5 trading bot with machine learning capabilities for automated forex and gold trading.

## Features

- **Smart Market Structure Analysis**: Break of Structure (BOS) and Change of Character (CHoCH) detection
- **Fibonacci Retracement Trading**: Automated 61.8% retracement level identification
- **EMA Crossover Signals**: 9 and 21 period exponential moving average analysis
- **Machine Learning Integration**: XGBoost, Random Forest, and SGD models for trade prediction
- **Incremental Learning**: Models adapt and improve from live trading results
- **Risk Management**: Dynamic volume calculation based on ATR and account risk
- **Correlation Filtering**: Prevents conflicting trades on correlated pairs
- **Real-time GUI Dashboard**: Live monitoring of trades, ML predictions, and market analysis

## Setup Instructions

### 1. Prerequisites
- MetaTrader 5 installed and running
- Python 3.8 or higher
- Active MT5 demo/live account

### 2. Installation
```bash
# Install required packages
pip install -r requirements.txt
```

### 3. Configuration
The `.env` file contains your MT5 connection details:
```
MT5_LOGIN=213711922
MT5_PASSWORD=j6t#UeuH
MT5_SERVER=OctaFX-Demo
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

### 4. Verification
Run the test script to verify everything is working:
```bash
python test_setup.py
```

### 5. Starting the Bot

#### Option 1: Command Line
```bash
python trading_bot.py
```

#### Option 2: Windows Batch File
Double-click `start_trading_bot.bat`

## Trading Strategy

### Signal Generation
1. **EMA Crossover**: 9 EMA crossing above/below 21 EMA
2. **BOS Retest**: Price retesting previous Break of Structure levels
3. **Fibonacci 61.8%**: Price approaching key retracement levels
4. **ML Predictions**: High-confidence machine learning signals

### Risk Management
- **Dynamic Volume**: Calculated based on ATR and risk per trade ($20 USD)
- **Stop Loss**: 1.2x ATR distance from entry
- **Take Profit**: 1.5x risk-reward ratio
- **Trailing Stop**: 2.0x ATR trailing distance
- **Max Concurrent Trades**: 1 per symbol

### Machine Learning Features
- **60+ Technical Indicators**: Price action, momentum, volatility, and trend features
- **Multi-timeframe Analysis**: M5 base with H1 trend confirmation
- **Ensemble Modeling**: Combines Random Forest, XGBoost, and SGD predictions
- **Confidence Scoring**: Only trades high-confidence ML signals (>75%)
- **Incremental Learning**: Models update with live trading results

## GUI Dashboard

The trading bot includes a comprehensive GUI with 4 tabs:

1. **Market Analysis**: Live SMC analysis, Fibonacci levels, EMA signals
2. **Trade Info**: Open positions, P&L, trade history
3. **ML Status**: Model performance, predictions, ensemble weights
4. **Live Log**: Real-time bot activity and error messages

## File Structure

```
metatraders5/
├── trading_bot.py          # Main trading bot application
├── app.py                  # Flask web API (separate service)
├── test_setup.py           # Setup verification script
├── start_trading_bot.bat   # Windows startup script
├── requirements.txt        # Python dependencies
├── .env                    # MT5 connection configuration
├── README.md              # This file
├── historical_data/       # ML training data (created automatically)
└── models/                # Trained ML models (created automatically)
```

## Trading Symbols

Currently configured for:
- **XAUUSD** (Gold)
- **EURUSD** (Euro/Dollar)

Additional symbols can be added in the `symbol_configs` dictionary in `main()`.

## ML Model Training

### Initial Training
1. Click "Train ML Models" in the GUI
2. Bot will collect 3+ years of historical data
3. Feature engineering creates 60+ technical indicators
4. Models train on historical patterns
5. Training takes 5-15 minutes depending on data size

### Incremental Learning
- Models automatically update with live trading results
- SGD models update every 100 new data points
- Tree-based models retrain every 500 samples
- Ensemble weights adjust based on recent performance

## Safety Features

- **Connection Monitoring**: Automatic MT5 connection verification
- **Error Handling**: Comprehensive error catching and logging
- **Volume Validation**: Broker limit compliance
- **Stop Level Checking**: Minimum distance requirements
- **Market Hours**: Trading only when markets are open
- **Correlation Filtering**: Prevents over-exposure to correlated pairs

## Troubleshooting

### Common Issues

1. **MT5 Connection Failed**
   - Ensure MetaTrader 5 is running
   - Check login credentials in `.env`
   - Verify MT5 path is correct

2. **Import Errors**
   - Run: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

3. **No Trading Signals**
   - Markets may be ranging (no clear trends)
   - Check if ML models are trained
   - Verify symbol availability in MT5

4. **Order Execution Failed**
   - Check account balance and margin
   - Verify symbol trading is enabled
   - Check market hours

### Log Analysis
- All activities are logged in the GUI "Live Log" tab
- Error messages include detailed troubleshooting information
- Check MT5 terminal for additional error details

## Performance Monitoring

### Key Metrics
- **Win Rate**: Percentage of profitable trades
- **Risk-Reward Ratio**: Average profit vs average loss
- **ML Confidence**: Model prediction accuracy
- **Drawdown**: Maximum account equity decline

### Optimization
- Monitor ML model performance in GUI
- Adjust risk parameters in `common_inputs`
- Fine-tune signal confirmation requirements
- Review correlation filtering effectiveness

## Disclaimer

This trading bot is for educational and research purposes. Trading forex and CFDs involves significant risk and may not be suitable for all investors. Past performance does not guarantee future results. Always test thoroughly on demo accounts before live trading.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review log messages in the GUI
3. Run `test_setup.py` to verify configuration
4. Ensure all dependencies are installed correctly