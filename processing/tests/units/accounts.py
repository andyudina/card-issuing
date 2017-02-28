import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from django.core.exceptions import ObjectDoesNotExist
from processing.models.accounts import UserAccountsUnion, \
                                       REVENUE_ACCOUNT_ROLE
from processing.models.transactions import TRANSACTION_AUTHORIZATION_STATUS, \
                                           TRANSACTION_LOAD_MONEY_STATUS
from card_issuing_excercise.utils import datetime_to_timestamp, to_start_day
from card_issuing_excercise.utils.tests import CreateAccountMixin, \
                                               CreateTransactionMixin

class CreateNewAccTestCase(CreateAccountMixin, TestCase):

    '''
    Test account creation logic
    '''

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()

    def test__create_new_user_basic_account(self):
        account = UserAccountsUnion.objects.create(user=self.user, id='TESTID')
        self._test_account_has_link(account, 'b')
        self._test_account_has_link(account, 'r')
        self._test_account_has_proper_links_number(account, 2)

    def test__create_special_account__success(self):
        self.create_root_user()
        account = self._create_revenue_account()
        self.assertEqual(account.role, REVENUE_ACCOUNT_ROLE)
 
    def test__create_special_account__owned_by_superuser(self):
        self.create_root_user()
        account = self._create_revenue_account()
        self.assertEqual(account.user.username, 'root')

    def test__create_duplicate_special_account__new_not_created(self):
        self.create_root_user()
        self._create_revenue_account()
        self._create_revenue_account()
        self.assertEqual(
            UserAccountsUnion.objects.filter(role=REVENUE_ACCOUNT_ROLE).count(), 1)

    def test__create_special_account__root_does_not_exist(self):
        with self.assertRaises(ValueError):
            self._create_revenue_account()

    def test__create_new_user_account_with_specified_type(self):
        account = UserAccountsUnion.objects.create(user=self.user, id='TESTID2', 
                                                   linked_account_types=['b',])
        self._test_account_has_link(account, 'b')
        self._test_account_has_proper_links_number(account, 1)

    def _test_account_has_link(self, user_account, link_type):
        self.assertTrue(user_account.accounts.filter(account_type=link_type).exists())

    def _test_account_has_proper_links_number(self, user_account, links_number):
        self.assertEqual(user_account.accounts.count(), links_number)

    def _create_revenue_account(self):
        return UserAccountsUnion.objects.\
                                 create_special_account(REVENUE_ACCOUNT_ROLE)


class GetAccountForUpdate(CreateAccountMixin, TestCase):

    '''
    Kind of smoke test for select_for_update account logic
    '''

    @classmethod
    def setUpTestData(cls):
        cls.account = cls.create_account()

    def test__get_account_for_update(self):
        # actually smoke test that everything works - we can't check if django orm
        # really did select for update or not
        account = UserAccountsUnion.objects.get_account_for_update(self.account.id)
        self.assertEqual(account.id, self.account.id)


class GetUserBalance(CreateAccountMixin, CreateTransactionMixin, TestCase):

    '''
    Test user balance method, which returns tuple of two fields: 
    - total_balance (available + reserved)
    - available_balance
    '''

    @classmethod
    def setUpTestData(cls):
        cls.base_balance = 10.0
        cls.reserved_balance = 5.0

        cls.today = to_start_day(datetime.datetime.now())
        cls.yesterday = cls.today - datetime.timedelta(days=1)
        cls.day_before_yesterday = cls.yesterday - datetime.timedelta(days=1)

        cls.user_account = cls.create_account(cls.day_before_yesterday)
        cls.user_account.accounts.filter(account_type='b').update(amount=cls.base_balance)
        cls.user_account.accounts.filter(account_type='r').update(amount=cls.reserved_balance)
        
        cls.base_account = cls.user_account.accounts.filter(account_type='b').first()
        cls.reserved_account = cls.user_account.accounts.filter(account_type='r').first()
        # emulate load data transaction
        cls.add_transfer(transaction_code='TEST1', status=TRANSACTION_LOAD_MONEY_STATUS,
                         account=cls.base_account, amount=15.0,
                         datetime=cls.day_before_yesterday + datetime.timedelta(hours=1))
        # emulate authorization transaction for the firts usage day
        cls.add_transfer(transaction_code='TEST2', status=TRANSACTION_AUTHORIZATION_STATUS,
                         account=cls.base_account, amount=-2.5,
                         datetime=cls.day_before_yesterday + datetime.timedelta(hours=3))
        cls.add_transfer(transaction_code='TEST2', status=TRANSACTION_AUTHORIZATION_STATUS,
                         account=cls.reserved_account, amount=2.5,
                         datetime=cls.day_before_yesterday + datetime.timedelta(hours=3))
        # emulates authorization transaction for the second usage day
        cls.add_transfer(transaction_code='TEST3', status=TRANSACTION_AUTHORIZATION_STATUS,
                          account=cls.base_account, amount=-2.5,
                          datetime=cls.yesterday + datetime.timedelta(hours=1))
        cls.add_transfer(transaction_code='TEST3', status=TRANSACTION_AUTHORIZATION_STATUS,
                          account=cls.reserved_account, amount=2.5,
                          datetime=cls.yesterday + datetime.timedelta(hours=1))
        # create logs for yesterday
        cls.base_account.account_logs.create(date=cls.yesterday.date(),
                                             amount=12.5)
        cls.reserved_account.account_logs.create(date=cls.yesterday.date(),
                                                 amount=2.5)       


    def test__get_current_balance(self):
        self.assertTupleEqual(
            self.user_account.get_amounts_for_ts(),
            (15.0, 10.0))
 
    def test__get_past_balance(self):
        self.assertTupleEqual(
            self.user_account.get_amounts_for_ts(
                datetime_to_timestamp(self.yesterday + datetime.timedelta(hours=2))
            ),
            (15.0, 10.0))

    def test__get_past_balance_for_first_usage_day(self):
        self.assertEqual(
            self.user_account.get_amounts_for_ts(
                datetime_to_timestamp(self.day_before_yesterday + datetime.timedelta(hours=4))
            ),
            (15.0, 12.5))
