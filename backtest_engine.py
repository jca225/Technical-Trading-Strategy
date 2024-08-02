import numpy as np
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import datetime
from sw import SwingIndex
from datetime import timedelta
from broker import Broker
from capital_manager import CapitalManager
from position import SwingIndexPosition
import mplfinance as mpf
import yfinance as yf
from settings import LONG, SHORT, INITIAL, api, tz
import random

# Number of assets to sample from the list of tradable assets
N = 500

# Instantiate client used for fetching historical data
client = StockHistoricalDataClient("AKI29DKDVUCK0HHOWS29","exq36aNVg61VtaAhoiJnuBYofXvbNtGkaBYplDC0")

class Backtest():
    def __init__(self):
        pass

    def sample_data(self, start_date: pd.Timestamp, end_date: pd.Timestamp, timeframe=TimeFrame.Day):
        # Each element is of type <class 'alpaca_trade_api.entity.Asset'>
        active_assets = api.list_assets(status='active')

        # Get subset of assets that are tradable, then the symbol
        tradable_assets = [a for a in active_assets if a.tradable]
        sample_tradable_assets = random.sample(tradable_assets, N)
        sample_tradable_assets_symbols = [a.symbol for a in sample_tradable_assets]

        # Define parameters to send to the server
        request_params = StockBarsRequest(
                        symbol_or_symbols=sample_tradable_assets_symbols,
                        timeframe=timeframe,
                        start=start_date,
                        end=end_date
        )
        # Send request to the server, convert to dataframe
        bars = client.get_stock_bars(request_params).df

        # deal with assets that did not have historical data
        for i in range(len(sample_tradable_assets_symbols)):
            asset = sample_tradable_assets_symbols[i]
            try:
                bars.loc[asset]
            except KeyError:
                sample_tradable_assets_symbols.pop(i)
        return sample_tradable_assets_symbols,bars
        

    def get_data_bars(self, symbols: list, start_date: pd.Timestamp, end_date: pd.Timestamp, timeframe=TimeFrame.Day):

        '''
        This method will get data for symbols starting on start_date. The timeframe is by default 1 day

        Parameters:
            - symbols   : list
                        list of Tickers we want to fetch data from
            - start_date: TimeStamp
                        where to start collecting data. Takes input in the form `YYYY-MM-DD`
        Returns:
            - dataframe of the daily OHLC values for the specified symbols

        '''

        # Define parameters to send to the server
        request_params = StockBarsRequest(
                        symbol_or_symbols=symbols,
                        timeframe=timeframe,
                        start=start_date,
                        end=end_date
        )
        # Send request to the server, convert to dataframe
        bars = client.get_stock_bars(request_params).df

        return bars

    
    def plot(self, df: pd.DataFrame, orders: list):
        # Initialize the series with NaN values
        long_positions = pd.Series([np.nan] * len(df))
        short_positions = pd.Series([np.nan] * len(df))
        price = pd.Series([np.nan] * len(df))
        for i in range(len(df)):
            for order in orders:
                if order._start_index == i and order.state != INITIAL:
                    if order.state == LONG:
                        long_positions.iloc[i] = order.buy_price
                    elif order.state == SHORT:
                        short_positions.iloc[i] = order.buy_price
        long_positions.index = df.index
        short_positions.index = df.index

        # Define the colors for the markers
        event_colors = {'LONG': 'green', 'SHORT': 'red'}

        buy_markers = mpf.make_addplot(long_positions, type='scatter', markersize=120, marker='^')
        sell_markers = mpf.make_addplot(short_positions, type='scatter', markersize=120, marker='v')

        markers = [buy_markers, sell_markers]

        mpf.plot(df[['open', 'high', 'low', 'close']], title='Swing Index System', ylabel='Price', addplot=markers)


        return df

    def backtest(self, stocklist: list, total_capital: float, start_dt: str, end_dt: str, c1=.5, c2=.25, c3=.5, c4=.25, c5=.25, c6=3, c7=50, a1=20, a2=25):

        # Instantiate VBF
        broker = Broker()

        # all orders
        inactive_orders = []
        # parameters for the Capital Manager class
        margin_per_commodity = .15
        total_margin = .6
        capital_manager = CapitalManager(total_capital, total_margin, margin_per_commodity)

        initial_date = pd.to_datetime(start_dt).tz_localize('America/New_York')
        end_date = pd.to_datetime(end_dt).tz_localize('America/New_York')

        # this is in a sense a virtualization
        swing_index = SwingIndex(stocklist)

        # this method is choreagraphed for a very specific type of dataset! This should be developed with 
        # great thought
        stocklist_override, df_init_all_assets = self.sample_data(initial_date, end_date)
        stocklist = stocklist_override
        for asset in stocklist:
            df_init_one_asset = df_init_all_assets.loc[asset]
            position = SwingIndexPosition(0, 0, asset, 0, "INITIAL")

            # add logic so that orders pertaining to the same asset are mutually exclusive
            for i in range(2,df_init_one_asset.shape[0]):
                # each 'i' is currently happening
            
                # take the dataframe up to these indexes
                df = df_init_one_asset.iloc[0:i]
                # initialize df
                df = swing_index.initialize_swing_df_demo(df)
                # check if any of the values are null (invalid values)
                if df.iloc[-1].isnull().any():
                    continue
                # create signal
                signal, ask_price = position.signal(df)
                # buy signal 
                if signal == 1 and position.state != LONG:
                    sell_index = len(df) - 1
                    # buy was a success
                    if (broker.submit_order(asset,df,ask_price,"LIMIT") != -1):
                        position.sell(ask_price, sell_index)
                        inactive_orders.append(position)
                        position = SwingIndexPosition(1, ask_price, asset, sell_index, LONG)
                            
                # we move LONG -> SHORT (markov property: memoryless) 
                elif signal == -1 and position.state != SHORT:
                    # we are able to make an order based on the rules of our capital management system
                    sell_index = len(df)
                    # buy was a success
                    if (broker.submit_order(asset,df, ask_price,"LIMIT") != -1):
                        position.sell(ask_price, sell_index)
                        inactive_orders.append(position)
                        pl = position.profits_losses
                        position = SwingIndexPosition(1, ask_price, asset, sell_index, "SHORT")

        total_profit = sum(order.profits_losses for order in inactive_orders)
        self.plot(df, inactive_orders)
        self.calculate_statistics(inactive_orders)
        sorted_inactive_orders = sorted(inactive_orders)
        # create series to put our data into pandas df
        pl_series = pd.Series([order.profits_losses for order in sorted_inactive_orders])
        asset_series = pd.Series([order.asset for order in sorted_inactive_orders])
        buy_series = pd.Series([order.start_index for order in sorted_inactive_orders])
        time_held_series = pd.Series([order.time_held for order in sorted_inactive_orders])
        buy_price_series = pd.Series([order.buy_price for order in sorted_inactive_orders])
        buy_date_series = pd.Series([df_init_all_assets.loc[order.asset].index[order.start_index] for order in sorted_inactive_orders])
        df = pd.DataFrame({"profits_losses": pl_series, "asset":asset_series, "buy_index":buy_series, "time_held":time_held_series, "buy_price":buy_price_series, "buy_date":buy_date_series})
        return df
    

    def backtest_testcase(self, stocklist: list, total_capital: float, start_dt: str, end_dt: str, c1: float, c2: float, c3: float, c4: float, c5: float, c6: float, c7: float, a1: float, a2: float):
        a1 = 1000
        a2 = 0
        # Instantiate VBF
        broker = Broker()

        # all orders
        inactive_orders = []
        # parameters for the Capital Manager class
        margin_per_commodity = .15
        total_margin = .6
        capital_manager = CapitalManager(total_capital, total_margin, margin_per_commodity)

        # this is in a sense a virtualization
        swing_index = SwingIndex("DEMO", c1, c2, c3, c4, c5, c6, c7, a1, a2)

        # this method is choreagraphed for a very specific type of dataset! This should be developed with 
        # great thought
        
        
        # Specify the file path
        file_path = '/Users/johncabrahams/Desktop/Projects/Operation Algo/operation_dart_monkey/demo_data.txt'

        # Read the data from the text file
        df_init_one_asset = pd.read_csv(file_path, sep=" ")
        df_init_one_asset = df_init_one_asset.drop(df_init_one_asset.columns[-1],axis=1)

        asset = "DEMO"
        position = SwingIndexPosition(0, 0, asset, 0, "INITIAL")
        

        # add logic so that orders pertaining to the same asset are mutually exclusive
        for i in range(2,df_init_one_asset.shape[0]):
            # each 'i' is currently happening
        
            # take the dataframe up to these indexes
            df = df_init_one_asset.iloc[0:i]
            # initialize df
            df = swing_index.initialize_swing_df_demo(df)
            # check if any of the values are null (invalid values)
            if df.iloc[-1].isnull().any():
                continue
            # create signal
            signal, ask_price = position.signal(df)
            # buy signal 
            if signal == 1 and position.state != LONG:
                sell_index = len(df) - 1
                # we are able to make an order based on the rules of our capital management system
                if capital_manager.submit_order_check(1,ask_price):
                    # buy was a success
                    if (broker.submit_order(asset,df,ask_price,"LIMIT") != -1):
                        position.sell(ask_price, sell_index)
                        inactive_orders.append(position)
                        position = SwingIndexPosition(1, ask_price, asset, sell_index, LONG)
                        capital_manager.buy(1, ask_price)
            # we move LONG -> SHORT (markov property: memoryless) 
            elif signal == -1 and position.state != SHORT:
                # we are able to make an order based on the rules of our capital management system
                sell_index = len(df)
                if capital_manager.submit_order_check(1,ask_price):
                    # buy was a success
                    if (broker.submit_order(asset,df, ask_price,"LIMIT") != -1):
                        position.sell(ask_price, sell_index)
                        inactive_orders.append(position)
                        pl = position.profits_losses
                        capital_manager.sell(1, ask_price, pl)
                        position = SwingIndexPosition(1, ask_price, asset, sell_index, "SHORT")
        total_profit = 0                 
        for order in inactive_orders:
            total_profit += order.profits_losses
                #print(order.profits_losses)
        #df = self.plot(df, inactive_orders)
        self.calculate_statistics(inactive_orders)
        print(total_profit)
        return total_profit
    
    def plot(self, df: pd.DataFrame, orders: list):
        # Initialize the series with NaN values
        long_positions = pd.Series([np.nan] * len(df))
        short_positions = pd.Series([np.nan] * len(df))
        for i in range(len(df)):
            for order in orders:
                if order._start_index == i and order.state != INITIAL:
                    if order.state == LONG:
                        long_positions.iloc[i] = order.buy_price
                    elif order.state == SHORT:
                        short_positions.iloc[i] = order.buy_price
        long_positions.index = df.index
        short_positions.index = df.index

        buy_markers = mpf.make_addplot(long_positions, type='scatter', markersize=120, marker='^')
        sell_markers = mpf.make_addplot(short_positions, type='scatter', markersize=120, marker='v')

        markers = [buy_markers, sell_markers]

        mpf.plot(df[['open', 'high', 'low', 'close']], title='Swing Index System', ylabel='Price', addplot=markers)



    def calculate_statistics(self, orders):
        length = len(orders)
        assets = pd.Series([np.nan] * length)
        profits_losses = pd.Series([np.nan] * length)
        state = pd.Series([np.nan] * length)
        time_held = pd.Series([np.nan] * length)

        for i in range(length):
            assets.iloc[i] = orders[i].asset
            profits_losses.iloc[i] = orders[i].profits_losses
            state.iloc[i] = orders[i].state
            time_held.iloc[i] = orders[i].time_held
        

        df = pd.DataFrame({'assets': assets, 'pl': profits_losses, 'state': state, 'number of days': time_held})

        # get only Long trades
        df_long = df.loc[lambda df: df['state'] == LONG, :]
        
        # get only short trades
        df_short = df.loc[lambda df: df['state'] == SHORT, :]

        pl_long_stats = {
        'Profit/Losses Long Mean': df_long['pl'].mean(),
        'Profit/Losses Long Standard Deviation': df_long['pl'].std(),
        'Profit/Losses Long Minimum': df_long['pl'].min(),
        'Profit/Losses Long Maximum': df_long['pl'].max()
        }

        pl_short_stats = {
        'Profit/Losses Short Mean': df_short['pl'].mean(),
        'Profit/Losses Short Standard Deviation': df_short['pl'].std(),
        'Profit/Losses Short Minimum': df_short['pl'].min(),
        'Profit/Losses Short Maximum': df_short['pl'].max()
        }


        pl_overall_stats = {
        'Profit/Losses Mean': df['pl'].mean(),
        'Profit/Losses Standard Deviation': df['pl'].std(),
        'Profit/Losses Minimum': df['pl'].min(),
        'Profit/Losses Maximum': df['pl'].max()
        }

        time_long_stats = {
        'Time per Trade Long Mean': df_long['number of days'].mean(),
        'Time per Trade Long Standard Deviation': df_long['number of days'].std(),
        'Time per Trade Long Minimum': df_long['number of days'].min(),
        'Time per Trade Long Maximum': df_long['number of days'].max()
        }

        time_short_stats = {
        'Time per Trade Short Mean': df_short['number of days'].mean(),
        'Time per Trade Short Standard Deviation': df_short['number of days'].std(),
        'Time per Trade Short Minimum': df_short['number of days'].min(),
        'Time per Trade Short Maximum': df_short['number of days'].max()
        }


        time_overall_stats = {
        'Time per Trade Mean': df['number of days'].mean(),
        'Time per Trade Standard Deviation': df['number of days'].std(),
        'Time per Trade Minimum': df['number of days'].min(),
        'Time per Trade Maximum': df['number of days'].max()
        }

        all_stats = [pl_long_stats, pl_short_stats, pl_overall_stats, time_long_stats, time_overall_stats, time_overall_stats]
        
        for stat in all_stats:
            for stat, value in stat.items():
                print(f"{stat}: {value}")
        
        # security traded

        pass

