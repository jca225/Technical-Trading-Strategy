import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import talib

class SwingIndex:

    '''
    The purpose of this class is to provide a scope for all variables relevant to the Swing Index System.
    '''
    def __init__(self, symbols: list, c1=.5, c2=.25, c3=.5, c4=.25, c5=.25, c6=3, c7=50, adxr_sell_threshold=20, adxr_buy_threshold=20):
        self.__symbols = symbols
        self.__c1 = c1
        self.__c2 = c2
        self.__c3 = c3
        self.__c4 = c4
        self.__c5 = c5
        self.__c6 = c6
        self.__c7 = c7
        self.__adxr_buy_threshold = adxr_buy_threshold
        self.__adxr_sell_threshold = adxr_sell_threshold

    def __calculate_asi(self, high:pd.Series, low:pd.Series, close:pd.Series, open:pd.Series) -> pd.Series:
        '''
        This method calculates the accumulative swing index (ASI). 
        Parameters:
        - high: high price points
        - low: low price points
        - close: close price points
        - open: open price points
        Returns:
        - accumulative swing index, as described in New Concepts in Technical Trading Systems
        '''
        # length of series
        N = len(high)


        # constants (These will be optimized in a future project!)
        c_1 = self.__c1
        c_2 = self.__c2
        c_3 = self.__c3
        c_4 = self.__c4
        c_5 = self.__c5
        limit = self.__c6
        
        '''
        `np.roll()` can be quite counter-intuitive, so I included an example of it below:
        Example of np.roll():
            x = np.arange(10)
            np.roll(x, 2)
            array([8, 9, 0, 1, 2, 3, 4, 5, 6, 7])
            np.roll(x, -2)
            array([2, 3, 4, 5, 6, 7, 8, 9, 0, 1])
        '''
 
        previous_high = np.roll(high, 1, 0)
        previous_high[0] = np.NaN

        previous_close = np.roll(close, 1, 0)
        previous_close[0] = np.NaN

        previous_low = np.roll(low, 1, 0)
        previous_low[0] = np.NaN

        previous_open = np.roll(open, 1, 0)
        previous_open[0] = np.NaN

        # conditions for determining "R" (i.e., R is the largest of the following)
        l_one = abs(high - previous_close)
        l_two = abs(low - previous_close)
        l_three = abs(high - low)

        # R can take on three conditional values:
        R = np.zeros_like(l_one)  # Initialize 'r_1' array with zeros with the same shape as the given array

        for i in range(N):
            if l_one.iloc[i] == max(l_one.iloc[i], l_two.iloc[i], l_three.iloc[i]):
                R[i] = (l_one.iloc[i]) - (c_3 * abs(low.iloc[i] - previous_close[i])) + (c_4 * abs(previous_close[i] - previous_open[i]))
                continue
            
            elif l_two.iloc[i] == max(l_one.iloc[i], l_two.iloc[i], l_three.iloc[i]):
                R[i] =  (l_two.iloc[i]) - (c_3 * abs(high.iloc[i] - previous_close[i])) + (c_4 * abs(previous_close[i] - previous_open[i]))
                continue

            elif l_three.iloc[i] == max(l_one.iloc[i], l_two.iloc[i], l_three.iloc[i]):
                R[i] = (l_three.iloc[i]) + (c_5 * abs(previous_close[i] - previous_open[i]))
                continue

        # requires previous day's value
        R[0] = np.nan


        # Equation for SI
        K = (np.maximum(abs(high - previous_close), abs(low - previous_close))/limit)
        si = (self.__c7/R) * ((close - previous_close) + (c_1 * (close - open)) + (c_2 * (previous_close - previous_open)))  * K

        # Accumulative Swing Index 
        asi = np.cumsum(si)

        asi = pd.Series(asi)
        asi.index = high.index
        return asi


    def __init_swing_points(self,x:pd.Series, hi=True) -> pd.Series:
        """
        This method is abstracted in terms of both price and asi. It calculates HIP, LOP, and HSP and LSP, in terms of price and asi, respectively
        This method calculates the critical points. Whenever a new local critical point is discovered, it is updated and remains 
        until a new one is found.
        - x: These are the values with which we will find our significant points
        - hi: Indicates whether we are looking for max or min
        Returns:
        - hsp or lsp, filled in **forward** so there are no nan values
        """
        swing_points = np.full(len(x), np.nan)
        if hi: # maxima
            for i in range(2, len(x)):
                # we cannot look ahead until the day finishes; take x[i - 1] as critical point
                if x.iloc[i - 1] >= x.iloc[i] and x.iloc[i - 1] >= x.iloc[i - 2]: # def of local maxima
                    swing_points[i] = x.iloc[i - 1]
                else:
                    continue
        else: # minima
            for i in range(2, len(x)):
                if x.iloc[i - 1] <= x.iloc[i] and x.iloc[i - 1] <= x.iloc[i - 2]: # def of local minima
                    swing_points[i] = x.iloc[i - 1]
                else:
                    continue

        # pandas manipulations; we convert to a pandas series, and make the indices the same
        swing_points = pd.Series(swing_points)
        swing_points.index = x.index

        # forward fills missing values, creating a sort of sar 
        swing_points.ffill(inplace=True)
        return swing_points


    def initialize_swing_df(self, data: pd.DataFrame) -> pd.DataFrame:
        '''
        This method will add the required variables for the Swing Index System to `data`.

        Parameters:
            - symbols : List of Tickers we want to add variables to
            - data    : The dataframe we will use to calculate the variables, and will hold the sws variables
        Returns:
            - dataframe of everything in it previously and six new columns: 'asi,' 'hsp,' 'hip,' 'lsp,' 'lop,' 'adxr.'

        '''

        # adxr
        adxr = pd.Series(talib.ADXR(data.loc[:]['high'], data.loc[:]['low'], data.loc[:]['close'], timeperiod=14))

        # Create values pertaining to the Swing Index System
        asi = self.__calculate_asi(data.loc[:]['high'], data.loc[:]['low'], data.loc[:]['close'], data.loc[:]['open'])
        hsp = self.__init_swing_points(asi)
        hip = self.__init_swing_points(data.loc[:]['high'])
        lsp = self.__init_swing_points(asi, False)
        lop = self.__init_swing_points(data.loc[:]['low'], False)
        data = data.copy()
        # Add those corresponding values to the dataframe
        data.loc[:, "asi"] = asi.values
        data.loc[:, "hsp"] = hsp.values
        data.loc[:, "hip"] = hip.values
        data.loc[:, "lsp"] = lsp.values
        data.loc[:, "lop"] = lop.values

        data.loc[:,"adxr_buy_threshold"] = adxr > self.__adxr_buy_threshold
        data.loc[:,"adxr_sell_threshold"] = adxr < self.__adxr_sell_threshold
            
        return data




    def initialize_swing_df_demo(self, data: pd.DataFrame) -> pd.DataFrame:
        '''
        This method will add the required variables for the Swing Index System to `data`.

        Parameters:
            - symbols : List of Tickers we want to add variables to
            - data    : The dataframe we will use to calculate the variables, and will hold the sws variables
        Returns:
            - dataframe of everything in it previously and six new columns: 'asi,' 'hsp,' 'hip,' 'lsp,' 'lop,' 'adxr.'

        '''

        adxr = pd.Series(talib.ADXR(data['high'], data['low'], data['close'], timeperiod=14))

        # Create values pertaining to the Swing Index System
        asi = self.__calculate_asi(data['high'], data['low'], data['close'], data['open'])
        hsp = self.__init_swing_points(asi)
        hip = self.__init_swing_points(data['high'])
        lsp = self.__init_swing_points(asi, False)
        lop = self.__init_swing_points(data['low'], False)
        data = data.copy()
        # Add those corresponding values to the dataframe
        data.loc[:,"asi"] = asi
        data.loc[:,"hsp"] = hsp
        data.loc[:,"hip"] = hip
        data.loc[:,"lsp"] = lsp
        data.loc[:,"lop"] = lop
        data.loc[:,"adxr_buy_threshold"] = adxr > self.__adxr_buy_threshold
        data.loc[:,"adxr_sell_threshold"] = adxr < self.__adxr_sell_threshold
            
        return data
    

