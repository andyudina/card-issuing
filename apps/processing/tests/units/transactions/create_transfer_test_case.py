from django.test import TestCase

from utils.tests import CreateAccountMixin, CreateTransactionMixin, \
                        TestTransactionMixin


class TransactionTransferManagement(CreateAccountMixin, 
                                    CreateTransactionMixin, 
                                    TestTransactionMixin, TestCase):

    '''
    Test for transfering logic. 
    We want to be sure that trasferings are balanced.
    '''

    def setUp(self):
        self.user_account = self.create_account_with_amount()
        self.base_amount = self.user_account.base_amount
        self.transfer_amount = self.user_account.base_amount
        self.transaction = self.create_transaction()
        print(self.transfer_amount)
        print(self.base_amount)
    ##
    # Helpers
    ##

    def add_transfer(self):
       '''
       Helper for ading transfer to transaction
       '''
       self.transaction.add_transfer(self.user_account.base_account, 
                                     self.user_account.reserved_account, self.transfer_amount)

    def test__add_transfer__sender_amount_was_decucted(self):
        self.add_transfer()
        self.check_successfull_money_transfering(account_id=self.user_account.base_account.id,
            expected_amount=self.base_amount - self.transfer_amount, 
            transaction_id=self.transaction.id, 
            transfer_amount=-self.transfer_amount)

    def test__add_transfer__reciever_amount_was_increased(self):
        self.add_transfer()
        self.check_successfull_money_transfering(account_id=self.user_account.reserved_account.id,
            expected_amount=self.transfer_amount, transaction_id=self.transaction.id,
            transfer_amount=self.transfer_amount)


