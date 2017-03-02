'''Tests presentment transaction creation'''

import decimal
from unittest import skip

from apps.processing.models.transactions import Transaction, IssuerTransactionError, \
                                                TRANSACTION_PRESENTMENT_STATUS
from utils.tests import TransactionBaseTestCase


class PresentmentTransaction(TransactionBaseTestCase):

    '''
    Test for presentment transaction creation
    '''

    def setUp(self):
        self.arrange_accounts()
        self.arrange_amounts()
        self.arrange_authirzation_transaction()

    ##
    # Helpers
    ##

    # Arrangements for better readability

    def arrange_accounts(self):
        self.sender_account = self.create_account_with_amount()
        self.reciever_account = self.create_account()
        self.revenue_account = self.create_account()
        self.settlement_coeff = decimal.Decimal(0.7)

    def arrange_amounts(self):
        self.base_amount = self.sender_account.base_account.amount
        self.transfer_amount = decimal.Decimal(0.5) * self.sender_account.base_account.amount

    def arrange_authirzation_transaction(self):
        self.authoriazation_transaction = self.create_transaction(
            from_account=self.sender_account.base_account,
            to_account=self.sender_account.reserved_account,
            amount=self.transfer_amount)

    # Transaction creation shortcuts

    def create_valid_transaction_without_revenue(self):
        return Transaction.objects.present_transaction(
            self.authoriazation_transaction.code, self.transfer_amount, 
            self.transfer_amount,
            from_account=self.sender_account.base_account,
            to_account=self.reciever_account.base_account)

    def create_valid_transaction_with_revenue(self):
        return  Transaction.objects.present_transaction(
            self.authoriazation_transaction.code, 
            self.transfer_amount, 
            self.settlement_coeff * self.transfer_amount,
            from_account=self.sender_account.base_account,
            to_account=self.reciever_account.base_account,
            extra_account=self.revenue_account.base_account)

    def duplicate_transaction(self):
        self.create_transaction(
            code=self.authoriazation_transaction.code, 
            amount=self.transfer_amount,
            status=TRANSACTION_PRESENTMENT_STATUS,
            from_account=self.sender_account.base_account,
            to_account=self.reciever_account.base_account)
        Transaction.objects.present_transaction(
            self.authoriazation_transaction.code, 
            self.transfer_amount, self.transfer_amount,
            from_account=self.sender_account.base_account,
            to_account=self.reciever_account.base_account)

    # valid transaction without revenue

    def test__valid_transaction__without_extra_transfers__sender_amount_modified(self):
        self.create_valid_transaction_without_revenue()
        self.check_account_result_amount(
             self.sender_account.base_account.id, self.base_amount - self.transfer_amount)

    def test__valid_transaction__without_extra_transfers__reciever_amount_modified(self):
        self.create_valid_transaction_without_revenue()
        self.check_account_result_amount(
             self.reciever_account.base_account.id, self.transfer_amount)

    def test__valid_transaction__without_extra_transfers__sender_transfer_exists(self):
        transaction = self.create_valid_transaction_without_revenue()
        self.check_transfer_exists(
             self.sender_account.base_account.id, 
             -self.transfer_amount,
             transaction.id)

    def test__valid_transaction__without_extra_transfers__reciever_transfer_exists(self):
        transaction = self.create_valid_transaction_without_revenue()
        self.check_transfer_exists(
             self.reciever_account.base_account.id, 
             self.transfer_amount,
             transaction.id)

    # valid transaction with revenue

    def test__valid_transaction__with_extra_transfer__sender_amount_modified(self):
        self.create_valid_transaction_with_revenue()
        self.check_account_result_amount(
             self.sender_account.base_account.id, 
             self.base_amount - self.transfer_amount)

    def test__valid_transaction__with_extra_transfer__reciever_amount_modified(self):
        self.create_valid_transaction_with_revenue()
        self.check_account_result_amount(
             self.reciever_account.base_account.id, 
             self.transfer_amount * self.settlement_coeff)

    def test__valid_transaction__with_extra_transfer__revenue_acc_amount_modified(self):
        self.create_valid_transaction_with_revenue()
        self.check_account_result_amount(
             self.revenue_account.base_account.id, 
             self.transfer_amount * (1 - self.settlement_coeff))

    def test__valid_transaction__with_extra_transfer__sender2reciever_transfer_exists(self):
        transaction = self.create_valid_transaction_with_revenue()
        self.check_transfer_exists(
             self.sender_account.base_account.id, 
             -self.transfer_amount * self.settlement_coeff,
             transaction.id)

    def test__valid_transaction__with_extra_transfer__sender2revenue_acc_transfer_exists(self):
        transaction = self.create_valid_transaction_with_revenue()
        self.check_transfer_exists(
             self.sender_account.base_account.id, 
             -self.transfer_amount * (1 - self.settlement_coeff),
             transaction.id)

    def test__valid_transaction__with_extra_transfer__reciever_transfer_exists(self):
        transaction = self.create_valid_transaction_with_revenue()
        self.check_transfer_exists(
             self.reciever_account.base_account.id, 
             self.transfer_amount * self.settlement_coeff,
             transaction.id)

    def test__valid_transaction__with_extra_transfer__revenue_acc_transfer_exists(self):
        transaction = self.create_valid_transaction_with_revenue()
        self.check_transfer_exists(
             self.revenue_account.base_account.id, 
             self.transfer_amount * (1 - self.settlement_coeff),
             transaction.id)

    def test__duplicate_transaction_raises_error(self):
        with self.assertRaises(IssuerTransactionError) as err_cm:
            self.duplicate_transaction()
        err = err_cm.exception
        self.assertEqual(err.args[0], Transaction.Errors.ALREADY_DONE)

    # it is better to check if modified only once
    # TODO: change amounts in test transactions
    # before this fix test is not correct and should be skipped
    @skip('incorrect testing mechanism')
    def test__duplicate_transaction__sender_amount_not_modified(self):
        try:
            self.duplicate_transaction()
        except IssuerTransactionError:
            pass
        self.check_account_result_amount(
             self.sender_account.base_account.id, 
             self.base_amount - self.transfer_amount)

    def test__duplicate_transaction__reciever_amount_modified_not_modified(self):
        try:
            self.duplicate_transaction()
        except IssuerTransactionError:
            pass
        self.check_account_result_amount(
             self.reciever_account.base_account.id, self.transfer_amount)

