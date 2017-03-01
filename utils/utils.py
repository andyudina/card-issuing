import datetime
from json import loads, dumps
import time

#TODO: names with datetime_to_timestamp should be symmetrical
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

# TODO: refactor layout
def almost_equal(value_1, value_2, accuracy=10**-4, precision=4):
    '''
    Helper for compairing decimals.
    Used in custom assertIn for unit tests
    '''
    return abs(
        round(value_1, precision) - round(value_2, precision)) < accuracy


def to_dict(input_ordered_dict):
    '''
    Coverts ordered dict to dict
    '''
    return loads(dumps(input_ordered_dict))