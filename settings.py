import datetime
from pytz import timezone
import logging
import alpaca_trade_api as tradeapi

# Here we define macro-variables
global INITIAL 
INITIAL = "INITIAL"

global LONG 
LONG = "LONG"

global SHORT
SHORT = "SHORT"

TIMEZONE = 'EST'

LOGGING_INFO_FILE = './apca_algo.log'


SECRET_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
KEY_ID = 'XXXXXXXXXXXXXXXXXX'

ALPACA_LINK = 'https://api.alpaca.markets'

# Define global timezone
global tz
tz = timezone(TIMEZONE)

# Inputs logging info into './apca_algo.log'. 
logging.basicConfig(filename=LOGGING_INFO_FILE, format='%(name)s - %(levelname)s - %(message)s')
logging.warning('{} logging started'.format(datetime.datetime.now().strftime("%x %X")))

# Instantiate global trading-api 
global api
api = tradeapi.REST(KEY_ID,
                    SECRET_KEY,
                    ALPACA_LINK)


