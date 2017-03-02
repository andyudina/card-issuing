''' Tests trasfer creation '''

from card_issuing_excercise.apps.utils.tests import TransactionBaseTestCase


class TransactionTransferManagement(TransactionBaseTestCase):

    '''
    Test for transfering logic. 
    We want to be sure that trasferings are balanced.
    '''

    def setUp(self):
        self.user_account = self.create_account_with_amount()
        self.base_amount = self.user_account.base_amount
        self.transfer_amount = self.user_account.base_amount
        self.transaction = self.create_transaction()

    ##
    # Helpers
    ##

    def add_transfer(self):
        '''
        Helper for ading transfer to transaction
        '''
        self.transaction.add_transfer(
            self.user_account.base_account,
            self.user_account.reserved_account,
            self.transfer_amount)

    def test__add_transfer__sender_amount_was_decucted(self):
        self.add_transfer()
        self.check_account_result_amount(
            self.user_account.base_account.id,
            self.base_amount - self.transfer_amount)

    def test__add_transfer__sender_transfer_exists(self):
        self.add_transfer()
        self.check_transfer_exists(
            self.user_account.base_account.id,
            -self.transfer_amount,
            self.transaction.id)

    def test__add_transfer__reciever_amount_was_increased(self):
        self.add_transfer()
        self.check_account_result_amount(
            self.user_account.reserved_account.id, self.transfer_amount)

    def test__add_transfer__reciever_transfer_exists(self):
        self.add_transfer()
        self.check_transfer_exists(
            self.user_account.reserved_account.id,
            self.transfer_amount,
            self.transaction.id)
