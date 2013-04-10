#-------------------------------------------------------------------------------
# Name:        Computational Investing Part I HW3 analyze.py
# Purpose:  http://wiki.quantsoftware.org/index.php?title=CompInvesti_Homework_3
#
# Author:      Di Di
#
# Created:     04/06/2013
# Copyright:   (c) Di Di 2013
#-------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import datetime as dt
import sys
import os
import csv
import matplotlib.pyplot as plt
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu


def df_from_portfolio_values(filename):

    dates_arr = []
    values_arr = []

    # parse the csv file
    with open(filename, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            year = int(row[0])
            month = int(row[1])
            day = int(row[2])
            value = int(row[3])
            date = dt.datetime(year, month, day) + dt.timedelta(hours=16)
            dates_arr.append(date)
            values_arr.append(value)

    # Create the data frame
    df = pd.DataFrame(values_arr, index=dates_arr, columns=['value'])

    return df


def compare_portfolio_to_benchmark(portfolio, benchmark):

    # Compute normalized returns
    portfolio['value_norm'] = portfolio['value'] / float(portfolio.ix[0, 'value'])
    # Compute daily normalized returns
    rets_norm = portfolio['value_norm'].copy()
    tsu.returnize0(rets_norm)

    # Compute the statistics
    volatility = rets_norm.std()
    avg_daily_ret = rets_norm.mean()
    sharpe = np.sqrt(252) * avg_daily_ret / volatility
    cum_ret = portfolio['value_norm'][-1]

    # Do the same for the benchmark equity
    c_dataobj = da.DataAccess('Yahoo')
    ls_keys = ['close']
    ldf_data = c_dataobj.get_data(list(portfolio.index), [benchmark], ls_keys)
    d_data_b = dict(zip(ls_keys, ldf_data))
    na_price_b = d_data_b['close'].values
    na_normalized_price_b = na_price_b / na_price_b[0]
    rets_norm_b = na_normalized_price_b.copy()
    tsu.returnize0(rets_norm_b)
    volatility_b = rets_norm_b.std()
    avg_daily_ret_b = rets_norm_b.mean()
    sharpe_b = np.sqrt(252) * avg_daily_ret_b / volatility_b
    cum_ret_b = na_normalized_price_b[-1][0]

    print "Sharpe Ratio of Fund: %s" % sharpe
    print "Sharpe Ratio of %s: %s" % (benchmark, sharpe_b)
    print ""
    print "Standard Deviation of Fund: %s" % volatility
    print "Standard Deviation of %s: %s" % (benchmark, volatility_b)
    print ""
    print "Total Return of Fund: %s" % cum_ret
    print "Total Return of %s: %s" % (benchmark, cum_ret_b)
    print ""
    print "Average Daily Return of Fund: %s" % avg_daily_ret
    print "Average Daily Return %s: %s" % (benchmark, avg_daily_ret_b)

    plt.clf()
    plt.plot(portfolio.index, portfolio['value_norm'], portfolio.index, na_normalized_price_b)
    plt.legend(['Portfolio', benchmark])
    plt.ylabel('Adjusted Close')
    plt.xlabel('Date')
    plt.show()

    return


def main():
    args = sys.argv
    args.append(os.path.relpath('values.csv'))
    args.append('$SPX')

    df = df_from_portfolio_values(args[1])
    compare_portfolio_to_benchmark(df, args[2])

    return


if __name__ == '__main__':
    main()
