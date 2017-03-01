import decimal

from apps.processing.models.transactions import Transaction, \
                                                IssuerTransactionError, \
                                                TRANSACTION_AUTHORIZATION_STATUS

from utils.tests import TransactionBaseTestCase


class AuthorisationTransaction(TransactionBaseTestCase):

    '''
    Test for authorization transaction creation
    '''

    def setUp(self):
        self.user_account = self.create_account_with_amount()
        self.transfer_amount = decimal.Decimal(0.5) * self.user_account.base_account.amount 
        self.base_amount = self.user_account.base_account.amount 
        self.real_transfer_amount = Transaction.objects.\
                                                get_amount_for_reserve(self.transfer_amount)

    ##
    # Helpers
    ##
    def create_valid_transaction(self):
        '''
        Shortcut for valid transaction
        '''
        return Transaction.objects.try_authorise_transaction(
            'VALID', self.transfer_amount,
            from_account=self.user_account.base_account,
            to_account=self.user_account.reserved_account)

    def create_transaction_with_too_big_amount(self):
        '''
        Shortcut for invalid transaction with too big amount
        '''
        Transaction.objects.try_authorise_transaction(
                'TOOMUCH', 3 * self.transfer_amount,
                from_account=self.user_account.base_account,
                to_account=self.user_account.reserved_account)

    def create_duplicate_transaction(self):
        '''
        Shortcut for duplicating transaction
        '''
        trasaction_code = 'DUBLE'
        self.create_transaction(code=trasaction_code, status=TRANSACTION_AUTHORIZATION_STATUS)
        Transaction.objects.try_authorise_transaction(
                trasaction_code, self.transfer_amount,
                from_account=self.user_account.base_account,
                to_account=self.user_account.reserved_account)

    ##
    # Tests
    ##

    def test__valid_transaction__base_amount_deducted(self):
        transaction = self.create_valid_transaction()
        self.check_account_result_amount(
             self.user_account.base_account.id, self.base_amount - self.real_transfer_amount)

    def test__valid_transaction__reserved_amount_increased(self):
        transaction = self.create_valid_transaction()
        self.check_account_result_amount(
             self.user_account.reserved_account.id, self.real_transfer_amount)

    def test__valid_transaction__base_account_transfer_exists(self):
        transaction = self.create_valid_transaction()
        self.check_transfer_exists(
             self.user_account.base_account.id, 
             -self.real_transfer_amount,
             transaction.id)

    def test__valid_transaction__reserved_account_transfer_exists(self):
        transaction = self.create_valid_transaction()
        self.check_transfer_exists(
             self.user_account.reserved_account.id, 
             self.real_transfer_amount,
             transaction.id)

    def test__not_enough_money__error_raised(self):
        with self.assertRaises(IssuerTransactionError) as err_cm:
            self.create_transaction_with_too_big_amount()   
        err = err_cm.exception
        self.assertEqual(err.args[0], Transaction.Errors.NOT_ENOUGH_MONEY)

    def test__not_enough_money__base_amount_not_modified(self):
        try:
            self.create_transaction_with_too_big_amount()
        except IssuerTransactionError:
            pass
        self.check_account_result_amount(
             self.user_account.base_account.id, self.base_amount)

    def test__not_enough_money__reserved_amount_not_modified(self):
        try:
            self.create_transaction_with_too_big_amount()
        except IssuerTransactionError:
            pass
        self.check_account_result_amount(
             self.user_account.reserved_account.id, 0.0)

    def test__already_created__error_raised(self):
        with self.assertRaises(IssuerTransactionError) as err_cm:
            self.create_duplicate_transaction()
        err = err_cm.exception
        self.assertEqual(err.args[0], Transaction.Errors.ALREADY_DONE) 

    # it is better to check if modified only once
    # TODO: change amounts in test transactions
    def test__already_created__base_amount_not_modified(self):
        try:
            self.create_duplicate_transaction()
        except IssuerTransactionError:
            pass
        self.check_account_result_amount(
             self.user_account.base_account.id, self.base_amount)

    def test__already_created__reserved_amount_not_modified(self):
        try:
            self.create_duplicate_transaction()
        except IssuerTransactionError:
            pass
        self.check_account_result_amount(
             self.user_account.reserved_account.id, 0.0)

