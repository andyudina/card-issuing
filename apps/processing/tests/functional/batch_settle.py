import datetime
import decimal

from django.core.management import call_command

from apps.processing.models.transactions import Transaction, \
                                                TRANSACTION_PRESENTMENT_STATUS
from apps.processing.models.transfers import Transfer
from card_issuing_excercise.settings import AUTHORISATION_TRANSACTION_TTL
from utils import to_start_day
from utils.tests import TransactionBaseTestCase


class SettlementTestCase(TransactionBaseTestCase):
   
    '''
    Functional test for ettlement management.
    Checks transfers from settlement account to "outer" Schema account and
    that all outdated transactions were rollbacked
    '''

    def setUp(self):
        self.arrange_accounts()
        self.arrange_amounts()

    ##
    # Helpers
    ##

    # Arrangements

    def arrange_accounts(self):
        self.sender_account = self.create_account_with_amount()
        self.settlement_account = self.create_settlement_account()

    def arrange_amounts(self):
        self.external_settlement_account = self.create_external_settlement_account()
        self.base_amount = self.sender_account.base_account.amount
        self.reserved_amount = self.sender_account.reserved_account.amount
        self.transfer_amount = decimal.Decimal(0.3) * self.base_amount

    def make_arrangements_for_settlement_check(self):
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
            to_account=self.settlement_account.base_account)

    def make_arrangements_for_rollback_check(self): 
        '''
        Prepares data for rollback check
        '''
        date_to_exceed_ttl = self.construct_outdated_transaction_date()
        self.outdated_authorization_transaction = self.create_transaction(
            created_at=date_to_exceed_ttl,
            from_account=self.sender_account.base_account,
            to_account=self.sender_account.reserved_account,
            amount=self.transfer_amount)

    def construct_outdated_transaction_date(self):
        '''
        Helper for constructiong outdated transaction date
        '''
        date_to_exceed_ttl = to_start_day(
             datetime.datetime.now() - \
             datetime.timedelta(days=AUTHORISATION_TRANSACTION_TTL))
        return date_to_exceed_ttl - datetime.timedelta(hours=12)

    ##
    # Tests
    ##

    def test__settlements_were_transfered__settlement_amount_deducted(self):
        self.make_arrangements_for_settlement_check()
        call_command('batch_settle')
        self.check_account_result_amount(
            self.settlement_account.base_account.id, 0.0)

    def test__outdated_transaction_rollback__base_amount_increased(self):
        self.make_arrangements_for_rollback_check()
        call_command('batch_settle')
        self.check_account_result_amount(
            self.sender_account.base_account.id, self.base_amount)

    def test__outdated_transaction_rollback__reserved_amount_deducted(self):
        self.make_arrangements_for_rollback_check()
        call_command('batch_settle')
        self.check_account_result_amount(
            self.sender_account.reserved_account.id, 0.0)


