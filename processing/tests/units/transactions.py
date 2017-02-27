import datetime
import decimal

from django.test import TestCase

from processing.models.transactions import Transaction, IssuerTransactionError, \
                                           TRANSACTION_PRESETMENT_STATUS, \
                                           TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS, \
                                           TRANSACTION_AUTHORIZATION_STATUS
from processing.tests.units.utils import CreateAccountMixin, \
                                         CreateTransactionMixin, \
                                         TestTransactionMixin


# TODO: more precise test checks in presentment transactions:
# - test if duplicates occured in the rollback
# - test rolback transferings on success
# - test all transaction codes etc.
# - refactor tests: one seert in one method
# - split test cases into packages
# - cover "transfer_amount" with tests
# - 'already_done' codes as constants
# - cover get_amount_for_reserve  with tests
# - should we sum all deductions insde one transaction?
# - obj setUp or class setUp?
class TransactionTransferManagement(CreateAccountMixin, CreateTransactionMixin, 
                                    TestTransactionMixin, TestCase):

    '''
    Test for transfering logic. 
    We want to be sure that trasferings are balanced.
    '''

    @classmethod
    def setUpTestData(cls):
        cls.user_account = cls.create_account_with_amount()
        cls.transfer_sum = cls.user_account.base_account.amount
        cls.transaction = cls.create_transaction()

    def test__add_transfer(self):
        self.transaction.add_transfer(self.user_account.base_account, 
                                      self.user_account.reserved_account, self.transfer_sum)
        # check base_account amount was deducted
        self.check_successfull_money_transfering(account_id=self.user_account.base_account.id,
            expected_sum=0.0, transaction_id=self.transaction.id, 
            transfer_sum=-self.transfer_sum)
        # check reserved_account amount was added
        self.check_successfull_money_transfering(account_id=self.user_account.reserved_account.id,
            expected_sum=self.transfer_sum, transaction_id=self.transaction.id, 
            transfer_sum=self.transfer_sum)
     

class AuthorisationTransaction(CreateAccountMixin, CreateTransactionMixin, 
                               TestTransactionMixin, TestCase):

    '''
    Test for authorization transaction creation
    '''

    @classmethod
    def setUpTestData(cls):
        cls.user_account = cls.create_account_with_amount()
        cls.transfer_sum = decimal.Decimal(0.5) * cls.user_account.base_account.amount 
        cls.base_amount = cls.user_account.base_account.amount 

    def test__transaction_is_ok(self):
        transaction = Transaction.objects.try_authorise_transaction(
            'TEST1', self.transfer_sum,
            from_account=self.user_account.base_account,
            to_account=self.user_account.reserved_account)
        real_transfer_sum = Transaction.objects.get_amount_for_reserve(self.transfer_sum)
        # check base_account amount was deducted
        self.check_successfull_money_transfering(account_id=self.user_account.base_account.id,
            expected_sum=self.base_amount - real_transfer_sum, transaction_id=transaction.id, 
            transfer_sum=-real_transfer_sum)
        # check reserved_account amount was added
        self.check_successfull_money_transfering(account_id=self.user_account.reserved_account.id,
            expected_sum=real_transfer_sum, transaction_id=transaction.id, 
            transfer_sum=real_transfer_sum)



    def test__not_enough_money(self):
        with self.assertRaises(IssuerTransactionError) as err_cm:
            Transaction.objects.try_authorise_transaction(
                'TEST1', 3 * self.transfer_sum,
                from_account=self.user_account.base_account,
                to_account=self.user_account.reserved_account)

        err = err_cm.exception
        self.assertEqual(err.args[0], 'not_enough_money')

    def test__already_created(self):
        trasaction_code = 'TEST'
        self.create_transaction(code=trasaction_code, status=TRANSACTION_AUTHORIZATION_STATUS)
        with self.assertRaises(IssuerTransactionError) as err_cm:
            Transaction.objects.try_authorise_transaction(
                trasaction_code, self.transfer_sum,
                from_account=self.user_account.base_account,
                to_account=self.user_account.reserved_account)

        err = err_cm.exception
        self.assertEqual(err.args[0], 'already_done')        


