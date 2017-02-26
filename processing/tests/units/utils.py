import random
import string

from django.db import IntegrityError, transaction
from django.contrib.auth.models import User

from processing.models.accounts import UserAccountsUnion, Account
from processing.models.transactions import Transaction, TRANSACTION_AUTHORIZATION_STATUS
from processing.models.transfers import Transfer


def get_random_string_for_test(N=8):
    '''
    Shortcut for random string generation.
    Uses ascii uppercase and digits.
    Accepts length
    '''
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))


class CreateAccountMixin:
    
    '''
    Helper mixin for creating account and user
    '''

    @classmethod
    def create_user(cls):
        unique_user_id = '_'.join(['TEST', get_random_string_for_test()])
        return User.objects.create(username=unique_user_id, password=unique_user_id)

    @classmethod
    def create_account(cls, created_at=None):
        user = cls.create_user()
        account_id = get_random_string_for_test()
        account = UserAccountsUnion.objects.create(user=user, id=account_id)
        if created_at:
            UserAccountsUnion.objects.filter(id = account.id).update(created_at=created_at)
        return account

    @classmethod
    def create_account_with_amount(cls, created_at=None):
        base_amount = 10.0
        user_account = cls.create_account(created_at)
        user_account.base_account.amount = base_amount
        user_account.base_account.save(update_fields=['amount'])
        return user_account


class CreateTransactionMixin:

    '''
    Helper mixin for creation transaction with transfers.
    Don't take care of transfering consistensy!
    '''

    @classmethod
    def create_transaction(cls, **kwargs):
        transaction = Transaction.objects.create(code=kwargs.get('code', get_random_string_for_test()), 
                                                 status=kwargs.get('status', TRANSACTION_AUTHORIZATION_STATUS))
        if kwargs.get('created_at'):
            Transaction.objects.filter(id=transaction.id).\
                                update(created_at=kwargs.get('created_at'))
        if kwargs.get('from_account'):
            transaction.transfers.create(account=kwargs.get('from_account'), amount=-kwargs.get('amount'))
        if kwargs.get('to_account'):
            transaction.transfers.create(account=kwargs.get('to_account'), amount=kwargs.get('amount'))
        return transaction

    @classmethod
    def add_transfer(cls, **kwargs):
        '''
        Create one transfer and its transaction if transaction didn't exist already.
        Takes arguments:
            - transaction_code
            - status
            - account
            - amount
            - datetime
        '''
        try:
            with transaction.atomic():
                issuer_transaction = Transaction.objects.create(code=kwargs.get('transaction_code'),
                                                                status=kwargs.get('status'))
            Transaction.objects.filter(id=issuer_transaction.id).\
                                update(created_at=kwargs.get('datetime'))
        except IntegrityError:
            issuer_transaction = Transaction.objects.get(code=kwargs.get('transaction_code'),
                                                         status=kwargs.get('status'))
        issuer_transaction.transfers.create(account=kwargs.get('account'), amount=kwargs.get('amount'))


class TestTransactionMixin:

    '''
    Helper mixin for testing that transaction was created successfully
    and did all require modifications
    '''

    def check_successfull_money_transfering(self, **kwargs):
        self.check_account_result_sum(kwargs.get('account_id'), kwargs.get('expected_sum'))
        self.check_transfer_exists(kwargs.get('account_id'), kwargs.get('transfer_sum'), kwargs.get('transaction_id'))

    def check_account_result_sum(self, account_id, expected_sum):
        self.assertTrue(
            Account.objects.filter(id=account_id, amount=expected_sum).exists())

    def check_transfer_exists(self,
            account_id, transfer_sum, transaction_id):
        self.assertTrue(
            Transfer.objects.filter(transaction_id=transaction_id, account_id=account_id, amount=transfer_sum))