class DemoStrategy:
    '''
    Aidan's Strategy. He's semi-retarded, but we decided to give him the benefit of the doubt.
    '''
    def __init__():
        pass


    def add_indicator(df: pd.DataFrame):
        '''
        c_0, o_0, h_0, l_0
        c_1, o_1, h_1, l_1

        o_1 < c_1 < c_0

        (c_2 - o_2)/x > 0.03
        '''
        signals = pd.Series([np.nan]*len(df))
        for i in range(3, len(df)):
            if df['open'].iloc[i - 2] < df['close'].iloc[i - 2]:
                if df['close'].iloc[i - 2] < df['close'].iloc[i - 3]:
                    percent_gain = (df['close'].iloc[i - 1] - df['open'].iloc[i])/df['open'].iloc[i - 1]
                    if percent_gain > 0.03:
                        signals.iloc[i] = 1
                        continue
            signals.iloc[i] = 0
        
    def add_extraneous_indicators(df: pd.DataFrame):
        '''
            1. Above 20 day EMA
            2. Below 20 day EMA
            3. Above 50 day EMA
            4. Below 50 day EMA
            5. Exit after 2% gain
            6. Exit after 3% gain
        '''
        twenty_day_ema = 0
        fifty_day_ema = 0

        # indicator r.v
        df['above_twenty_ema'] = df['low'] > twenty_day_ema 
        df['above_fifty_ema'] = df['low'] > fifty_day_ema 


