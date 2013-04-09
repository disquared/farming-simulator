import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np


def simulate(start, end, equities, allocs):
    vol, daily_ret, sharpe, cum_ret = 0,0,0,0
    
    # setup, get matrix of normalized closing prices
    dt_timeofday = dt.timedelta(hours=16)
    ldt_timestamps = du.getNYSEdays(start, end, dt_timeofday)
    c_dataobj = da.DataAccess('Yahoo', cachestalltime=0)
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = c_dataobj.get_data(ldt_timestamps, equities, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    na_price = d_data['close'].values
    na_normalized_price = na_price / na_price[0,:]
    
    # first, compute (normalized) daily returns
    na_weighted_cumulative_ret = np.sum(na_normalized_price * allocs, axis=1)
    na_normalized_weighted_daily_ret = na_weighted_cumulative_ret.copy()
    tsu.returnize0(na_normalized_weighted_daily_ret)    
    
    # compute volatility of daily returns of total portfolio
    vol = np.std(na_normalized_weighted_daily_ret)
    
    # compute average daily return
    daily_ret = np.mean(na_normalized_weighted_daily_ret)
    
    #compute Sharpe ratio
    sharpe = np.sqrt(252) * daily_ret / vol
    
    # compute cumulative return of portfolio
    cum_ret = na_weighted_cumulative_ret[len(na_weighted_cumulative_ret)-1]
    
    return vol, daily_ret, sharpe, cum_ret

def find_best_portfolio(start, end, equities):
    best = [0,0,0,0]
    best_sharpe = float("-inf")
    
    # setup, get matrix of closing prices
    dt_timeofday = dt.timedelta(hours=16)
    ldt_timestamps = du.getNYSEdays(start, end, dt_timeofday)
    c_dataobj = da.DataAccess('Yahoo', cachestalltime=0)
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = c_dataobj.get_data(ldt_timestamps, equities, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    na_price = d_data['close'].values
    na_normalized_price = na_price / na_price[0,:]
    
    steps = np.array(range(0, 11)) / 10.0
    for a in steps:
        for b in steps:
            for c in steps:
                for d in steps:
                    if (a + b + c + d == 1.0):
                        allocs = [a, b, c, d]
                        na_weighted_cumulative_ret = np.sum(na_normalized_price * allocs, axis=1)
                        na_normalized_weighted_daily_ret = na_weighted_cumulative_ret.copy()
                        tsu.returnize0(na_normalized_weighted_daily_ret)    
                        vol = np.std(na_normalized_weighted_daily_ret)
                        daily_ret = np.mean(na_normalized_weighted_daily_ret)
                        sharpe = np.sqrt(252) * daily_ret / vol
                        
                        if sharpe > best_sharpe:
                            best_sharpe = sharpe
                            best = [a, b, c, d]
    
    for alloc in best:
        best[best.index(alloc)] = round(alloc, 4)
    
    return best, best_sharpe
    
def print_results(array):
    vol, daily_ret, sharpe, cum_ret = array[0], array[1], array[2], array[3]
    print "Sharpe Ratio: %s" % sharpe
    print "Volatility (stdev of daily returns): %s" % vol
    print "Average Daily Return: %s" % daily_ret
    print "Cumulative Return: %s" % cum_ret

def main():
    print "---Part 2a---"
    start = dt.datetime(2011, 1, 1)
    end = dt.datetime(2011, 12, 31)
    equities = ['AAPL', 'GLD', 'GOOG', 'XOM']
    allocs = [0.4, 0.4, 0.0, 0.2]
    print_results(simulate(start, end, equities, allocs))
    
    print "---Part 2b---"
    start = dt.datetime(2010, 1, 1)
    end = dt.datetime(2010, 12, 31)
    equities = ['AXP', 'HPQ', 'IBM', 'HNZ']
    allocs = [0.0, 0.0, 0.0, 1.0]
    print_results(simulate(start, end, equities, allocs))    
    
    print "---Part 3quiz1---"
    start = dt.datetime(2011, 1, 1)
    end = dt.datetime(2011, 12, 31)
    equities = ['AAPL', 'GOOG', 'IBM', 'MSFT']    
    print find_best_portfolio(start, end, equities)
    
    print "---Part 3quiz2---"
    start = dt.datetime(2010, 1, 1)
    end = dt.datetime(2010, 12, 31)
    equities = ['C', 'GS', 'IBM', 'HNZ']  
    print find_best_portfolio(start, end, equities)
    
    print "---Part 4---"
    

if __name__ == '__main__':
    main()