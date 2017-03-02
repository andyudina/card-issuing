''' Tests account getters'''

from django.test import TestCase

from apps.processing.models.accounts import UserAccountsUnion
from utils.tests import CreateAccountMixin


class GetAccount(CreateAccountMixin,
                 TestCase):

    '''
    Tests account getters and
    smoke test for select_for_update account logic
    '''

    def setUp(self):
        self.account = self.create_account()

    def test__get_account_for_update(self):
        # actually smoke test that everything works - we can't check if django orm
        # really did select for update or not
        account = UserAccountsUnion.objects.\
            get_account_for_update(self.account.id)
        self.assertEqual(account.id, self.account.id)

    def test__get_valid_special_account__exists(self):
        self.create_revenue_account()
        account = UserAccountsUnion.objects.get_revenue_account()
        self.assertIsNotNone(account)

    def test__get_invalid_special_account__none_returned(self):
        account = UserAccountsUnion.objects.\
            get_special_account_or_none('INVALID')
        self.assertIsNone(account)

    def test__get_valid_special_account_not_created_yet__none_returned(self):
        account = UserAccountsUnion.objects.\
            get_external_load_money_account()
        self.assertIsNone(account)
