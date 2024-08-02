from typing import Union
import pandas as pd
from settings import LONG, SHORT, INITIAL

class Position:

    '''
    This class allows us to keep track of our positions. We can think of it as a trader; it creates the
    buy and sell signals for the algorithm we decide to implement.

     - num_shares : number of shares purchased
     - buy_price  : The price the asset was purchased at
     - asset      : The asset that was purchased
     - index      : The index in the dataframe at which the asset was brought 
     - state : LONG, SHORT, or INITIAL. Represents the state of our purchase
    '''
    def __init__(self, num_shares: int, buy_price: float, asset: str, index: int, state: str):
        self._buy_price  = buy_price
        self._asset  = asset
        self._start_index  = index
        self._sell_price = 0
        self._sell_index = 0
        self._num_shares = num_shares
        self._active = True
        self._state = state

    @property
    def profits_losses(self):
        return self._num_shares * (self._buy_price - self._sell_price)
    

    def sell(self, sell_price, sell_index):
        if self._state == "INITIAL":
            self._sell_price = self._buy_price
        else:
            self._sell_price = sell_price
        self._sell_index = sell_index
        self._active = False

    @property
    def state(self):
        return self._state
    
    @property
    def buy_price(self):
        return self._buy_price
    
    @property
    def time_held(self):
        return self._sell_index - self._start_index
    
    @property
    def asset(self):
        return self._asset
    
    @property
    def start_index(self):
        return self._start_index
    
    # define equality
    def __eq__(self, other):
        return self._start_index == other._start_index 
    
    # define method of comparison for sorting
    def __lt__(self, other):
        self._start_index  < other._start_index 


