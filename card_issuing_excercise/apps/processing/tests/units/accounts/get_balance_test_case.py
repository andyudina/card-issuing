'''Tests user balance getter in different time points'''

import datetime

from django.test import TestCase

from card_issuing_excercise.apps.processing.models.accounts import \
    BASIC_ACCOUNT_TYPE, \
    REVENUE_ACCOUNT_ROLE
from card_issuing_excercise.apps.processing.models.transactions import \
    TRANSACTION_AUTHORIZATION_STATUS, \
    TRANSACTION_LOAD_MONEY_STATUS
from card_issuing_excercise.apps.utils import \
    datetime_to_timestamp, \
    to_start_day
from card_issuing_excercise.apps.utils.tests import CreateAccountMixin, \
    CreateTransactionMixin


class GetUserBalance(CreateAccountMixin,
                     CreateTransactionMixin, TestCase):

    '''
    Tests user amount method, which returns tuple of two fields: 
    - total_amount (available + reserved)
    - available_amount
    '''

    def setUp(self):
        self.arrange_amounts()
        self.arrange_dates()
        self.arrange_accounts()
        # arrange transactions
        self.create_load_data_transaction()
        self.create_auth_transaction_for_first_day()
        self.create_auth_transaction_for_second_day()
        self.create_account_logs_for_yesterday()

    ##
    # Heplers
    ##

    # Arrangements

    def arrange_amounts(self):
        self.base_amount = 10.0
        self.reserved_amount = 5.0
        self.transfer_amount = 2.5

    def arrange_dates(self):
        self.today = to_start_day(datetime.datetime.now())
        self.yesterday = self.get_day_before(self.today)
        self.day_before_yesterday = self.get_day_before(self.yesterday)

    def arrange_accounts(self):
        # construct accounts
        self.user_account = self.create_account(self.day_before_yesterday)
        self.update_account_amount(BASIC_ACCOUNT_TYPE, self.base_amount)
        self.update_account_amount(REVENUE_ACCOUNT_ROLE, self.reserved_amount)
        # shortcuts to accounts
        self.base_account = self.user_account.base_account
        self.reserved_account = self.user_account.reserved_account

    def create_load_data_transaction(self):
        self.add_transfer(transaction_code='LTEST',
                          status=TRANSACTION_LOAD_MONEY_STATUS,
                          account=self.base_account,
                          amount=self.base_amount + self.reserved_amount,
                          datetime=self.day_before_yesterday +
                          datetime.timedelta(hours=1))

    def create_auth_transaction_for_first_day(self):
        '''
        Creates transaction at the first usage day
        For testing past amount without logs
        '''
        transaction_code = 'A1TEST'
        transaction_created_at = self.day_before_yesterday + \
            datetime.timedelta(hours=3)
        self.add_transfer(transaction_code=transaction_code,
                          status=TRANSACTION_AUTHORIZATION_STATUS,
                          account=self.base_account,
                          amount=-self.transfer_amount,
                          datetime=transaction_created_at)
        self.add_transfer(transaction_code=transaction_code,
                          status=TRANSACTION_AUTHORIZATION_STATUS,
                          account=self.reserved_account,
                          amount=self.transfer_amount,
                          datetime=transaction_created_at)

    def create_auth_transaction_for_second_day(self):
        '''
        Creates transaction at the second usage day
        For testing past amount with logs
        '''
        transaction_code = 'A2TEST'
        transaction_created_at = self.yesterday + datetime.timedelta(hours=1)
        self.add_transfer(transaction_code=transaction_code,
                          status=TRANSACTION_AUTHORIZATION_STATUS,
                          account=self.base_account,
                          amount=-self.transfer_amount,
                          datetime=transaction_created_at)
        self.add_transfer(transaction_code=transaction_code,
                          status=TRANSACTION_AUTHORIZATION_STATUS,
                          account=self.reserved_account,
                          amount=self.transfer_amount,
                          datetime=transaction_created_at)

    def create_account_logs_for_yesterday(self):
        log_date = self.yesterday.date()
        self.base_account.account_logs.create(
            date=log_date,
            amount=self.transfer_amount + self.base_amount)
        self.reserved_account.account_logs.create(
            date=log_date, amount=self.transfer_amount)

    # Shortcuts

    def update_account_amount(self, acc_type, amount):
        '''
        Shortcut for account update
        '''
        self.user_account.accounts.\
            filter(account_type=acc_type).\
            update(amount=amount)

    def get_day_before(self, date):
        '''
        Get day before date in args 
        '''
        return date - datetime.timedelta(days=1)

    def get_total_amount(self, amounts_tuple):
        '''
        Shortcut for total amount
        '''
        return amounts_tuple[0]

    def get_available_amount(self, amounts_tuple):
        '''
        Shortcut for available amount 
        '''
        return amounts_tuple[1]

    def get_past_amount_for_second_day(self):
        '''
        Shortcut for amount for second usage day
        '''
        first_day_ts = datetime_to_timestamp(
            self.yesterday + datetime.timedelta(hours=2))
        return self.user_account.get_amounts_for_ts(first_day_ts)

    def get_past_amount_for_first_day(self):
        '''
        Shortcut for amount for firts usage day
        '''
        second_day_ts = datetime_to_timestamp(
            self.day_before_yesterday + datetime.timedelta(hours=4))
        return self.user_account.get_amounts_for_ts(second_day_ts)

    ##
    # Tests
    ##

    def test__get_current_amount__total_amount_is_ok(self):
        amount_tuple = self.user_account.get_amounts_for_ts()
        self.assertEqual(
            self.get_total_amount(amount_tuple), 15.0)

    def test__get_current_amount__available_amount_is_ok(self):
        amount_tuple = self.user_account.get_amounts_for_ts()
        self.assertEqual(
            self.get_available_amount(amount_tuple), 10.0)

    def test__get_past_amount__total_amount_is_ok(self):
        amount_tuple = self.get_past_amount_for_second_day()
        self.assertEqual(
            self.get_total_amount(amount_tuple), 15.0)

    def test__get_past_amount__available_amount_is_ok(self):
        amount_tuple = self.get_past_amount_for_second_day()
        self.assertEqual(
            self.get_available_amount(amount_tuple), 10.0)

    def test__get_past_amount_for_first_usage_day__total_amount_is_ok(self):
        amount_tuple = self.get_past_amount_for_first_day()
        self.assertEqual(
            self.get_total_amount(amount_tuple), 15.0)

    def test__get_past_amount_for_first_usage_day__available_amount_is_ok(self):
        amount_tuple = self.get_past_amount_for_first_day()
        self.assertEqual(
            self.get_available_amount(amount_tuple), 12.5)
