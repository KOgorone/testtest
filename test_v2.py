import time

import matplotlib.pyplot as plt
import numpy as np
import pyupbit
import pandas as pd
import datetime
import pandas
import talib

access = "K"
secret = "t2uK"

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
# 기술지표 구하기
def calindicator(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=200)
    df['ma5'] = talib.SMA(np.asarray(df['close']), 5)
    df['ma20'] = talib.SMA(np.asarray(df['close']), 20)
    df['ma60'] = talib.SMA(np.asarray(df['close']), 60)
    macd, macds, macdo = talib.MACD(np.asarray(df['close']), 12, 26, 9)
    df['macd'] = macd
    df['macds'] = macds
    df['macdo'] = macdo
    df['rsi'] = talib.RSI(np.asarray(df['close']), 14)
    df['psar'] = talib.SAR(df['high'], df['low'], acceleration=0.02,maximum=2)
    upper, middle, lower = talib.BBANDS(np.asarray(df['close']), timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    df['bbandup'] = upper
    df['bbandmid'] = middle
    df['bbandlow'] = lower
    df['momentum'] = talib.MOM(np.asarray(df['close']), timeperiod=10)
    df['momentumo'] = talib.CMO(df['close'], timeperiod=14)
    return df

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

def get_balance_avg(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0
    return 0


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
#     #     now = datetime.datetime.now()
#     #     start_time = get_start_time("KRW-BTC")
#     #     end_time = start_time + datetime.timedelta(days=1)
#     #
#     #
#     #     if start_time < now < end_time - datetime.timedelta(seconds=10):
#     #         target_price = get_target_price("KRW-BTC", 0.5)
#     #         ma15 = get_ma15("KRW-BTC")
#     #         current_price = get_current_price("KRW-BTC")
#     #         if target_price < current_price and ma15 < current_price:
#     #             krw = get_balance("KRW")
#     #             if krw > 5000:
#     #                 upbit.buy_market_order("KRW-BTC", krw*0.9995)
#     #     else:
#     #         btc = get_balance("BTC")
#     #         if btc > 0.00008:
#     #             upbit.sell_market_order("KRW-BTC", btc*0.9995)
#     #     time.sleep(1)
#     # except Exception as e:
#     #     print(e)
#     #     time.sleep(1)
#     #
        ticker = "KRW-ADA"
        code = ticker[4:]
        current_price = get_current_price(ticker)
        indicator = calindicator(ticker)
        avg = get_balance_avg(code)
        ada = get_balance(code)
        krw = get_balance("KRW")
        momen = indicator['momentum']


        if momen[-2] <5 and momen[-1] > 5:
            if not has_item(code):
                if krw > 5000:
                    upbit.buy_market_order(ticker, krw*0.9995)
                    print("매수!!")
        elif (indicator['macd'][-1] < indicator['macd'][-2]):
            ada = get_balance(code)
            if has_item(code):
                dif_rate = (((current_price * ada) - (avg * ada)) / (avg * ada)) * 100
                if dif_rate < -2 or dif_rate > 0.5:
                    if (ada * current_price) > 5000:
                        upbit.sell_market_order(ticker, ada)
                        print('매도!!')
                else:
                    print("젭알... 올라라")
            else:
                print("wait....")
        elif has_item(code):
            print("더더 올라라...")
        else:
            print("wait....")

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