class PresentmentTransaction(CreateAccountMixin, CreateTransactionMixin, 
                             TestTransactionMixin, TestCase):

    '''
    Test for presentment transaction creation
    '''

    def setUp(self):
        self.user_account_1 = self.create_account_with_amount()
        self.user_account_2 = self.create_account()
        self.revenue_account = self.create_account()
        self.base_sum = self.user_account_1.base_account.amount
        self.transfer_sum = decimal.Decimal(0.5) * self.user_account_1.base_account.amount
        self.transaction = self.create_transaction(
            from_account=self.user_account_1.base_account,
            to_account=self.user_account_1.reserved_account,
            amount=self.transfer_sum,
        )

    def test__transaction_is_ok__without_extra_transfers(self):
        transaction = Transaction.objects.present_transaction(
            self.transaction.code, self.transfer_sum, self.transfer_sum,
            from_account=self.user_account_1.base_account,
            to_account=self.user_account_2.base_account,
        )
        # check user_1 base amount was deducted
        self.check_successfull_money_transfering(account_id=self.user_account_1.base_account.id,
            expected_sum=self.base_sum - self.transfer_sum, transaction_id=transaction.id, 
            transfer_sum=-self.transfer_sum)
        # check user_2 base amount was added
        self.check_successfull_money_transfering(account_id=self.user_account_2.base_account.id,
            expected_sum=self.transfer_sum, transaction_id=transaction.id, 
            transfer_sum=self.transfer_sum)
        #TODO: check reserved account amount is 0

    def test__transaction_is_ok__with_extra_transfers(self):
        settlement_coeff = decimal.Decimal(0.7)
        transaction = Transaction.objects.present_transaction(
            self.transaction.code, self.transfer_sum, settlement_coeff * self.transfer_sum,
            from_account=self.user_account_1.base_account,
            to_account=self.user_account_2.base_account,
            extra_account=self.revenue_account.base_account
        )
        # check user_1 base amount was deducted
        # deduction for base payment
        self.check_successfull_money_transfering(account_id=self.user_account_1.base_account.id,
            expected_sum=self.base_sum - self.transfer_sum, transaction_id=transaction.id, 
            transfer_sum=-settlement_coeff * self.transfer_sum)
        # dedcution for revenue payment
        self.check_successfull_money_transfering(account_id=self.user_account_1.base_account.id,
            expected_sum=self.base_sum - self.transfer_sum, transaction_id=transaction.id, 
            transfer_sum=-(1 - settlement_coeff) * self.transfer_sum)
        # check user_2 base amount was added
        self.check_successfull_money_transfering(account_id=self.user_account_2.base_account.id,
            expected_sum=settlement_coeff * self.transfer_sum, transaction_id=transaction.id, 
            transfer_sum=settlement_coeff * self.transfer_sum)
        # check revenue ount was added
        self.check_successfull_money_transfering(account_id=self.revenue_account.base_account.id,
            expected_sum=(1 - settlement_coeff) * self.transfer_sum, transaction_id=transaction.id, 
            transfer_sum=(1 - settlement_coeff) * self.transfer_sum)

    def test__transaction_is_already_done(self):
        self.create_transaction(
            code=self.transaction.code, amount=self.transfer_sum,
            status=TRANSACTION_PRESETMENT_STATUS,
            from_account=self.user_account_1.base_account,
            to_account=self.user_account_2.base_account,
        )

        with self.assertRaises(IssuerTransactionError) as err_cm:
            Transaction.objects.present_transaction(
                self.transaction.code, self.transfer_sum, self.transfer_sum,
                from_account=self.user_account_1.base_account,
                to_account=self.user_account_2.base_account,
            )
        err = err_cm.exception
        self.assertEqual(err.args[0], 'already_done')        


class RollbackNonPresentmentTransaction(CreateAccountMixin, CreateTransactionMixin, 
                                        TestTransactionMixin, TestCase):

    '''
    Test for rolling back because of TTL
    '''

    @classmethod
    def setUpTestData(cls):
        # TODO: more verbose date manipulations
        # now it is essential to constract tomorrow obj before transaction
        # to fit into selection interval. which is not good
        cls.tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        cls.user_account = cls.create_account_with_amount()
        cls.base_sum = cls.user_account.base_account.amount
        cls.transfer_sum = decimal.Decimal(0.2) * cls.base_sum
        # create authorization transactions
        cls.transactions_number = 3
        cls.transactions = [
            cls.create_transaction(
                from_account=cls.user_account.base_account,
                to_account=cls.user_account.reserved_account,
                amount=cls.transfer_sum,
            )
            for i in range(cls.transactions_number)
        ]
        # create representment transaction
        cls.create_transaction(
            code=cls.transactions[0].code,
            status=TRANSACTION_PRESETMENT_STATUS,
            amount=cls.transfer_sum)
        cls.not_presented_transaction_codes = {transaction.code: 1 for transaction in cls.transactions[1:]}
        cls.base_sum_after_initial_transactions = cls.base_sum - cls.transactions_number * cls.transfer_sum

    def test__get_transactions_for_rollback(self):
        transaction_codes = Transaction.objects.get_non_presented_transactions_before(self.tomorrow)
        transaction_codes = {code: 1 for code in transaction_codes}
        self.assertDictEqual(transaction_codes, self.not_presented_transaction_codes)

    def test__transaction_are_rollbacked_already(self):
        self.create_transaction(
            code=self.transactions[1].code,
            status=TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS
        )
        Transaction.objects.rollback_late_presentment(self.transactions[1].code)
        # test double rollback dind't occured
        self.assertAlmostEqual(
            self.user_account.base_account.amount, self.base_sum_after_initial_transactions)


    def test__transaction_is_rollbacked_successfully(self):
        transaction = Transaction.objects.rollback_late_presentment(self.transactions[2].code)
        # check base_account amount was added
        self.check_successfull_money_transfering(account_id=self.user_account.base_account.id,
            expected_sum=self.base_sum_after_initial_transactions + self.transfer_sum, 
            transaction_id=transaction.id, 
            transfer_sum=self.transfer_sum)
        # check reserved_account amount was deducted
        self.check_successfull_money_transfering(account_id=self.user_account.reserved_account.id,
            expected_sum=self.transfer_sum * (self.transactions_number - 1), 
            transaction_id=transaction.id, 
            transfer_sum=-self.transfer_sum)