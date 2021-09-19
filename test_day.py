import time

import matplotlib.pyplot as plt
import numpy as np
import pyupbit
import pandas as pd
import datetime
import pandas
import requests

access = "pZxK"
secret = "t2uK"

def _parse_remaining_req(remaining_req):
    """

    :param remaining_req:
    :return:
    """
    try:
        p = re.compile("group=([a-z]+); min=([0-9]+); sec=([0-9]+)")
        m = p.search(remaining_req)
        return m.group(1), int(m.group(2)), int(m.group(3))
    except:
        return None, None, None


def _call_public_api(url, **kwargs):
    """

    :param url:
    :param kwargs:
    :return:
    """
    try:
        resp = requests.get(url, params=kwargs)
        remaining_req_dict = {}
        remaining_req = resp.headers.get('Remaining-Req')
        if remaining_req is not None:
            group, min, sec = _parse_remaining_req(remaining_req)
            remaining_req_dict['group'] = group
            remaining_req_dict['min'] = min
            remaining_req_dict['sec'] = sec
        contents = resp.json()
        return contents, remaining_req_dict
    except Exception as x:
        print("It failed", x.__class__.__name__)
        return None

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

    # df['ma5'] = df['close'].rolling(window=5).mean()
    # df['ma20'] = df['close'].rolling(window=20).mean()
    # df['ma60'] = df['close'].rolling(window=60).mean()

    df['ma12'] = df['close'].ewm(span=12).mean()
    df['ma26'] = df['close'].ewm(span=26).mean()
    # df['macd'] = df['ma12'] - df['ma26']
    df['macd'] = df.apply(lambda x: (x['ma12'] - x['ma26']), axis=1)
    df['macds'] = df['macd'].ewm(span=9).mean()
    df['macdo'] = df['macd'] - df['macds']


    # df['momentum'] = df['close'] - df['close'].shift(10)

    # delta = df['close'].diff()
    # gains, declines = delta.copy(), delta.copy()
    # gains[gains < 0] = 0
    # declines[declines >0] = 0
    # _gain = gains.ewm(com=13, min_periods=14).mean()
    # _lose = declines.abs().ewm(com=13, min_periods=14).mean()
    # RS = _gain/_lose
    # df['rsi'] = (100 - (100 / (1+RS)))

    L = df["low"].rolling(window=14).min()
    H = df["high"].rolling(window=14).max()
    df['fast_k'] = ((df["close"] - L) / (H - L)) * 100
    df['slow_k'] = df['fast_k'].rolling(window=3).mean()
    df['slow_d'] = df['slow_k'].rolling(window=3).mean()
    df['range'] = (df['high'] - df['low']) * 0.5

    df['R'] = (H - df['close']) /(H - L) * -100
    df['mbb'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['ubb'] = df['mbb'] + 2*df['std']
    df['lbb'] = df['mbb'] - 2*df['std']
    df['perb'] = (df['close'] - df['lbb']) / (df['ubb'] - df['lbb'])
    df['bw'] = (df['ubb'] - df['lbb']) / df['mbb']

    return df

def macd(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="week", count=200)
    df['ma12'] = round(df['close'].ewm(span=12).mean(), 2)
    df['ma26'] = round(df['close'].ewm(span=26).mean(), 2)
    df['macd'] = round(df.apply(lambda x: (x['ma12'] - x['ma26']), axis=1), 2)
    df['macds'] = round(df['macd'].ewm(span=9).mean(), 2)
    df['macdo'] = round(df['macd'] - df['macds'], 2)

    L = df["low"].rolling(window=14).min()
    H = df["high"].rolling(window=14).max()
    df['fast_k'] = ((df["close"] - L) / (H - L)) * 100
    df['slow_k'] = df['fast_k'].rolling(window=3).mean()
    df['slow_d'] = df['slow_k'].rolling(window=3).mean()
    df['range'] = (df['high'] - df['low']) * 0.5

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

def get_trade_vol(ticker):
    """
    최종 체결 가격 조회 (현재가)
    :param ticker:
    :return:
    """
    try:
        url = "https://api.upbit.com/v1/ticker"
        contents = _call_public_api(url, markets=ticker)[0]
        if not contents:
            return None

        if isinstance(ticker, list):
            ret = {}
            for content in contents:
                market = content['market']
                price = content['acc_trade_price_24h']
                ret[market] = price
            return ret
        else:
            return contents[0]['acc_trade_price_24h']
    except Exception as x:
        print(x.__class__.__name__)

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 자동매매 시작
while True:
    try:

        # 매수 종목 선택
        tickers = pyupbit.get_tickers(fiat='KRW')

        # for i in range(1, len(tickers)):
        #     if i == 1:
        #         ticker = tickers[i]
        #         df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
        #         df['currency'] = ticker
        #         df['trade_vol'] = get_trade_vol(ticker)
        #
        #     elif i != 1:
        #         ticker = tickers[i]
        #         df_temp = pyupbit.get_ohlcv(ticker, interval="day", count=1)
        #         df_temp['currency'] = ticker
        #         df_temp['trade_vol'] = get_trade_vol(ticker)
        #         df = df.append(df_temp)
        #         time.sleep(0.06)
        #
        # df.set_index('currency', inplace=True)
        # df = df.sort_values(by='trade_vol', ascending=False).head(50)
        # df = df.reset_index(drop=False, inplace=False)
        # ticker_buy = df['currency']

        # 매수시작
        for i in range(1, len(tickers)):
            ticker = tickers[i]
            code = ticker[4:]
            current_price = get_current_price(ticker)
            krw = get_balance("KRW")
            # 매도 확인부터
            if i == 0 or i == 33 or i == 66:
                for j in range(1, len(upbit.get_balances())):
                    code = upbit.get_balances()[j]['currency']
                    ticker = ('KRW-' + code)
                    if code == 'APENFT':
                        continue
                    indicator = calindicator(ticker)
                    clo = indicator['close']
                    time.sleep(0.02)
                    wmacd = macd(ticker)
                    # if code = ''
                    if has_item(code):
                        current_price = get_current_price(ticker)
                        avg = get_balance_avg(code)
                        sell = get_balance(code)
                        dif_rate = (((current_price * sell) - (avg * sell)) / (avg * sell)) * 100
                        if indicator['macd'][-1] - indicator['macd'][-2] < 0 and indicator['macdo'][-1] - indicator['macdo'][-2] < 0 :
                            if dif_rate > 0.5:
                                if (sell * current_price) > 5000:
                                    upbit.sell_market_order(ticker, sell)
                                    print(f'{ticker} few profit sell!!')
                            elif dif_rate < -5:
                                if (sell * current_price) > 5000:
                                    upbit.sell_market_order(ticker, sell)
                                    print(f'{ticker} loss sell!!')
                            else:
                                print(f"{ticker} selling check....")

                        elif ((clo[-1] - indicator['open'][-1]) / indicator['open'][-1]) * 100 < -2 :
                            if clo[-1] - (indicator['open'][-1]-indicator['range'][-2]) < 0:
                                if dif_rate > 0.5:
                                    if (sell * current_price) > 5000:
                                        upbit.sell_market_order(ticker, sell)
                                        print(f'{ticker} few profit sell!!')
                                elif dif_rate < -5:
                                    if (sell * current_price) > 5000:
                                        upbit.sell_market_order(ticker, sell)
                                        print(f'{ticker} loss sell!!')
                                else:
                                    print(f"{ticker} selling check....")

                        elif dif_rate < -5:
                            if (sell * current_price) > 5000:
                                upbit.sell_market_order(ticker, sell)
                                print(f'{ticker} lose sell!!')
                        else:
                            print(f"{ticker} selling check....")
                    time.sleep(0.06)
                print('balances check complete')

            if not has_item(code):
                indicator = calindicator(ticker)
                if indicator['R'][-2] - indicator['R'][-1] < 0 and indicator['R'][-2] <= -70 and indicator['R'][-1] > -80 \
                        and indicator['macdo'][-1] - indicator['macdo'][-2] > 0 and wmacd['macd'][-1] > wmacd['macd'][-2]:
                    if krw > 300000:
                        upbit.buy_market_order(ticker, 50000)
                        print(f"{ticker} buy!!")
                    else:
                        print(f'{ticker} money...')
                else:
                    print(f'{ticker} check!')

                # if indicator['slow_k'][-3] - indicator['slow_k'][-2] > 0 and indicator['slow_k'][-1] - indicator['slow_k'][-2] > 0 and indicator['macdo'][-1] - indicator['macdo'][-2] > 0:
                #     if krw > 300000:
                #         upbit.buy_market_order(ticker, 60000)
                #         print(f"{ticker} buy!!")
                #     else:
                #         print(f'{ticker} money...')
                #
                # elif indicator['macd'][-1] - indicator['macd'][-2] > 0 and indicator['macd'][-2] - indicator['macd'][-3] > 0 and indicator['macd'][-4] - indicator['macd'][-3] > 0:
                #     if indicator['close'][-1] -(indicator['open'][-1] - indicator['range'][-2]) > 0:
                #         if indicator['slow_k'][-1] - indicator['slow_k'][-2] > 0 :
                #             if krw > 300000:
                #                 upbit.buy_market_order(ticker, 60000)
                #                 print(f"{ticker} buy!!")
                #             else:
                #                 print(f'{ticker} money...')
                #         else:
                #             print(f'{ticker} check!')

            else:
                print(f"{ticker} keeping....")

            time.sleep(0.06)

        print('buylist check complete')

    except Exception as e:
        print(e)
        time.sleep(0.6)

