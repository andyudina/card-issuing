from django.core.management import call_command
from django.test import TestCase

from card_issuing_excercise.utils.tests import CreateAccountMixin, \
                                               TestTransactionMixin

# TODO: embedd currency exchange into architecture!
# TODO: cover currency exchange with tests!
class LoadMoneyCommandTestCase(CreateAccountMixin,
                               TestTransactionMixin, TestCase):
   
    '''
    Functional test for load money management command.
    Checks transfer from "outer" source and that user amount was increased
    '''

    def setUp(self):
        self.user_account = self.create_account()
    
    def test__user_base_amount_increased(self):
        load_money_amount = 10.0
        call_command('load_money', self.user_account.id, load_money_amount, 'EUR')
        self.check_account_result_sum(
            self.sender_account.base_account.id, load_money_amount)


