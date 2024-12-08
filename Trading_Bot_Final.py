import hmac
import hashlib
import base64
import json
import time
import requests
import talib
import pandas as pd
import datetime as dt
import numpy as np

# Enter your API Key and Secret here. If you don't have one, you can generate it from the website.
key = "18672fb65b1378d14c06ce568317a2ef210e5dab92326d63"
secret = "79a62e7fe54d655e87198c443a006816431cd306fad2c088252f1dd1bdf52925"

# python3
secret_bytes = bytes(secret, encoding='utf-8')


#Market Candles Data Generator
url_ticker = "https://api.coindcx.com/exchange/ticker"
response_markets = requests.get(url_ticker)
data = response_markets.json()
markets_df = pd.DataFrame(data)
inr_candles = []
# Ensure last_price is converted to numeric, errors='coerce' will convert invalid parsing to NaN

# Now perform the comparison safely
# Your code logic here
for i in markets_df['market']:
        Uprice = float(markets_df.loc[markets_df['market'] == i, 'last_price'].values[0])
        if i[-3:] == 'INR' and (Uprice <= 100 and Uprice > 0.01):
            inr_candles.append(i[:-3])

df_data = pd.DataFrame(columns = inr_candles)

# Generating a timestamp.
timeStamp = int(round(time.time() * 1000))

#Order creation
def order(side: str, symbol: str, tq: float):
    body = {
    "side": side,    #Toggle between 'buy' or 'sell'.
    "order_type": "market_order", #Toggle between a 'market_order' or 'limit_order'.
    "market": symbol, #Replace 'SNTBTC' with your desired market pair.
    "total_quantity": tq, #Replace this with the quantity you want
    "timestamp": timeStamp,
    }
    
    json_body = json.dumps(body, separators = (',', ':'))
    
    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
    
    url_order = "https://api.coindcx.com/exchange/v1/orders/create"
    
    headers = {
    'Content-Type': 'application/json',
    'X-AUTH-APIKEY': key,
    'X-AUTH-SIGNATURE': signature
    }
    
    response_order = requests.post(url_order, data = json_body, headers = headers)
    print(symbol, side, pd.DataFrame(response_order))
    
#Order condition
def order_condtion(name: str):
    bitch = name + '_INR'
    url_candles  = f"https://public.coindcx.com/market_data/candles?pair=I-{bitch}&interval=30m"
    response_price = requests.get(url_candles)
    data_price = response_price.json()
    df_price = pd.DataFrame(data_price)
    t3_fast = talib.T3(df_price['close'], timeperiod = 8, vfactor = 0.7)
    t3_slow = talib.T3(df_price['close'], timeperiod = 13, vfactor = 0.6)
    if not t3_fast.empty and not t3_slow.empty:
        if t3_fast.iloc[-1] > t3_slow.iloc[-1]:
             return 1
        else:
             return 0
    else:
        print("One of the DataFrames is empty.")

#Main body
while True:
    secret_bytes = bytes(secret, encoding='utf-8')

    # Generating a timestamp
    timeStamp = int(round(time.time() * 1000))

    body = {
        "timestamp": timeStamp
    }

    json_body = json.dumps(body, separators = (',', ':'))

    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

    url_balances = "https://api.coindcx.com/exchange/v1/users/balances"

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': key,
        'X-AUTH-SIGNATURE': signature
    }

    response_account = requests.post(url_balances, data = json_body, headers = headers)
    data_account = response_account.json();
    df_account = pd.DataFrame(data_account)
    print(df_account)

    for name in df_account['currency']:
        if not order_condtion(name):
            balance_value = df_account[df_account['currency'] == name]['balance'].values[0]
            bv = float(balance_value)
            order('sell', name, round(bv, 0))
            inr_candles.append(name)


    for name in inr_candles:  
        if order_condtion(name):
            PPU = df_price['close'].tail(1).values[0]
            wallet = df_account[df_account['currency'] == 'INR']['balance'].values[0]
            tq = round((float(wallet)/PPU), 0)
            order('buy', name, tq)
            inr_candles.pop(name)