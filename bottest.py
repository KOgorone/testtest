import time

import matplotlib.pyplot as plt
import numpy as np
import pyupbit
import pandas as pd
import datetime
import pandas

access = "pZuOj1PKWP8vnijaCtnllsAdFHl7u1NZFu9F3BxK"
secret = "tidRwi75358bTdvgIKdmTrEZy6LK3vICJgKaE2uK"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

# macd 구하기
def get_macd(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=200)
    df['ma12'] = round(df['close'].ewm(span=12).mean(), 2)
    df['ma26'] = round(df['close'].ewm(span=26).mean(), 2)
    macd = df['macd'] = round(df.apply(lambda x: (x['ma12'] - x['ma26']), axis=1).iloc[-1], 2)
    df['macds'] = round(df['macd'].ewm(span=9).mean(), 2)
    df['macdo'] = round(df['macd'] - df['macds'], 2)
    df['yes_macd'] = df['macd'].shift(1)
    df['yes_macds'] = df['macds'].shift(1)
    df['yes_macdo'] = df['macdo'].shift(1)
    return macd



def get_yes_macd(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=200)
    df['ma12'] = round(df['close'].ewm(span=12).mean(), 2)
    df['ma26'] = round(df['close'].ewm(span=26).mean(), 2)
    df['macd'] = round(df.apply(lambda x: (x['ma12'] - x['ma26']), axis=1), 2)
    df['macds'] = round(df['macd'].ewm(span=9).mean(), 2)
    df['macdo'] = round(df['macd'] - df['macds'], 2)
    df['yes_macd'] = df['macd'].shift(1)
    df['yes_macds'] = df['macds'].shift(1)
    df['yes_macdo'] = df['macdo'].shift(1)
    yes_macd = df['yes_macd'].iloc[-1]
    return yes_macd



def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0


def get_psar(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=200)
    # this is common accelerating factors for forex and commodity
    # for equity, af for each step could be set to 0.01
    initial_af = 0.02
    step_af = 0.02
    end_af = 0.2

    df['trend'] = 0
    df['sar'] = 0.0
    df['real sar'] = 0.0
    df['ep'] = 0.0
    df['af'] = 0.0

    # initial values for recursive calculation
    if df['close'][1] > df['close'][0]:
        df['trend'][1] = 1
    else:
        df['trend'][1] = -1
    if df['trend'][1] > 0:
        df['sar'][1] = df['high'][0]
    else:
        df['sar'][1] = df['low'][0]

    df['real sar'][1] = df['sar'][1]
    df['ep'][1] = df['high'][1] if df['trend'][1] > 0 else df['low'][1]
    df['af'][1] = initial_af

    # calculation
    for i in range(1, len(df)):

        temp = df['sar'][i - 1] + df['af'][i - 1] * (df['ep'][i - 1] - df['sar'][i - 1])
        if df['trend'][i - 1] < 0:
            df['sar'][i] = max(temp, df['high'][i - 1], df['high'][i - 2])
            temp = 1 if df['sar'][i] < df['high'][i] else df['trend'][i - 1] - 1
        else:
            df['sar'][i]= min(temp, df['low'][i - 1], df['low'][i - 2])
            temp = -1 if df['sar'][i] > df['low'][i] else df['trend'][i - 1] + 1
        df['trend'][i] = temp

        if df['trend'][i] < 0:
            temp = min(df['low'][i], df['ep'][i - 1]) if df['trend'][i] != -1 else df['low'][i]
        else:
            temp = max(df['high'][i], df['ep'][i - 1]) if df['trend'][i] != 1 else df['high'][i]
        df['ep'][i] = temp

        if np.abs(df['trend'][i]) == 1:
            temp = df['ep'][i - 1]
            df['af'][i] = initial_af
        else:
            temp = df['sar'][i]
            if df['ep'][i] == df['ep'][i - 1]:
                df['af'][i] = df['af'][i - 1]
            else:
                df['af'][i] = min(end_af, df['af'][i - 1] + step_af)
        df['real sar'][i] = temp
    real_sar = df['real sar'][-1]
    return real_sar

