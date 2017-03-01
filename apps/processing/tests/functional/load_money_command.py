from django.core.management import call_command
from django.test import TestCase

from utils.tests import CreateAccountMixin, \
                        TestTransactionMixin

# TODO: embedd currency exchange into architecture!
# TODO: cover currency exchange with tests!
# TODO: create accounts on the flight?
# TODO: to many errors without it
class LoadMoneyCommandTestCase(CreateAccountMixin,
                               TestTransactionMixin, TestCase):
   
    '''
    Functional test for load money management command.
    Checks transfer from "outer" source and that user amount was increased
    '''

    def setUp(self):
        self.user_account = self.create_account()
        self.create_root_user()
        self.create_load_money_account()
    
    def test__user_base_amount_increased(self):
        load_money_amount = 10.0
        call_command('load_money', self.user_account.card_id, load_money_amount, 'EUR')
        self.check_account_result_sum(
            self.user_account.base_account.id, load_money_amount)

    ## currency tests - not implemented
    def test__currency_exchanged__successfull(self):
        pass

    def test__currency_api_is_down__get_500(self):
        pass
