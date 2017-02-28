import datetime
import decimal

from django.core.management import call_command
from django.test import TestCase

from processing.models.transactions import Transaction, \
                                           TRANSACTION_PRESENTMENT_STATUS
from processing.models.transfers import Transfer
from card_issuing_excercise.utils import to_start_day
from card_issuing_excercise.utils.tests import CreateAccountMixin, \
                                               CreateTransactionMixin, \
                                               TestTransactionMixin
from card_issuing_excercise.settings import AUTHORISATION_TRANSACTION_TTL


#TODO: remove unnesessary calls from setUp
class SettlementTestCase(CreateAccountMixin, CreateTransactionMixin,
                         TestTransactionMixin, TestCase):
   
    '''
    Functional settlement management command.
    Checks transfers from settlement account to "outer" Schema account and
    that all outdated transactions were rollbacked
    '''

    def setUp(self):
        self.create_root_user()
        self.sender_account = self.create_account_with_amount()
        self.settlement_account = self.create_settlement_account()
        self.external_settlement_account = self.create_external_settlement_account()
        self.base_amount = self.sender_account.base_account.amount
        self.reserved_amount = self.sender_account.reserved_account.amount
        self.transfer_amount = decimal.Decimal(0.3) * self.base_amount

    def _arrange_for_settlement_check(self):
        '''
        Prepares data for settlement test
        '''
        self.authorization_transaction = self.create_transaction(
            from_account=self.sender_account.base_account,
            to_account=self.sender_account.reserved_account,
            amount=self.transfer_amount)
        self.presentment_transaction = self.create_transaction(
            code=self.authorization_transaction.code, amount=self.transfer_amount,
            status=TRANSACTION_PRESENTMENT_STATUS,
            from_account=self.sender_account.base_account,
            to_account=self.settlement_account.base_account,
        )

    def _arrange_for_rollback_check(self): 
        '''
        Prepares data for rollback check
        '''
        date_to_exceed_ttl = self._construct_outdated_transaction_date()
        self.outdated_authorization_transaction = self.create_transaction(
            created_at=date_to_exceed_ttl,
            from_account=self.sender_account.base_account,
            to_account=self.sender_account.reserved_account,
            amount=self.transfer_amount)

    def _construct_outdated_transaction_date(self):
        '''
        Helper for constructiong outdated transaction date
        '''
        date_to_exceed_ttl = to_start_day(
             datetime.datetime.now() - \
             datetime.timedelta(days=AUTHORISATION_TRANSACTION_TTL))
        return date_to_exceed_ttl - datetime.timedelta(hours=12)

    def test__settlements_were_transfered__settlement_amount_deducted(self):
        self._arrange_for_settlement_check()
        call_command('batch_settle')
        self.check_account_result_sum(
            self.settlement_account.base_account.id, 0.0)

    def test__outdated_transaction_rollback__base_amount_increased(self):
        self._arrange_for_rollback_check()
        call_command('batch_settle')
        self.check_account_result_sum(
            self.sender_account.base_account.id, self.base_amount)

    def test__outdated_transaction_rollback__reserved_amount_deducted(self):
        self._arrange_for_rollback_check()
        call_command('batch_settle')
        self.check_account_result_sum(
            self.sender_account.reserved_account.id, 0.0)


