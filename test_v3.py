import time

import matplotlib.pyplot as plt
import numpy as np
import pyupbit
import pandas as pd
import datetime
import pandas
import talib

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
# 기술지표 구하기
def calindicator(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=200)
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()

    df['ma12'] = round(df['close'].ewm(span=12).mean(), 2)
    df['ma26'] = round(df['close'].ewm(span=26).mean(), 2)
    df['macd'] = round(df.apply(lambda x: (x['ma12'] - x['ma26']), axis=1), 2)
    df['macds'] = round(df['macd'].ewm(span=9).mean(), 2)
    df['macdo'] = round(df['macd'] - df['macds'], 2)

    df['momentum'] = df['close'] - df['close'].shift(10)

    delta = df['close'].diff()
    gains, declines = delta.copy(), delta.copy()
    gains[gains < 0] = 0
    declines[declines >0] = 0
    _gain = gains.ewm(com=13, min_periods=14).mean()
    _lose = declines.abs().ewm(com=13, min_periods=14).mean()
    RS = _gain/_lose
    df['rsi'] = (100 - (100 / (1+RS)))


    L = df["low"].rolling(window=14).min()
    H = df["high"].rolling(window=14).max()
    df['fast_k'] = ((df["close"] - L) / (H - L)) * 100
    df['slow_k'] = df['fast_k'].ewm(span=3).mean()
    df['slow_d'] = df['slow_k'].ewm(span=3).mean()

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
    df = pyupbit.get_ohlcv(ticker, interval="day", count=200)
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
        ticker = "KRW-XRP"
        code = ticker[4:]
        current_price = get_current_price(ticker)
        indicator = calindicator(ticker)
        avg = get_balance_avg(code)
        ada = get_balance(code)
        krw = get_balance("KRW")
        momen = indicator['momentum']


        if indicator['slow_k'][-1]-indicator['slow_d'][-1] > 0 and indicator['slow_k'][-2]-indicator['slow_d'][-2] < 0:
            if not has_item(code):
                if krw > 5000:
                    upbit.buy_market_order(ticker, 10000)
                    print("매수!!")
        elif indicator['slow_k'][-1]-indicator['slow_d'][-1] < 0 and indicator['slow_k'][-2]-indicator['slow_d'][-2] > 0:
            ada = get_balance(code)
            if has_item(code):
                dif_rate = (((current_price * ada) - (avg * ada)) / (avg * ada)) * 100
                if dif_rate < -3 or dif_rate > 0.5:
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

