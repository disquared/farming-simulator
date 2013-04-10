#-------------------------------------------------------------------------------
# Name:        Computational Investing Part I HW3 marketsim.py
# Purpose:  http://wiki.quantsoftware.org/index.php?title=CompInvesti_Homework_3
#
# Author:      Di Di
#
# Created:     04/03/2013
# Copyright:   (c) Di Di 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import datetime as dt
import sys
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da


def portfolio_from_orders(filename, starting_cash):
    """
    :param filename: the path to a csv file containing a list of orders
    :param starting_cash: starting portfolio capital
    :return: a pandas dataframe containing the value of the portfolio on each trading day
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


def write_portfolio_to_file(portfolio, filename):

    # Cast all the values to integers
    portfolio['value'] = [int(v) for v in portfolio['value']]

    # Split the datetime objects to year, month, and day integers
    portfolio['year'] = [i.date().year for (i, s) in portfolio.iterrows()]
    portfolio['month'] = [i.date().month for (i, s) in portfolio.iterrows()]
    portfolio['day'] = [i.date().day for (i, s) in portfolio.iterrows()]

    # Write the columns to a csv file
    portfolio.to_csv(filename, cols=['year', 'month', 'day', 'value'], header=False, index=False)

    return


def main():
    args = sys.argv
    args.append('1000000')
    args.append('orders.csv')
    args.append('values.csv')

    p = portfolio_from_orders(args[2], args[1])
    write_portfolio_to_file(p, args[3])

    return


if __name__ == '__main__':
    main()
