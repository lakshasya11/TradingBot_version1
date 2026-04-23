//+------------------------------------------------------------------+
//|                                                Exit_Levels.mq5 |
//|        Shows 1pt SL, Trailing SL and 4pt TP for Trading Bot      |
//+------------------------------------------------------------------+
#property copyright "Trading Bot"
#property link      ""
#property version   "1.10"
#property indicator_chart_window
#property indicator_buffers 4
#property indicator_plots   4

//--- Plot Fixed 1pt SL
#property indicator_label1  "Fixed 1pt SL"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrRed
#property indicator_style1  STYLE_DOT
#property indicator_width1  2

//--- Plot Trailing SL
#property indicator_label2  "Trailing SL"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrOrange
#property indicator_style2  STYLE_DOT
#property indicator_width2  2

//--- Plot Take Profit
#property indicator_label3  "Take Profit"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrGreen
#property indicator_style3  STYLE_DOT
#property indicator_width3  2

//--- Plot EMA 7
#property indicator_label4  "EMA 7"
#property indicator_type4   DRAW_LINE
#property indicator_color4  clrDeepSkyBlue
#property indicator_style4  STYLE_SOLID
#property indicator_width4  1

//--- Input parameters
input int EMA_Period = 7;           // EMA Period
input double TrailingActivation = 0.01; // Trailing activation (points)

//--- Indicator buffers
double FixedSLBuffer[];
double TrailingSLBuffer[];
double TPBuffer[];
double EMA7Buffer[];

//--- Global variables
int ema_handle;

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
    //--- Set indicator buffers
    SetIndexBuffer(0, FixedSLBuffer, INDICATOR_DATA);
    SetIndexBuffer(1, TrailingSLBuffer, INDICATOR_DATA);
    SetIndexBuffer(2, TPBuffer, INDICATOR_DATA);
    SetIndexBuffer(3, EMA7Buffer, INDICATOR_DATA);
    
    //--- Create EMA handle
    ema_handle = iMA(_Symbol, _Period, EMA_Period, 0, MODE_EMA, PRICE_CLOSE);
    
    //--- Set indicator name
    IndicatorSetString(INDICATOR_SHORTNAME, "Bot Exit Levels");
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
    //--- Get EMA values
    if(CopyBuffer(ema_handle, 0, 0, rates_total, EMA7Buffer) <= 0)
        return 0;
    
    //--- Get current positions
    bool hasPosition = false;
    double entryPrice = 0;
    int positionType = -1;
    double currentPrice = close[rates_total-1];
    
    // Check for open positions for THIS symbol
    for(int i = 0; i < PositionsTotal(); i++)
    {
        ulong ticket = PositionGetTicket(i);
        if(PositionSelectByTicket(ticket))
        {
            if(PositionGetString(POSITION_SYMBOL) == _Symbol)
            {
                hasPosition = true;
                entryPrice = PositionGetDouble(POSITION_PRICE_OPEN);
                positionType = (int)PositionGetInteger(POSITION_TYPE);
                break;
            }
        }
    }
    
    //--- Calculate levels
    int start = (prev_calculated > 0) ? prev_calculated - 1 : 0;
    
    for(int i = start; i < rates_total; i++)
    {
        FixedSLBuffer[i] = EMPTY_VALUE;
        TrailingSLBuffer[i] = EMPTY_VALUE;
        TPBuffer[i] = EMPTY_VALUE;
        
        if(hasPosition)
        {
            // 1. Fixed SL and TP
            if(positionType == POSITION_TYPE_BUY)
            {
                FixedSLBuffer[i] = entryPrice - 1.0;
                TPBuffer[i] = entryPrice + 4.0;
                
                // 2. Trailing SL (using price at THIS bar)
                double barProfit = close[i] - entryPrice;
                if(barProfit >= TrailingActivation)
                {
                    double gap = 1.0;
                    if(barProfit >= 3.0) gap = 0.4;
                    else if(barProfit >= 2.0) gap = 0.6;
                    else if(barProfit >= 1.0) gap = 0.8;
                    
                    TrailingSLBuffer[i] = close[i] - gap;
                }
            }
            else // SELL
            {
                FixedSLBuffer[i] = entryPrice + 1.0;
                TPBuffer[i] = entryPrice - 4.0;
                
                // 2. Trailing SL
                double barProfit = entryPrice - close[i];
                if(barProfit >= TrailingActivation)
                {
                    double gap = 1.0;
                    if(barProfit >= 3.0) gap = 0.4;
                    else if(barProfit >= 2.0) gap = 0.6;
                    else if(barProfit >= 1.0) gap = 0.8;
                    
                    TrailingSLBuffer[i] = close[i] + gap;
                }
            }
        }
    }
    
    return rates_total;
}

//+------------------------------------------------------------------+
//| Cleanup function                                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    if(ema_handle != INVALID_HANDLE)
        IndicatorRelease(ema_handle);
}