'''
Stub for "cache_accounts_balance" management command test case
Checks if command can be run only at specific time interval and saves
proper balances for all presented accounts
'''

from django.test import TestCase


class CacheAccountsBalance(TestCase):

    '''
    Stub for "cache_accounts_balance" management command test case
    '''

    def test__already_processed__fail_silently(self):
        pass

    def test__valid_run__all_balances_saved(self):
        pass

    def test__valid_run__proper_balance_saved(self):
        pass
