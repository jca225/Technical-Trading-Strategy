from backtest_engine import Backtest
import pandas as pd
from datetime import date, timedelta
from bayes_opt import BayesianOptimization
from settings import api

# Read the CSV file
stock_df = pd.read_csv('/Users/johncabrahams/Desktop/Projects/Operation Algo/operation_dart_monkey/list_of_securities.csv')

# Get rid of those Tickers containing '.'
stock_df = stock_df[~stock_df['Ticker'].str.contains(r'[-.]')]

# sample size
n = 10

# random sample:
s = stock_df['Ticker'].sample(n=n, replace=False, random_state=1)

# define our parameters
#parameters = [0.5, 0.25, 0.5, 0.25, 0.25, 3, 50, 25, 25]

# optimal parameters
#optimal_parameters = [0.2089, 0.2616, 0.7351, 0.2036, 0.2297, 4.129, 19.88, 29.09, 43.61]
parameters = [0.2089, 0.2616, 0.7351, 0.2036, 0.2297, 4.129, 19.88, 29.09, 43.61]
backtest_engine = Backtest()

#s = ["PLTR"]

# where we will begin 
start_dt = '2019-11-19'
end_dt = '2023-11-19'

# difference between current and previous date
delta = timedelta(days=1)

total_capital = 1000

#backtest_engine.backtest(s, total_capital, start_dt, end_dt, optimal_parameters[0], optimal_parameters[1], optimal_parameters[2], optimal_parameters[3], optimal_parameters[4], optimal_parameters[5], optimal_parameters[6], optimal_parameters[7], optimal_parameters[8])
#backtest_engine.backtest(s, total_capital, start_dt, end_dt, parameters[0], parameters[1], parameters[2], parameters[3], parameters[4], parameters[5], parameters[6], parameters[7], parameters[8])
df = backtest_engine.backtest(s, total_capital, start_dt, end_dt)

# send to csv
df.to_csv('/Users/johncabrahams/Desktop/Projects/Operation Algo/operation_dart_monkey/buy_data.csv')
# define our keys
keys = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'a1', 'a2']

# define our bounds; we decide the hyperparameters by taking a 25% reduction on either side of our parameters:
bounds = []
for parameter in parameters:
    distance = .75*parameter
    bounds.append((parameter - distance, parameter + distance))

pbounds = dict(zip(keys, bounds))

def backtest_wrapper_to_optimize(c1, c2, c3, c4, c5, c6, c7, a1, a2):
    '''
    The purpose of this is to wrap our objective function so it only takes as inputs the 
    hyper parameters we would like to optimize
    '''
    

    # take sample of stocks as a list; Note: some stocks are not supported by Alpaca, which could prove troublesome
    #s = list(stock_df['Ticker'].sample(n = n, random_state=1))
    s = ["PLTR"]

    # where we will begin 
    start_dt = '2019-11-19'
    end_dt = '2023-11-19'

    # define start and end dates
    #start_dt = date(2022, 6, 10)
    #end_dt = date(2022, 6, 15)

    # difference between current and previous date
    delta = timedelta(days=1)

    total_capital = 100000
    return backtest_engine.backtest(s, total_capital, start_dt, end_dt, c1, c2, c3, c4, c5, c6, c7, a1, a2)

'''
optimizer = BayesianOptimization(
    f=backtest_wrapper_to_optimize,
    pbounds=pbounds,
    random_state=1,
)

optimizer.maximize(
    init_points=100,
    n_iter=100,
)

print(optimizer.max)
'''