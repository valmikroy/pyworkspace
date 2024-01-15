#!/usr/bin/env python


import yfinance as yf
from datetime import date
from dateutil.relativedelta import relativedelta
from termcolor import colored, cprint
from tabulate import tabulate


class Index:
    
    def __init__(self, stock, history=2) -> None:
        self.stock = stock 
        self.history = history
    

        today = date.today().replace(month=date.today().month)
        start_date = today - relativedelta(days=self.history)       

        self.df = yf.download(self.stock,
                 start=start_date,
                 end=today,
                 progress=False)
        
        self.df.reset_index(inplace=True)

    def last_price(self):
        df = self.df
        p = round(float(df['Close'].iloc[-1]),2) 
        if p > 20:
            p = Index.red(p)
        elif p < 12:
            p = Index.green(p)
        else:
            p = str(p)
        return p       
    
    def red(v):
        return colored(v,'red',attrs=['reverse', 'blink'])
                
    def green(v):
        return colored(v,'green',attrs=['reverse', 'blink'])


class Stock:

    def __init__(self, stock, history=400) -> None:
        self.stock = stock 
        self.history = history
    

        today = date.today().replace(month=date.today().month)
        start_date = today - relativedelta(days=self.history)       

        self.df = yf.download(self.stock,
                 start=start_date,
                 end=today,
                 progress=False)
        
        self.df.reset_index(inplace=True)


    def macd(self, fast=12, slow=26, signal=9):
        df = self.df
        df[f'EMA{fast}'] = df['Close'].ewm(span=fast, adjust=False).mean()
        df[f'EMA{slow}'] = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = df[f'EMA{fast}'] - df[f'EMA{slow}']
        df['sline'] = df['MACD'].ewm(span=signal, adjust=False).mean()

        macd = round(float(self.df['MACD'].tail(1)),2)
        signal = round(float(self.df['sline'].tail(1)),2)
        return [macd,signal]


    def bolinger(self,win=20):
        df = self.df
        df['SMA'] = df['Close'].rolling(window=win).mean()
        df['SD'] = df['Close'].rolling(window=win).std()
        df['BB_UPPER'] = df['SMA'] + 2 * df['SD']
        df['BB_LOWER'] = df['SMA'] - 2 * df['SD']

        bb_upper = round(float(df['BB_UPPER'].tail(1)),2)
        bb_lower = round(float(df['BB_LOWER'].tail(1)),2)
        bb_mean = round(float(df['SMA'].tail(1)),2)

        return [ bb_lower, bb_mean, bb_upper]
    

    def rsi(self,win=14):
        df = self.df
        
        change = df['Close'].diff()
        change.dropna(inplace=True)

        # two copies 
        change_up = change.copy()
        change_down = change.copy()

        # zero out opposite trend
        change_up[change_up<0] = 0
        change_down[change_down>0] = 0

        # verify the above zero outting
        change.equals(change_up+change_down)

        # averages 
        avg_up = change_up.rolling(14).mean()
        avg_down = change_down.rolling(14).mean().abs()

        # relative stregth
        rsi = 100 * avg_up / (avg_up + avg_down)

        # Take a look at the 20 oldest datapoints
        rsi.dropna(inplace=True)
        #self.rsi = rsi

        return round(rsi.iloc[-1],2)


    def vol_history(self):
        df = self.df
        week = 5 * -1
        month = week * 4
        year = month  * 12

        ret1 = round(float(df['Volume'].iloc[-2]),2) 
        ret2 = round(float(df['Volume'].iloc[week]),2) 
        return [ ret1, ret2 ]


    def price_history(self):
        df = self.df
        week = 5 * -1
        month = week * 4
        year = month  * 12

        ret1 = round(float(df['Close'].iloc[-2]),2) 
        ret2 = round(float(df['Close'].iloc[week]),2) 
        ret3 = round(float(df['Close'].iloc[month]),2) 
        ret4 = round(float(df['Close'].iloc[year]),2) 
        return [ ret1, ret2, ret3, ret4 ]
    
    def last_price(self):
        df = self.df
        return round(float(df['Close'].iloc[-1]),2) 
    
    def last_volume(self):
        df = self.df
        return round(float(df['Volume'].iloc[-1]),2) 


    def stock_line_data(self):
        line = []
        line.append(self.stock)

        # Last price
        last = self.last_price()
        line.append(str(last))

        # Price history 
        l = []
        for v in self.price_history():
            if last > v:
                l.append(Stock.red(v))      
            else:
                l.append(Stock.green(v))      
        line.append("/".join(str(z) for z in l ))


        # MACD
        l = []
        macd, signal = self.macd()
        if signal < 0 and signal < macd:
            l = [str(macd), Stock.red(signal)]  
        else:
            l = [str(macd), Stock.green(signal)]  
        line.append("/".join(str(z) for z in l ))


        # Bolinger
        l = []
        low, mid, high = self.bolinger()
        if mid > last:
            mid = Stock.red(mid)
        elif low > last:
            low = Stock.red(low)
        elif last > high:
            high = Stock.green(high)
        l = [low, mid, high] 
        line.append("/".join(str(z) for z in l ))

        # RSI
        rsi = self.rsi()
        if rsi > 50:
            line.append(Stock.green(rsi))
        else:
            line.append(Stock.red(rsi))

        # Volume
        l = []
        last_vol = self.last_volume()
        l.append(last_vol)
        for v in self.vol_history():
            vv = round(((last_vol - v)/v)*100,2)
            if last_vol > v:
                l.append(Stock.green(vv))      
            else:
                l.append(Stock.red(vv))      
        line.append("/".join(str(z) for z in l ))
    
        return line


    def stock_line_header():
        return ['Ticker', 'Last', '1d/1w/1m/1y', 'macd/sig', 'low/mid/high', 'rsi', 'vol/1d/1w']
                
    def red(v):
        return colored(v,'red',attrs=['reverse', 'blink'])
                
    def green(v):
        return colored(v,'green',attrs=['reverse', 'blink'])


def stock_watch(tickers=[]):
    all_data = []

    all_data.append( Stock.stock_line_header())
    for tick in tickers:
        d = Stock(tick).stock_line_data()
        all_data.append( d )

    print(tabulate(all_data,headers='firstrow'))


print("\n")
print( "VIX : ", Index('^VIX').last_price(), " ", "GVZ: ", Index('^GVZ').last_price())
print("\n")
stocks = ['AAPL', 'MSFT', 'AMZN', 'GOOG', 'META', 'TSLA', 'NVDA']
stock_watch(stocks)
print("\n")
sectors = ['SPY','XLV','XLU','XLP','XLRE','XLC','XLF','XLK','XLY']
stock_watch(sectors)
print("\n")
comm = ['GLDM', 'SLV', 'PPLT', 'CPER', 'URA']
stock_watch(comm)
print("\n")
crypto = ['BTC-USD','ETH-USD']
stock_watch(crypto)
print("\n")
