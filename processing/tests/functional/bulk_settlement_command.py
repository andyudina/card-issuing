import datetime

from django.core.management import call_command
from django.test import TestCase

from processing.models.transactions import Transaction, \
                                           TRANSACTION_PRESETMENT_STATUS
from card_issuing_excercise.utils.tests import CreateAccountMixin, \
                                               CreateTransactionMixin, \
                                               TestTransactionMixin
from card_issuing_exercise.settings import AUTHORISATION_TRANSACTION_TTL


#TODO: remove unnesessary calls from setUp
class SettlementTestCase(CreateAccountMixin, CreateTransactionMixin,
                         TestTransactionMixin, TestCase):
   
    '''
    Functional settlement management command.
    Checks transfers from settlement account to "outer" Schema account and
    that all outdated transactions were rollbacked
    '''

    def setUp(self):
        self.sender_account = self.create_account_with_amount()
        self.settlement_account = self.create_settlement_account()
        #self.revenue_account = self.create_revenue_account()
        self.base_amount = self.sender_account.base_account.amount
        self.reserved_amount = self.sender_account.reserved_account.amount
        self.transfer_amount = decimal.Decimal(0.3) * self.base_amount
        #self.real_transfered_amount = Transaction.objects.get_amount_for_reserve(self.transfer_amount)
        #self.settlement_coeff = decimal.Decimal(0.7)
        self.authorization_transaction = self.create_transaction(
            from_account=self.sender_account.base_account,
            to_account=self.sender_account.reserved_account,
            amount=self.transfer_amount)
        self.presentment_transaction = self.create_transaction(
            code=self.transaction.code, amount=self.transfer_amount,
            status=TRANSACTION_PRESETMENT_STATUS,
            from_account=self.sender_account.base_account,
            to_account=self.settlement_account.base_account,
        )
        # create outdates authorization trnasaction for rollback check
        date_to_exceed_ttl = datetime.datetime.now() - datetime.timedelta(days=AUTHORISATION_TRANSACTION_TTL)
        self.outdated_authorization_transaction = self.create_transaction(
            date_to_exceed_ttl,
            from_account=self.sender_account.base_account,
            to_account=self.sender_account.reserved_account,
            amount=self.transfer_amount)

    def test__settlements_were_transfered__settlement_amount_decreased(self):
        call_command('batch_settle')
        self.check_account_result_sum(
            self.settlement_account.base_account.id, 0.0)

    def test__outdated_transaction_rollback__base_amount_increased(self):
        call_command('batch_settle')
        self.check_account_result_sum(
            self.sender_account.base_account.id, self.base_amount - self.transfer_amount)

    def test__outdated_transaction_rollback__reserved_amountdeducted(self):
        call_command('batch_settle')
        self.check_account_result_sum(
            self.sender_account.reserved_account.id, 0.0)


