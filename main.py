from datetime import datetime, timedelta
import time
import ccxt
import yaml
import pandas as pd
import numpy as np
import re

# from ccxt import async_support
# import asyncio
# exchange = async_support.bitstamp({'enableRateLimit': True})

# b = ccxt.binance()
# response = b.load_markets()
#
# tickers = b.symbols
#
# max_len = len(max(tickers, key=len))
#
# tickers_formatted = [
#     ''.join([tick.ljust(max_len+3, ' ')
#     for tick in tickers[i:i+5]]).strip()
#     for i in range(0, len(tickers), 5)
# ]
#
# print('\n'.join(tickers_formatted))


MESSAGES = {}
VARIABLES = {}


# Saving environment variables
def setup():

    # Open config file and save variables locally
    with open('config.yaml', 'r') as myfile:
        config = yaml.load(myfile, Loader=yaml.Loader)

        # Save all messages to MESSAGES
        MESSAGES['exchange'] = config['MESSAGES']['message_1']
        MESSAGES['exchange_not_found'] = config['MESSAGES']['message_1_error_handler']
        MESSAGES['api_public_key'] = config['MESSAGES']['message_2']
        MESSAGES['api_secret_key'] = config['MESSAGES']['message_3']
        MESSAGES['ticker'] = config['MESSAGES']['message_4']
        MESSAGES['ticker_not_found'] = config['MESSAGES']['message_4_error_handler']
        MESSAGES['candle_interval'] = config['MESSAGES']['message_5']
        MESSAGES['candle_interval_not_found'] = config['MESSAGES']['message_5_error_handler']
        MESSAGES['start_date'] = config['MESSAGES']['message_6']
        MESSAGES['start_date_not_found'] = config['MESSAGES']['message_6_error_handler1']
        MESSAGES['start_date_doesnt_exist'] = config['MESSAGES']['message_6_error_handler2']
        MESSAGES['end_date'] = config['MESSAGES']['message_7']
        MESSAGES['end_date_not_found'] = config['MESSAGES']['message_7_error_handler']

        # Save all variables to VARIABLES
        VARIABLES['exchange'] = config['VARIABLES']['EXCHANGE']
        VARIABLES['api_public_key'] = config['VARIABLES']['API_PUBLIC_KEY']
        VARIABLES['api_secret_key'] = config['VARIABLES']['API_SECRET_KEY']


def main():

    #  1. Enter exchange used and display tickers
    if VARIABLES['exchange'] == '':
        VARIABLES['exchange'] = str(input(MESSAGES['exchange'])).lower()
    try:
        exchange = getattr(ccxt, VARIABLES['exchange'])()
    except:
        print(MESSAGES['exchange_not_found'] % VARIABLES['exchange'])
        return


    #   2. Add API public key if needed
    # api_public_key = input(MESSAGES['api_public_key'])
    #  3. Add API private key if needed
    # api_secret_key = input(MESSAGES['api_secret_key'])


    #  4. Enter ticker
    # First, display available tickers
    markets = exchange.load_markets()
    tickers = sorted(exchange.symbols)

    max_len = len(max(tickers, key=len))

    tickers_formatted = [''.join([tick.ljust(max_len+3, ' ')
                         for tick in tickers[i:i+5]]).strip()
                         for i in range(0, len(tickers), 5)]

    print('Available tickers: \n')
    print('\n'.join(tickers_formatted))

    VARIABLES['ticker'] = str(input(MESSAGES['ticker'])).upper()
    try:
        response = exchange.fetch_ohlcv(VARIABLES['ticker'])
    except:
        print(MESSAGES['ticker_not_found'] % (VARIABLES['ticker'], VARIABLES['exchange']))
        return


    #  5. Enter candle_interval
    VARIABLES['candle_interval'] = input(MESSAGES['candle_interval'])
    try:
        exchange.fetch_ohlcv(VARIABLES['ticker'], VARIABLES['candle_interval'], limit=500)
    except:
        print(MESSAGES['candle_interval_not_found'] % VARIABLES['candle_interval'])
        return
    else:
        interval_num = int(re.findall(r'\d+', VARIABLES['candle_interval'])[0])
        interval_str = re.findall(r'[a-zA-Z]+', VARIABLES['candle_interval'])[0]
        if interval_str == 's':
            timedelta_kwargs = {'seconds': interval_num}
        elif interval_str == 'm':
            timedelta_kwargs = {'minutes': interval_num}
        elif interval_str == 'h':
            timedelta_kwargs = {'hours': interval_num}
        elif interval_str == 'd':
            timedelta_kwargs = {'days': interval_num}

    #  6. Enter start_date
    VARIABLES['start_date'] = input(MESSAGES['start_date'])
    if VARIABLES['start_date'] != '':
        try:
            VARIABLES['start_date'] = datetime.strptime(VARIABLES['start_date'], '%Y-%m-%d %H:%M:%S')
        except:
            print(MESSAGES['start_date_not_found'] % VARIABLES['start_date'])
            return
        else:
            # Make sure first date pulled matches start_date
            data = exchange.fetch_ohlcv(
                VARIABLES['ticker'],
                VARIABLES['candle_interval'],
                limit=500,
                since=int(time.mktime(VARIABLES['start_date'].timetuple())*1000)
            )
            first_date = datetime.fromtimestamp(data[0][0]/1000)
            if first_date != VARIABLES['start_date']:
                print(MESSAGES['start_date_doesnt_exist'] % datetime.strftime(first_date, '%Y-%m-%d %H:%M:%S'))
                return

    #  7. Enter end_date
    VARIABLES['end_date'] = input(MESSAGES['end_date'])
    if VARIABLES['end_date'] != '':
        try:
            VARIABLES['end_date'] = datetime.strptime(VARIABLES['end_date'], '%Y-%m-%d %H:%M:%S')
        except:
            print(MESSAGES['end_date_not_found'] % VARIABLES['end_date'])
            return

    #  8. Double check everything entered correctly
    print('\n---\nIf this looks correct, press `Enter` only.  To cancel, type anything and press `Enter`\n')
    for key, val in VARIABLES.items():
        print(f'{key}:  {val}')
    print('\n---')
    response = input()
    if len(response) > 0:
        print('\nEnding early.\n')
        return
    else:
        print('\nLoading...\n')

    # Update start_Date and end_date if empty
    if VARIABLES['start_date'] == '':
        VARIABLES['start_date'] = None
    if VARIABLES['end_date'] == '':
        VARIABLES['end_date'] = datetime.now()

    #  9. Get that motherfucking data
    df = []
    while VARIABLES['start_date'] is None or VARIABLES['start_date'] < VARIABLES['end_date']:
        if VARIABLES['start_date'] is None:
            since=None
        else:
            since = int(time.mktime(VARIABLES['start_date'].timetuple())*1000)
        data = exchange.fetch_ohlcv(VARIABLES['ticker'], VARIABLES['candle_interval'], limit=500, since=since)
        df.extend(data)
        last_date = datetime.fromtimestamp(np.array(data)[-1, 0]/1000)
        VARIABLES['start_date'] = last_date + timedelta(**timedelta_kwargs)
        time.sleep(.1)

    df = pd.DataFrame(df, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = df['date'].apply(lambda x: datetime.fromtimestamp(x/1000))
    df.to_csv(f'{VARIABLES["ticker"].replace("/", "-")}.csv', index=False)

    print('DONE')


if __name__ == '__main__':
    setup()
    main()
