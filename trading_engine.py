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


def get_data_bars(symbols: list, start_date: pd.Timestamp, end_date: pd.Timestamp, timeframe=TimeFrame.Day):

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


    # Instantiate client used for fetching historical data
    client = StockHistoricalDataClient("PKO3PXBNSZ2T56DJ43LX","xNiiXnClkbfWHgzoox1vpOjqcNyS7Y5jOI0djt2D")

    # Convert start_date to datetime object
    #start_time = pd.to_datetime(start_date).tz_localize('America/New_York')
    #end_time   = pd.to_datetime(end_date).tz_localize('America/New_York')

    # Define parameters to send to the server

    request_params = StockBarsRequest(
                    symbol_or_symbols=symbols,
                    timeframe=timeframe,
                    start=start_date,
                    end=end_date
    )
    # Send request to the server, convert to dataframe
    bars = client.get_stock_bars(request_params).df

    '''
    data = yf.download(symbols, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    if data.empty:
        return data

    # Set the new MultiIndex
    #data['symbol'] = "KO"

    # Set the index using the new columns
    #data.set_index(['symbol'], inplace=True)
    data.columns = data.columns.str.lower()
    '''

    return bars

    

def get_test_data():
    # Read the contents of the file
    with open('/Users/johncabrahams/Desktop/Projects/Operation Algo/operation_dart_monkey/demo_data.txt', 'r') as file:
        content = file.read()

    # Split the content by whitespace to create a one-dimensional array
    one_dimensional_array = content.split()
    length = int(len(one_dimensional_array)/47)
    rows = [one_dimensional_array[i:i+length] for i in range(0, len(one_dimensional_array), length)]

    #for i in range(0,len(one_dimensional_array/4),4):
    data = pd.DataFrame(rows, columns=['open', 'high', 'low', 'close'])
    data = data.astype(float)
    start_date = '2024-01-01'
    end_date = '2024-01-04'
    date_range = pd.date_range(start=start_date, periods=47, freq='D')
    # Plot candlestick chart
    data.index = date_range

    return data

def get_data_bars_1m(symbols: list):

    today = datetime.today()

    # Instantiate client used for fetching historical data
    client = StockHistoricalDataClient("PKO3PXBNSZ2T56DJ43LX","xNiiXnClkbfWHgzoox1vpOjqcNyS7Y5jOI0djt2D")

    # Define parameters to send to the server
    request_params = StockBarsRequest(
                    symbol_or_symbols=symbols,
                    timeframe=TimeFrame.Minute,
                    start=today
    )
    # Send request to the server, convert to dataframe
    bars = client.get_stock_bars(request_params).df
    return bars


def time_to_open(current_time: datetime):
    '''
    Helper function for `trade().` Calculates the time until the market will open. 

    Parameters:
        - current_time: The current time from the market open. It is a datetime object 
    Returns:
        - Amount of time until the market will open (in seconds)

    '''
    if current_time.weekday() <= 4:
        d = (current_time + timedelta(days=1)).date()
    else:
        days_to_mon = 0 - current_time.weekday() + 7
        d = (current_time + timedelta(days=days_to_mon)).date()
    next_day = datetime.datetime.combine(d, datetime.time(9, 30, tzinfo=tz))
    seconds = (next_day - current_time).total_seconds()
    return seconds

'''
def trade(stocklist, df):

    # Global position variable
    position = Initial()
    print('run_checker started')
    entry_point = entry_sar = sar = trailing_sar = 0
    while True:

        # Check if Monday-Friday
        if datetime.datetime.now(tz).weekday() >= 0 and datetime.datetime.now(tz).weekday() <= 4:
            print('Trading day')

            # Check if it is time to conduct pre-trade calculations
            if datetime.datetime.now(tz).time() > datetime.time(9, 00) and datetime.datetime.now(tz).time() <= datetime.time(9, 30):
                print("Pre-Trade Calculations")

                # If we are in an initial position, find our entry point and entry sar
                if isinstance(position, Initial):
                    sar = trailing_sar = 0 # invalid
                    entry_point, entry_sar = position.initial_to_long(df)

                # If we are in a long position, find our SAR and trailing SAR
                elif isinstance(position, Long):
                    entry_point = entry_sar = 0 # invalid
                    sar = position.new_sar(df)
                    trailing_sar = position.trailing_sar(df)

            # Check if it is time to carry out orders
            if datetime.datetime.now(tz).time() > datetime.time(9, 30) and datetime.datetime.now(tz).time() <= datetime.time(15, 30):
                
                # get today's 1m bars
                today_bars_1m = get_data_bars_1m(df)

                # If we are in an initial position, check to see if we should initiate a position
                if isinstance(position, Initial):
                    pass

                # If we are in a long position, check to see if we should reverse our position
                elif isinstance(position, Long):
                    # get current price
                    pass
                
                # we run in cycles
                time.sleep(60)
            else:
                # Get time amount until open, sleep that amount
                print('Market closed ({})'.format(datetime.datetime.now(tz)))
                print('Sleeping', round(time_to_open(datetime.datetime.now(tz))/60/60, 2), 'hours')
                time.sleep(time_to_open(datetime.datetime.now(tz)))
        else:
            # If not trading day, find out how much until open, sleep that amount
            print('Market closed ({})'.format(datetime.datetime.now(tz)))
            print('Sleeping', round(time_to_open(datetime.datetime.now(tz))/60/60, 2), 'hours')
            time.sleep(time_to_open(datetime.datetime.now(tz)))
'''

