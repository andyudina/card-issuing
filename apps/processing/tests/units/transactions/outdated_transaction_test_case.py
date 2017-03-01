import datetime
import decimal

from apps.processing.models.transactions import Transaction, \
                                                TRANSACTION_PRESENTMENT_STATUS, \
                                                TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS
from utils.tests import TransactionBaseTestCase


class RollbackNonPresentmentTransaction(TransactionBaseTestCase):

    '''
    Test for rolling back because of TTL
    '''

    def setUp(self):
        # now it is essential to constract tomorrow obj before transaction
        # to fit into selection interval. which is not good -> TODO
        self.tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        self.user_account = self.create_account_with_amount()
        self.arrange_amounts()
        # create authorization transactions
        self.arrange_authorization_transactions()
        # create representment transaction
        self.arrange_presentment_transaction()

    ##
    # Helpers
    ##

    # Arrangements for better readability
    def arrange_amounts(self):
        self.base_amount = self.user_account.base_account.amount
        self.transfer_amount = decimal.Decimal(0.2) * self.base_amount

    def arrange_authorization_transactions(self):
        self.transactions_number = 3
        self.transactions = [
            self.create_transaction(
                from_account=self.user_account.base_account,
                to_account=self.user_account.reserved_account,
                amount=self.transfer_amount)
            for i in range(self.transactions_number)]
        self.transaction_for_double_rollback = self.transactions[1]
        self.transaction_for_valid_rollback = self.transactions[2]

    def arrange_presentment_transaction(self):
        self.create_transaction(
             code=self.transactions[0].code,
             status=TRANSACTION_PRESENTMENT_STATUS,
             amount=self.transfer_amount)
        self.not_presented_transaction_codes = {transaction.code: 1 
                                                for transaction in self.transactions[1:]}
        self.base_amount_after_initial_transactions = \
             self.base_amount - self.transactions_number * self.transfer_amount
        self.reserved_amount_after_initial_transactions = \
             self.transactions_number * self.transfer_amount


    # Shortcuts for tested method calls

    def create_valid_rollback(self):
        return Transaction.objects.rollback_late_presentment(
                                   self.transaction_for_valid_rollback.code)

    def dublicate_rollback(self):
        self.create_transaction(
            code=self.transaction_for_double_rollback.code,
            status=TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS
        )
        Transaction.objects.rollback_late_presentment(
                            self.transaction_for_double_rollback.code)

    ##
    # Tests
    ##
    def test__get_transactions_for_rollback__all_transactions_returned(self):
        transaction_codes = Transaction.objects.get_non_presented_transactions_before(self.tomorrow)
        transaction_codes = {code: 1 for code in transaction_codes}
        self.assertDictEqual(transaction_codes, self.not_presented_transaction_codes)

    def test__double_rollback__base_amount_not_modified(self):
        self.dublicate_rollback()
        self.assertAlmostEqual(
            self.user_account.base_account.amount, self.base_amount_after_initial_transactions)

    def test__double_rollback__reserved_amount_not_modified(self):
        self.dublicate_rollback()
        self.assertAlmostEqual(
            self.user_account.reserved_account.amount, self.reserved_amount_after_initial_transactions)

    def test__valid_rollback_rollbacked__base_amount_increased(self):
        self.create_valid_rollback()
        self.check_account_result_amount(
             self.user_account.base_account.id, self.base_amount_after_initial_transactions + self.transfer_amount)

    def test__valid_rollback_rollbacked__reserved_amount_deducted(self):
        self.create_valid_rollback()
        self.check_account_result_amount(
             self.user_account.reserved_account.id, self.transfer_amount * (self.transactions_number - 1))

    def test__valid_rollback_rollbacked__base_transfer_exists(self):
        transaction = self.create_valid_rollback()
        self.check_transfer_exists(
             self.user_account.base_account.id, 
             self.transfer_amount,
             transaction.id)

    def test__valid_rollback_rollbacked__reserved_transfer_exists(self):
        transaction = self.create_valid_rollback()
        self.check_transfer_exists(
             self.user_account.reserved_account.id, 
             -self.transfer_amount,
             transaction.id)

        