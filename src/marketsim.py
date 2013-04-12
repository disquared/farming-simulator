#-------------------------------------------------------------------------------
# Name:        marketsim.py
#
# Author:      Di Di (ddi0168@gmail.com)
#
# Created:     04/10/2013
# Copyright:   (c) Di Di 2013
#-------------------------------------------------------------------------------

import pandas as pd
import numpy as np
import datetime as dt
import os
import time
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu
import matplotlib.pyplot as plt


def portfolio_from_orders(filename, starting_cash):
    """
    :param filename:        the path to a csv file containing a list of orders
    :param starting_cash:   starting portfolio capital
    :return:                a pandas dataframe containing the value of the portfolio per trading day
    """

    # read in the csv file; remove the trailing newline crap from the end of each line
    csv_headers = ('year', 'month', 'day', 'symbol', 'ordertype', 'amt', 'junk')
    orders = pd.read_csv(filename, header=None, names=csv_headers)
    del orders['junk']

    # construct an initial orders dataframe, sorted by date ascending
    dates_arr = [dt.datetime(s['year'], s['month'], s['day']) for (i, s) in orders.iterrows()]
    orders_dict = {'date': dates_arr,
                   'symbol': orders['symbol'],
                   'ordertype': orders['ordertype'],
                   'amt': orders['amt']}
    orders_headers = ('date', 'symbol', 'ordertype', 'amt')
    orders = pd.DataFrame(orders_dict, columns=orders_headers)
    orders = orders.sort(columns='date', axis=0, ascending=True)

    # Map each Buy/Sell transaction to a net quantity change
    orders['ordertype'] = orders['ordertype'].map(lambda x: 1 if x == 'Buy' else -1)
    orders['amt'] = orders['amt'] * orders['ordertype']
    del orders['ordertype']

    # Creating an object of the dataaccess class with Yahoo as the source
    dataobj = da.DataAccess('Yahoo')

    # Remove all the transactions with invalid symbols
    all_symbols = dataobj.get_all_symbols()
    bad_symbols = list(set(orders['symbol']) - set(all_symbols))
    if len(bad_symbols) != 0:
        print "Portfolio contains invalid symbols : ", bad_symbols
    for bad_symbol in bad_symbols:
        orders = orders[orders['symbol'] != bad_symbol]

    # calculate date boundaries
    startdate = orders.irow(0)['date']
    enddate = orders.irow(-1)['date']

    # Get a list of trading days between the start and the end
    ldt_timestamps = du.getNYSEdays(startdate, enddate + dt.timedelta(hours=16), dt.timedelta(hours=16))

    # Reading the data, now d_data is a dictionary with the keys above
    ls_keys = ['close']
    symbols = list(set(orders['symbol']))
    ##print "Relevant symbols: %", symbols

    ldf_data = dataobj.get_data(ldt_timestamps, symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))

    # Copying close price into separate dataframe to find rets
    prices = d_data['close'].copy()

    # Filling the data.
    #prices = prices.fillna(method='ffill')
    #prices = prices.fillna(method='bfill')

    # Subtract 16 hours from each of the dates in the index
    tmpDates = pd.DataFrame([date - dt.timedelta(hours=16) for date in prices.index], index=prices.index, columns=['date'])
    prices = prices.join(tmpDates)
    prices = prices.set_index('date')

    # Create the holdings df from orders
    timestamps = du.getNYSEdays(startdate, enddate)
    holdings_change = pd.DataFrame(np.zeros((len(timestamps), len(symbols)), dtype=np.int), columns=symbols, index=timestamps)
    for (i, s) in orders.iterrows():
        holdings_change.ix[s['date'], s['symbol']] = s['amt'] + holdings_change.ix[s['date'], s['symbol']]
    holdings = holdings_change.cumsum(axis=0)

    # Create the equities df from holdings and prices
    equities = (holdings * prices).sum(axis=1)

    # Create the cash df from orders, holdings_change, prices, and starting cash
    cash_change = pd.DataFrame(np.zeros((len(timestamps), 1)), columns=['value'], index=timestamps)
    for (i, s) in orders.iterrows():
        cash_change.ix[s['date']] += -1 * holdings_change.ix[s['date'], s['symbol']] * prices.ix[s['date'], s['symbol']]
    cash_change.ix[0] += int(starting_cash)
    cash = cash_change.cumsum(axis=0)

    # Create the overall portfolio df from equities and cash
    portfolio = equities + cash

    ##print "timestamps: %", timestamps
    ##print "orders: %", orders.ix[0:5]
    ##print "prices: %", prices.ix[0:5]
    ##print "holdings: %", holdings.ix[0:5]
    ##print "equities: %", equities.ix[0:5]
    ##print "cash_change: %", cash_change.ix[0:5]
    ##print "cash: %", cash.values
    ##print "total portfolio: %", portfolio

    return portfolio


def compare_portfolio_to_benchmark(portfolio, benchmark):
    """
    :param portfolio:   a pandas dataframe containing the value of the portfolio per trading day
    :param benchmark:   a string containing the symbol of the benchmark equity
    :return:            nothing, just display a graph, and print out a summary of statistics
    """

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
    c_dataobj = da.DataAccess('Yahoo') ##, cachestalltime=0)
    ls_keys = ['close']
    ldf_data = c_dataobj.get_data(list(portfolio.index + dt.timedelta(hours=16)), [benchmark], ls_keys)
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


def write_portfolio_to_csv_file(portfolio, filename):
    """
    :param portfolio:   a pandas dataframe containing the value of the portfolio on each trading day
    :param filename:    a string specifying the output csv filename
    :return:            nothing, just create a csv file representing the porfolio
    :note:              not currently used
    """

    # Cast all the values to integers
    portfolio['value'] = [int(v) for v in portfolio['value']]

    # Split the datetime objects to year, month, and day integers
    portfolio['year'] = [i.date().year for (i, s) in portfolio.iterrows()]
    portfolio['month'] = [i.date().month for (i, s) in portfolio.iterrows()]
    portfolio['day'] = [i.date().day for (i, s) in portfolio.iterrows()]

    # Write the columns to a csv file
    os.chdir('../out/')
    portfolio.to_csv(filename, cols=['year', 'month', 'day', 'value'], header=False, index=False)
    os.chdir('../src/')

    return


def main():

    orders_file = os.path.relpath('../test/orders.csv')
    starting_cash = 1000000
    benchmark = '$SPX'

    p = portfolio_from_orders(orders_file, starting_cash)
    compare_portfolio_to_benchmark(p, benchmark)
    #write_portfolio_to_csv_file(p, 'marketsim_portf_results.csv')

    return


if __name__ == '__main__':
    start_time = time.time()
    main()
    print "--------"
    print "Program execution time: %s seconds" % (time.time() - start_time)

