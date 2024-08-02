from typing import Union
import pandas as pd

class CapitalManager():

    '''
    A Capital Manager. This is used as a method for managing money. 
    Parameters:
         - total_capital        : Amount of money the user has in their account
         - margin               : Maximum amount of capital allowed to be allocated as percent. (0 <= margin <= 1)
         - margin_per_commodity : Maximum amount of capital allowed to be allocated for each commodity as percent. 
                                  (0 <= margin_per_commodity <= 1)
    '''
    def __init__(self, total_capital: float, margin: float, margin_per_commodity: float): 
        self.__total_capital = total_capital # total capital
        self.__total_capital_allocated = 0 # total capital currently allocated
        # maximum amount of capital allowed to be allocated for each commodity
        self.__margin_per_commodity = total_capital * margin_per_commodity
        # maximum amount of capital allowed to be allocated in total
        self.__total_margin = total_capital * margin
        self.__buying_power = total_capital
    
    
    def submit_order_check(self, number_of_shares: Union[float, int], cost: float) -> bool:
        '''
        Checks to make sure we are able to buy an underlying asset based on our capital management system
        Parameters:
            - number_of_shares : Number of shares we are able to purchase. For now, we will only take ints as input (i.e., no fractional shares)
            - cost             : Cost of the asset
        return:
            bool indicating whether the order is able to be made
        '''

        total_cost = number_of_shares * cost
        if total_cost > self.__buying_power:
            return False
        return True

    def buy(self, number_of_shares: Union[float, int], cost: float) -> None:
        total_cost = number_of_shares * cost
        self.__buying_power -= total_cost

    def sell(self, number_of_shares: Union[float, int], cost: float, profits_losses: float) -> None:
        self.set_total_capital(profits_losses, cost)

    def set_total_capital(self, profits_losses: float, buy_price: float):
        self.__total_capital += profits_losses
        self.__total_capital_allocated -= buy_price

