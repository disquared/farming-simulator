#-------------------------------------------------------------------------------
# Name:        event.py

# Author:      Di Di (ddi0168@gmail.com)
#
# Created:     4/12/13
# Copyright:   (c) Di Di 2013
#-------------------------------------------------------------------------------

import eventprofiler as eprofiler # avoid namespace conflict with 'ep'

class Event:

    def __init__(self, event_name):
        self.event_name = event_name

    def find_events(self, symbols, data, benchmark):
        try:
            event_func = getattr(eprofiler, self.event_name)
        except AttributeError:
            print "[ERROR] {event.py} %s not found!" % self.event_name
            return
        else:
            print "Finding events for: " + self.event_name
            return event_func(symbols, data, benchmark)
