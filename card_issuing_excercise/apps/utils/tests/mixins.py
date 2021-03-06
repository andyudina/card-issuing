''' Test helper mixins'''

import decimal
import random
import string


from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from card_issuing_excercise.apps.processing.models.accounts import UserAccountsUnion, \
    Account
from card_issuing_excercise.apps.processing.models.transactions import Transaction, \
    TRANSACTION_AUTHORIZATION_STATUS
from card_issuing_excercise.apps.processing.models.transfers import Transfer
from card_issuing_excercise.apps.utils.utils import almost_equal
from card_issuing_excercise.settings import AMOUNT_PRECISION_SETTINGS


def get_random_string_for_test(N=8):
    '''
    Shortcut for random string generation.
    Uses ascii uppercase and digits.
    Accepts length
    '''
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for _ in range(N))


class CreateAccountMixin:

    '''
    Helper mixin for creating account and user
    '''

    @classmethod
    def create_user(cls):
        unique_user_id = '_'.join(['TEST', get_random_string_for_test()])
        return User.objects.create(
            username=unique_user_id,
            password=unique_user_id)

    @classmethod
    def create_account(cls, created_at=None):
        '''
        Create basic account without any money saved
        '''
        user = cls.create_user()
        card_id = get_random_string_for_test()
        account = UserAccountsUnion.objects.create(user=user, card_id=card_id)
        if created_at:
            UserAccountsUnion.objects.\
                filter(id=account.id).\
                update(created_at=created_at)
            account.refresh_from_db()
        return account

    @classmethod
    def create_account_with_amount(cls, created_at=None):
        '''
        Create basic account with money already loaded.
        '''
        base_amount = 10.0
        user_account = cls.create_account(created_at)
        Account.objects.filter(id=user_account.base_account.id).\
            update(amount=base_amount)
        user_account.base_account.refresh_from_db()
        return user_account

    @classmethod
    def create_revenue_account(cls):
        '''
        Helper for creating special account for collecting revenue.
        '''
        return UserAccountsUnion.objects.create_revenue_account()

    @classmethod
    def create_settlement_account(cls):
        '''
        Helper for creating special account for collecting debts to the Schema.
        '''
        return UserAccountsUnion.objects.create_inner_settlement_account()

    @classmethod
    def create_external_settlement_account(cls):
        '''
        Helper for creating special account for collecting debts to the Schema.
        '''
        return UserAccountsUnion.objects.create_external_settlement_account()

    @classmethod
    def create_load_money_account(cls):
        '''
        Helper for creating special account for loading money to user account.
        '''
        return UserAccountsUnion.objects.create_external_load_money_account()


class CreateTransactionMixin:

    '''
    Helper mixin for creation transaction with transfers.
    Don't take care of transfering consistensy!
    '''

    @classmethod
    def create_transaction(cls, **kwargs):
        '''
        Helper for creating arbitrary transaction.
        Modifies amount exactly as in args!
        Don't do "reserve more" magic
        '''
        transaction = Transaction.objects.create(
            code=kwargs.get('code', get_random_string_for_test()),
            status=kwargs.get('status', TRANSACTION_AUTHORIZATION_STATUS))
        if kwargs.get('created_at'):
            Transaction.objects.filter(id=transaction.id).\
                update(created_at=kwargs.get('created_at'))
            transaction.refresh_from_db()
        cls._try_create_transfers(transaction, **kwargs)
        return transaction

    @classmethod
    def _try_create_transfers(cls, transaction, **kwargs):
        '''
        Helper for trasfers creation
        Modifies account amounts
        '''
        # for amount deductions
        AMOUNT_COEFF_TO_ACC_TYPE = {
            'to_account': 1,
            'from_account': -1}
        for acc_type in ['from_account', 'to_account']:
            account = kwargs.get(acc_type)
            if not account:
                continue
            amount_coeff = AMOUNT_COEFF_TO_ACC_TYPE.get(acc_type)
            amount = amount_coeff * kwargs.get('amount')
            account.modify_amount(amount)
            transaction.transfers.create(
                account=account, amount=amount)

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
                issuer_transaction = Transaction.objects.create(
                    code=kwargs.get('transaction_code'),
                    status=kwargs.get('status'))
            Transaction.objects.\
                filter(id=issuer_transaction.id).\
                update(created_at=kwargs.get('datetime'))
        except IntegrityError:
            issuer_transaction = Transaction.objects.get(
                code=kwargs.get('transaction_code'),
                status=kwargs.get('status'))
        issuer_transaction.transfers.create(
            account=kwargs.get('account'), amount=kwargs.get('amount'))


