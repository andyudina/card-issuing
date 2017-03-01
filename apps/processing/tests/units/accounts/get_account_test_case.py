import datetime

from django.test import TestCase

from apps.processing.models.accounts import UserAccountsUnion
from utils.tests import CreateAccountMixin


class GetAccountForUpdate(CreateAccountMixin, 
                          TestCase):

    '''
    Kind of smoke test for select_for_update account logic
    '''

    def setUp(self):
        self.account = self.create_account()

    def test__get_account_for_update(self):
        # actually smoke test that everything works - we can't check if django orm
        # really did select for update or not
        account = UserAccountsUnion.objects.\
                                    get_account_for_update(self.account.id)
        self.assertEqual(account.id, self.account.id)