class SwingIndexPosition(Position):
        
    '''
    This class is a clever implementation, combining our features in the Position class with the 
    necessary properties for our states in the Swing Index System (specifically memorylessness).
    It is meant to manage our position autonomously. In a sense it is an AI algorithm, though I 
    do not like the sound of that in particular. In fact, I would rather think of it as a series
    of concrete steps that works to automate the trading logic of a regular trader using this 
    system.

    This class is ephemeral. Once we are done using it (we change states), we instantiate a new instance
    '''

    def __init__(self, num_shares: int, buy_price: float, asset: str, index: int, state: str):
        super().__init__(num_shares, buy_price, asset, index, state)


    def signal(self, df: pd.DataFrame):

        '''
        We consider the last index as the current day (no variables are calculated for it because it is
        "happening"). Therefore we calculate our SAR variables for indices 0,...,N-1.
        '''
        
        # we need at least one day of data
        if df.iloc[self._start_index:].shape[0] <= 2:
            return 0, 0
        trailing_sar = self.__get_trailing_sar(df.iloc[0:-1])
        sar = self.__get_sar(df.iloc[0:-1])

        # these are are bounds for buying and selling on the next day
        # after we are given the signal
        current_high = df.iloc[-1]['high']
        current_low = df.iloc[-1]['low']

        if self._state == INITIAL:
            entry_point_long = self.__initial_to_long(df.iloc[0:-1])
            entry_point_short = self.__initial_to_short(df.iloc[0:-1])
            # check if initial sar is triggered for long
            if entry_point_long != None and current_high >= entry_point_long:
                return 1, entry_point_long
            # check if initial sar is triggered for short
            elif entry_point_short != None and current_low <= entry_point_short:
                return -1, entry_point_short
            else:
                return 0, 0
        elif self._state == SHORT:
            # Sell threshold indicates we must sell
            if df['adxr_sell_threshold'].iloc[-1]:
                return -1, df['close'].iloc[-1]
            # Buy threshold indicates we can reverse
            if not df['adxr_buy_threshold'].iloc[-1]:
                return 0, 0
            # check if there exists a valid trailing sar
            if trailing_sar != None:
                # check if the trailing sar is triggered
                if current_high >= trailing_sar:
                    return 1, trailing_sar
            # check if the regular sar is triggered
            if current_high >= sar:
                return 1, sar
            return 0, 0
        elif self._state == LONG:
            # Sell threshold indicates we must sell
            if df['adxr_sell_threshold'].iloc[-1]:
                return -1, df['close'].iloc[-1]
            # Buy threshold indicates we can reverse
            if not df['adxr_buy_threshold'].iloc[-1]:
                return 0, 0
            # check if there exists a valid trailing sar
            if trailing_sar != None:
                # check if the trailing sar is triggered
                if current_low <= trailing_sar:
                    return -1, trailing_sar
            # check if the regular sar is triggered
            if current_low <= sar:
                return -1, sar
            return 0, 0

        

    def __get_trailing_sar(self, df: pd.DataFrame) -> Union[float, None]:
        '''
        This method calculates the trailing sar in terms of ASI. 
        
        If short, it finds the highest daily high made between the lowest lsp and the close of the day on which 
        the ASI increased by 60 points or more.

        If long, it finds the lowest daily low made between the highest hsp and the close of the day
        on which the ASI decreased by 60 points or more

            - df: Dataframe to perform our calculations on.

        Returns:
            - trailing_sar for the current trade
        '''
        
        # For long order
        if self._state == SHORT:
            sig_lsp_idx = df["lsp"][self._start_index:].idxmax(skipna=True) # get minimum LSP value for this trade
            integer_index = df.index.get_loc(sig_lsp_idx)
            # Iterate between this time interval
            for i in range(integer_index, len(df)):

                # Cannot be an LSP prior to the decrease
                if df["hsp"].iloc[i] != df["hsp"].iloc[i-1]:
                    break
                # ASI decreased by 60 points or more
                if df["asi"].iloc[i] - df["lsp"].loc[sig_lsp_idx] > 60:
                    return df['high'].iloc[i]
        
        # For short order
        elif self._state == LONG:
            sig_hsp_idx = df["hsp"][self._start_index:].idxmax(skipna=True) # get maximum HSP value for this trade

            # Convert the timestamp index to an integer index
            integer_index = df.index.get_loc(sig_hsp_idx)
            # Iterate between this time interval
            for i in range(integer_index, len(df)):

                # Cannot be an LSP prior to the decrease
                if df["lsp"].iloc[i] != df["lsp"].iloc[i-1]:
                    break
                # ASI decreased by 60 points or more
                if df["hsp"].loc[sig_hsp_idx] - df["asi"].iloc[i] > 60:
                    return df['low'].iloc[i]
                
        return None

    def __initial_to_long(self, df: pd.DataFrame):

        '''
        This function gives us and entry point and SAR value for entering long. It is meant to be calculated on each new 
        trading day. Also, it is the exact inverse of `initial_to_short()` below.

        Parameters:
         - df - DataFrame to analyze
        returns:
         - entry_point - If the price exceeds this value, then we go long on the corresponding security
         - entry_sar   - Immediately after being reversed to long the SAR is the previous LSP
        '''
        # ADXR buy threshold indicates when we can buy
        if not df['adxr_buy_threshold'].iloc[-1]:
            return None
        # Long when the ASI crosses above the previous significant HSP
        sig_hsp_idx = df["hsp"].idxmax(skipna=True)
        if pd.isna(sig_hsp_idx):
            return None
        if df["asi"].iloc[-1] > df["hsp"].loc[sig_hsp_idx] or df["asi"].iloc[-1] > df["hsp"].iloc[-1]:
            entry_point = df["hip"].loc[sig_hsp_idx] # trigger
            return entry_point
        return None
    
    def __initial_to_short(self, df):

        '''
        This function gives us and entry point and SAR value for entering short for the current trading day. 

        parameters:
            df - Pandas dataframe including the new price information. Fetched before the market opens.
        returns:
            entry_point - If the price exceeds this value, then we short the corresponding security
            entry_sar   - Immediately after being reversed to short the SAR is the previous HSP
        '''
        # ADXR buy threshold indicates when we can buy
        if not df['adxr_buy_threshold'].iloc[-1]:
            return None
        # Short when the ASI crosses below the previous significant LSP
        sig_lsp_idx = df["lsp"].idxmax(skipna=True)
        if pd.isna(sig_lsp_idx):
            return None
        if df["asi"].iloc[-1] < df["lsp"].loc[sig_lsp_idx] or df["asi"].iloc[-1] < df["lsp"].iloc[-1]:
            entry_point = df["lop"].loc[sig_lsp_idx] # trigger
            return entry_point
        return None
    

    def __get_sar(self, df: pd.DataFrame) -> float:
        if self._state == LONG:
            # Loop through all indices since our start
            for i in range(len(df) - 1,self._start_index, -1):
                # if the HSP changed, look for a new LSP in between the two intervals
                if df["hsp"].iloc[i] != df["hsp"].iloc[i-1]:
                    # Loop between the two intervals, looking at LSP values now
                    for j in range(i, len(df)):
                        if df["lsp"].iloc[j] != df["lsp"].iloc[j-1]: # LSP changed
                            if df["lop"].iloc[j] != df["lop"].iloc[j - 1]: # LOP changes as well
                                return df["lop"].iloc[j]
                            # Check if the LSP preceded the LOP by one day
                            try:
                                if df["lop"].iloc[j + 1] != df["lop"].iloc[j]:
                                    return df["lop"].iloc[j + 1]
                            # we access an element outside of the number of rows
                            except IndexError:
                                pass
                            # return the corresponding price
                            return df["low"].iloc[j]
            # If there exists no valid posterior SAR, then return the previous LSP (anterior SAR)
            return df["lop"].iloc[-1] 

        elif self._state == SHORT:
            # Loop through all indices since our start
            for i in range(len(df) - 1,self._start_index, -1):
                # if the LSP changed, look for a new HSP in between the two intervals
                if df["lsp"].iloc[i] != df["lsp"].iloc[i-1]:
                    # Loop between the two intervals, looking at HSP values now
                    for j in range(i, len(df)):
                        if df["hsp"].iloc[j] != df["hsp"].iloc[j-1]: # HSP changed
                            if df["hip"].iloc[j] != df["hip"].iloc[j - 1]:
                                return df["hip"].iloc[j]
                            # deal with precedence issue
                            try:
                                if df["hip"].iloc[j + 1] != df["hip"].iloc[j]:
                                    return df["hip"].iloc[j + 1]
                            except IndexError:
                                pass
                            return df["high"].iloc[j]
            return df["hip"].iloc[-1] 