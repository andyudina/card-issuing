'''Misc utils'''

import base64
import datetime
from json import loads, dumps
import time


def timestamp_to_datetime(ts):
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
    date = timestamp_to_datetime(ts)
    return to_start_day(date)


def is_in_future(ts):
    '''
    Checks if timestamp is in the future
    '''
    return timestamp_to_datetime(ts) > datetime.datetime.now()


def datetime_to_timestamp(dt):
    '''
    Shortcut for transforming datetime object to ts
    '''
    return time.mktime(dt.timetuple())

def almost_equal(value_1, value_2, accuracy=10**-4, precision=4):
    '''
    Helper for compairing decimals.
    Used in custom assertIn for unit tests
    '''
    diff = round(value_1, precision) - round(value_2, precision)
    return abs(diff) < accuracy


def to_dict(input_ordered_dict):
    '''
    Coverts ordered dict to dict
    '''
    return loads(dumps(input_ordered_dict))


def dict_to_base64(dict_to_convert):
    '''
    Convert dict as base64 string
    '''
    if not dict_to_convert:
        return ''
    # convert all values to its str representatation
    dict_to_convert = {key: str(value)
                       for key, value in dict_to_convert.items()}
    return base64.b64encode(
        dumps(dict_to_convert).encode('utf-8')).\
        decode('ascii')
