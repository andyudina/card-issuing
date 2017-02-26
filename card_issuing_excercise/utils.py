import datetime
import time

def date_from_ts(ts):
    '''
    Shortcut for ts to datetime obj converting
    '''
    return datetime.datetime.fromtimestamp(ts)


def to_start_day(dt):
    '''
    Get datetime of the beginning of the day. 
    Works with datetime object
    '''
    return datetime.datetime.combine(dt, datetime.time.min)


def to_start_day_from_ts(ts):
    '''
    Get datetime of the beginning of the day.
    Works with timesatmps
    '''
    date = date_from_ts(ts)
    return to_start_day(date)


def is_in_future(ts):
    '''
    Checks if timestamp is in the future
    '''
    return date_from_ts(ts) > datetime.datetime.now()


def datetime_to_timestamp(dt):
    '''
    Shortcut for transforming datetime object to ts
    '''
    return time.mktime(dt.timetuple())

