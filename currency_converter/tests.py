''' Stub module for converter unit tests '''

import unittest


class ConverterTestCase(unittest.TestCase):

    '''Stub test case for converter'''

    def setUp(self):
        # mock external service
        # mock apis for alarm
        # mock cache
        pass

    def test__convertation__different_currencies_is_ok(self):
        pass

    def test__convertation__same_currency_is_ok(self):
        pass

    def test__convertation_rate__from_api_is_ok(self):
        pass

    def test__api_is_down__send_alarm(self):
        pass

    def test__api_is_down__raise_error(self):
        pass

    def test__take_rate_from_cache__is_ok(self):
        pass

    def test__invalid_currency__alarm(self):
        pass