def get_yes_psar(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=200)
    # this is common accelerating factors for forex and commodity
    # for equity, af for each step could be set to 0.01
    initial_af = 0.02
    step_af = 0.02
    end_af = 0.2

    df['trend'] = 0
    df['sar'] = 0.0
    df['real sar'] = 0.0
    df['ep'] = 0.0
    df['af'] = 0.0

    # initial values for recursive calculation
    if df['close'][1] > df['close'][0]:
        df['trend'][1] = 1
    else:
        df['trend'][1] = -1
    if df['trend'][1] > 0:
        df['sar'][1] = df['high'][0]
    else:
        df['sar'][1] = df['low'][0]

    df['real sar'][1] = df['sar'][1]
    df['ep'][1] = df['high'][1] if df['trend'][1] > 0 else df['low'][1]
    df['af'][1] = initial_af

    # calculation
    for i in range(1, len(df)):

        temp = df['sar'][i - 1] + df['af'][i - 1] * (df['ep'][i - 1] - df['sar'][i - 1])
        if df['trend'][i - 1] < 0:
            df['sar'][i] = max(temp, df['high'][i - 1], df['high'][i - 2])
            temp = 1 if df['sar'][i] < df['high'][i] else df['trend'][i - 1] - 1
        else:
            df['sar'][i]= min(temp, df['low'][i - 1], df['low'][i - 2])
            temp = -1 if df['sar'][i] > df['low'][i] else df['trend'][i - 1] + 1
        df['trend'][i] = temp

        if df['trend'][i] < 0:
            temp = min(df['low'][i], df['ep'][i - 1]) if df['trend'][i] != -1 else df['low'][i]
        else:
            temp = max(df['high'][i], df['ep'][i - 1]) if df['trend'][i] != 1 else df['high'][i]
        df['ep'][i] = temp

        if np.abs(df['trend'][i]) == 1:
            temp = df['ep'][i - 1]
            df['af'][i] = initial_af
        else:
            temp = df['sar'][i]
            if df['ep'][i] == df['ep'][i - 1]:
                df['af'][i] = df['af'][i - 1]
            else:
                df['af'][i] = min(end_af, df['af'][i - 1] + step_af)
        df['real sar'][i] = temp
    yes_realsar = df['real sar'][-2]
    return yes_realsar

#보유 유무 확인
def has_item(ticker):
    df = pd.DataFrame(upbit.get_balances())
    if (df['currency'] == f'{ticker}').any():
        return True
    else:
        return False

def close(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=200)
    a = df['close'].iloc[-2]
    return a

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# 자동매매 시작
while True:
    try:
    #     now = datetime.datetime.now()
    #     start_time = get_start_time("KRW-BTC")
    #     end_time = start_time + datetime.timedelta(days=1)
    #
    #
    #     if start_time < now < end_time - datetime.timedelta(seconds=10):
    #         target_price = get_target_price("KRW-BTC", 0.5)
    #         ma15 = get_ma15("KRW-BTC")
    #         current_price = get_current_price("KRW-BTC")
    #         if target_price < current_price and ma15 < current_price:
    #             krw = get_balance("KRW")
    #             if krw > 5000:
    #                 upbit.buy_market_order("KRW-BTC", krw*0.9995)
    #     else:
    #         btc = get_balance("BTC")
    #         if btc > 0.00008:
    #             upbit.sell_market_order("KRW-BTC", btc*0.9995)
    #     time.sleep(1)
    # except Exception as e:
    #     print(e)
    #     time.sleep(1)
    #
        ticker = "KRW-ADA"
        current_price = get_current_price(ticker)
        psar = get_psar(ticker)
        yes_psar = get_yes_psar(ticker)

        macd = get_macd(ticker)
        yes_macd = get_yes_macd(ticker)

        if (current_price > psar) and (close(ticker) < yes_psar):
            krw = get_balance("KRW")
            if not has_item(ticker) and (krw > 5000):
                upbit.buy_market_order("KRW-ADA", krw*0.9995)
                print("매수!!")
        elif (macd < yes_macd):
            ada = get_balance('ADA')
            if has_item(ticker):
                if  -2 < (current_price - close(ticker)) /close(ticker)*100 < 0:
                    print("wait..")
                elif ada*current_price > 5000:
                    upbit.sell_market_order("KRW-ADA", ada*0.9995)
                    print('매도!!')
                else:
                    print("Wait...")
            else:
                print("wait...")

        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)

# psar = get_psar('KRW-ADA')
# df = pd.DataFrame(upbit.get_balances())
# print(psar)

# print(upbit.get_balances())
# df = pd.DataFrame(upbit.get_balances())
# print(df)
# print(df['currency'][1])
