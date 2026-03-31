//+------------------------------------------------------------------+
//|                                                   SuperTrend.mq5 |
//|                                  Copyright 2024, Your Trading Bot |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, Your Trading Bot"
#property link      "https://www.mql5.com"
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_plots   1

//--- plot SuperTrend
#property indicator_label1  "SuperTrend"
#property indicator_type1   DRAW_COLOR_LINE
#property indicator_color1  clrLime,clrRed
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

//--- input parameters
input int      ATR_Period = 10;        // ATR Period
input double   Multiplier = 3.0;       // ATR Multiplier

//--- indicator buffers
double SuperTrendBuffer[];
double ColorBuffer[];

//--- global variables
double atr[];

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   //--- indicator buffers mapping
   SetIndexBuffer(0, SuperTrendBuffer, INDICATOR_DATA);
   SetIndexBuffer(1, ColorBuffer, INDICATOR_COLOR_INDEX);
   
   //--- set indicator properties
   IndicatorSetString(INDICATOR_SHORTNAME, "SuperTrend(" + (string)ATR_Period + "," + DoubleToString(Multiplier, 1) + ")");
   IndicatorSetInteger(INDICATOR_DIGITS, _Digits);
   
   //--- initialize ATR array
   ArraySetAsSeries(atr, true);
   ArrayResize(atr, ATR_Period + 1);
   
   return(INIT_SUCCEEDED);
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
   //--- check for minimum bars
   if(rates_total < ATR_Period + 1)
      return(0);
      
   //--- set arrays as series
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(SuperTrendBuffer, true);
   ArraySetAsSeries(ColorBuffer, true);
   
   //--- calculate ATR
   for(int i = 0; i < rates_total - prev_calculated + 1 && i < rates_total - ATR_Period; i++)
   {
      double tr = MathMax(high[i] - low[i], MathMax(MathAbs(high[i] - close[i+1]), MathAbs(low[i] - close[i+1])));
      
      if(i == 0)
         atr[i] = tr;
      else
         atr[i] = (atr[i-1] * (ATR_Period - 1) + tr) / ATR_Period;
   }
   
   //--- calculate SuperTrend
   for(int i = rates_total - prev_calculated; i >= 0 && i < rates_total - ATR_Period; i--)
   {
      double hl2 = (high[i] + low[i]) / 2.0;
      double upperBand = hl2 + (Multiplier * atr[i]);
      double lowerBand = hl2 - (Multiplier * atr[i]);
      
      //--- determine trend
      if(close[i] <= lowerBand)
      {
         SuperTrendBuffer[i] = upperBand;
         ColorBuffer[i] = 1; // Red (downtrend)
      }
      else if(close[i] >= upperBand)
      {
         SuperTrendBuffer[i] = lowerBand;
         ColorBuffer[i] = 0; // Green (uptrend)
      }
      else
      {
         // Continue previous trend
         if(i < rates_total - 1)
         {
            SuperTrendBuffer[i] = SuperTrendBuffer[i+1];
            ColorBuffer[i] = ColorBuffer[i+1];
         }
         else
         {
            SuperTrendBuffer[i] = lowerBand;
            ColorBuffer[i] = 0;
         }
      }
   }
   
   return(rates_total);
}
//+------------------------------------------------------------------+