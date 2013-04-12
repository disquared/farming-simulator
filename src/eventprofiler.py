#-------------------------------------------------------------------------------
# Name:        eventprofiler.py
#
# Author:      Di Di (ddi0168@gmail.com)
#
# Created:     04/10/2013
# Copyright:   (c) Di Di 2013
#-------------------------------------------------------------------------------

import numpy as np
import copy
import time
import os
import QSTK.qstkutil.qsdateutil as du
import datetime as dt
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkstudy.EventProfiler as ep

from event import *


def five_dollar_event(ls_symbols, data, benchmark):

    # use actual close
    df_close = data['actual_close']
    ts_market = df_close[benchmark]

    # Creating an empty dataframe
    df_events = copy.deepcopy(df_close)
    df_events = df_events * np.NAN

    # Time stamps for the event range
    ldt_timestamps = df_close.index

    for s_sym in ls_symbols:
        for i in range(1, len(ldt_timestamps)):
            # Calculating the returns for this timestamp
            f_symprice_today = df_close[s_sym].ix[ldt_timestamps[i]]
            f_symprice_yest = df_close[s_sym].ix[ldt_timestamps[i - 1]]
            f_marketprice_today = ts_market.ix[ldt_timestamps[i]]
            f_marketprice_yest = ts_market.ix[ldt_timestamps[i - 1]]
            f_symreturn_today = (f_symprice_today / f_symprice_yest) - 1
            f_marketreturn_today = (f_marketprice_today / f_marketprice_yest) - 1

            # Event is price transition at $5
            if f_symprice_yest >= 5.0 and f_symprice_today < 5.0:
                df_events[s_sym].ix[ldt_timestamps[i]] = 1

    return df_events

def main():
    startdate = dt.datetime(2008, 1, 1)
    enddate = dt.datetime(2009, 12, 31)
    timestamps = du.getNYSEdays(startdate, enddate, dt.timedelta(hours=16))

    dataobj = da.DataAccess('Yahoo')
    ls_symbols = dataobj.get_symbols_from_list('sp5002012')
    benchmark = 'SPY'
    ls_symbols.append(benchmark)
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = dataobj.get_data(timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))

    # remove NaN from price data
    for k in ls_keys:
        d_data[k] = d_data[k].fillna(method = 'ffill')
        d_data[k] = d_data[k].fillna(method = 'bfill')
        d_data[k] = d_data[k].fillna(1.0)

    event = Event('five_dollar_event')
    df_events = event.find_events(ls_symbols, d_data, benchmark)

    #df_events = find_events(event_func, ls_symbols, d_data, benchmark)

    # Create the event study
    print "Creating study for: " + event.event_name
    outfile = '../out/' + event.event_name + '.pdf'
    ep.eventprofiler(df_events, d_data, i_lookback=20, i_lookforward=20,
                     s_filename=outfile, b_market_neutral=True, b_errorbars=True,
                     s_market_sym=benchmark)

    # Open the output pdf file
    os.startfile(outfile.replace('/', '\\'))


if __name__ == '__main__':
    start_time = time.time()
    main()
    print "--------"
    print "Program execution time: %s seconds" % (time.time() - start_time)
