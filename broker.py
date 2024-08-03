from typing import Union
import pandas as pd

class Broker:

    '''
    This is meant to virtualize the brokerage firm. 
    '''


    def submit_order(self,asset: str, df: pd.DataFrame, ask_price: int, type: str) -> Union[float, int]:
        '''
        Emulates submitting an order to a brokerage firm.
        Parameters:
            - asset     : The asset we would like to purchase
            - df        : The dataframe that contains OHLCV data
            - ask_price : The price we would like to buy the asset
            - type      : The type of order. Valid options include:
                        "market order"
                        "limit order"
                        "stop order"
        Returns:
            - Price at which the commodity was purchased
        '''
        # get df with asset
        # asset_df: pd.DataFrame = df.loc[asset]
        asset_df = df
        # for now, we just buy the asset and return the price it was brought for 
        if asset_df.iloc[-1]['high'] >= ask_price:
            return ask_price
        else: # error: The ask_price is not valid
            return -1
    '''
    The purpose of this method is to calculate the bid-ask spread. We use the method described in "A Simple Way to Estimate
    Bid-Ask Spreads from Daily High and Low Prices."
    '''
    '''
    def calculate_bid_ask_spread(self,df,index):
        observed_high = max(df[index - 1]['high'], df[index]['high'])
        observed_low = min(df[index - 1]['low'], df[index]['low'])
        gamma = (math.log(observed_high/observed_low)) ** 2

        # we take the positive root and solve for alpha w.r.t the quadratic equation
        alpha = (math.sqrt(2 * beta) - math.sqrt(beta))/(3 - (2 * math.sqrt(2))) - math.sqrt(gamma/(3 - (2 * math.sqrt(2))))
        spread = 2 * (math.exp(alpha) - 1)/(1 + math.exp(alpha))
        pass
    '''