class DecimalAssertionsMixin:

    '''
    Helper mixin for testing complex structions with decimals.
    '''

    def assertAlmostIn(self, obj, list_):
        # TODO: more verbose err message
        assert any(almost_equal(obj, value) for value in list_)


class TestTransactionMixin(DecimalAssertionsMixin):

    '''
    Helper mixin for testing that transaction was created successfully
    and did all require modifications
    '''

    def check_account_result_amount(self, account_id, expected_amount):
        account = Account.objects.get(id=account_id)
        self.assertAlmostEqual(
            account.amount, decimal.Decimal(expected_amount),
            places=AMOUNT_PRECISION_SETTINGS.get('decimal_places'))

    def check_transfer_exists(self, account_id,
                              transfer_amount, transaction_id):
        transfer_amounts = Transfer.objects.\
            filter(transaction_id=transaction_id, account_id=account_id).\
            values_list('amount', flat=True)
        self.assertAlmostIn(transfer_amount, transfer_amounts)


EXTRA_SCHEMA_REQUEST_KEYS = ['settlement_amount', 'settlement_currency']


class TestTransactionAPIMixin(TestTransactionMixin):

    '''
    Mixin for testing transaction API.
    '''

    def create_schema_request(self, **kwargs):
        '''
        Generates dictionary with transaction parameters, 
        which is used by schema web hook.
        '''
        # TODO: what happens when transfer reciever is another our client?
        # TODO: how currency are managed?
        # are transactions saved in one base currency and who is responsible
        # for exchange?
        extra_request_params = {
            key: kwargs.get(key) for key in EXTRA_SCHEMA_REQUEST_KEYS
            if kwargs.get(key)
        }
        schema_request = {
            'type': kwargs.get('type', 'authorization'),
            'card_id': kwargs.get('card_id', 'TEST'),
            'transaction_id': kwargs.get('transaction_code', 'TEST'),
            'merchant_name': kwargs.get('merchant_name', 'Test merchant'),
            'merchant_country': kwargs.get('merchant_country', 'US'),
            'merchant_mcc': kwargs.get('merchant_mcc', '1111'),
            'billing_amount': kwargs.get('amount', 10.00),
            'billing_currency': kwargs.get('currency', 'EUR'),
            'transaction_amount': kwargs.get('transaction_amount', 10.0),
            'transaction_curreny': kwargs.get('transaction_currency', 'EUR'),
        }
        schema_request.update(extra_request_params)
        self._amounts_to_str_inplace(schema_request)
        return schema_request

    def _amounts_to_str_inplace(self, schema_request):
        '''
        Transforming values of all amount keys to str with 2 decimal places
        '''
        for key in schema_request.keys():
            if 'amount' in key:
                schema_request[key] = '%.2f' % schema_request[key]


class TestUsersAPIMixin:

    '''
    Mixin for testing users public API - misc helpers
    '''

    def get_resource_for_user(self, resource, *args, **kwargs):
        '''
        Constructs and executes request for user API.
        '''
        # use APIClient for more verbose routing test
        client = APIClient()
        if kwargs.get('user_for_auth'):
            client.force_authenticate(user=kwargs.get('user_for_auth'))
        # TODO: native url constructions
        return client.get(
            '/api/v1/user/{}/{}/'.format(kwargs.get('user_id'), resource),
            *args)

    def get_amount_repr(self, amount):
        '''
        Converts amount to json representation
        '''
        return str(-round(amount, 4))
