'''Tests public API which returns transactions of current user'''

import datetime
import decimal
from unittest import skip

from rest_framework import status

from card_issuing_excercise.apps.processing.models.transactions import \
    TRANSACTION_PRESENTMENT_STATUS
from card_issuing_excercise.apps.utils import datetime_to_timestamp, \
    to_dict
from card_issuing_excercise.apps.utils.tests import UserAPITestCase, \
    CreateTransactionMixin


class GetUserTransactions(UserAPITestCase,
                          CreateTransactionMixin):

    '''
    Functional test for transactions API.
    '''

    def setUp(self):
        self.arrange_accounts()
        self.arrage_amounts()
        self.arrange_transactions()

    ##
    # Helpers
    ##

    # Arrangements
    def arrange_accounts(self):
        self.user_account = self.create_account_with_amount()
        self.settlement_account = self.create_settlement_account()

    def arrage_amounts(self):
        self.base_amount = self.user_account.base_account.amount
        self.reserved_amount = self.user_account.reserved_account.amount
        self.transfer_amount = decimal.Decimal(0.3) * self.base_amount

    def arrange_transactions(self):
        self.authorization_transaction = self.create_transaction(
            from_account=self.user_account.base_account,
            to_account=self.user_account.reserved_account,
            amount=self.transfer_amount)
        self.presentment_transaction = self.create_transaction(
            code=self.authorization_transaction.code,
            amount=self.transfer_amount,
            status=TRANSACTION_PRESENTMENT_STATUS,
            from_account=self.user_account.base_account,
            to_account=self.settlement_account.base_account)

    # Shortcuts
    def get_user_transactions_by_request(self, *args, **kwargs):
        '''
        Constructs and executes request for transaction API.
        '''
        return self.get_resource_for_user(
            'transaction', *args,
            user_id=kwargs.get('user_id', self.user_account.id),
            user_for_auth=kwargs.get('user_for_auth', self.user_account.user))

    ##
    # Tests
    ##

    def test__paginated_transactions__successfull(self):
        response = self.get_user_transactions_by_request({'page': 1})
        transfer = self.presentment_transaction.transfers.\
            get(account_id=self.user_account.base_account.id)
        self.assertDictEqual(to_dict(response.data),

                             {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'created_at': datetime_to_timestamp(
                        self.presentment_transaction.created_at),
                    'id': self.presentment_transaction.id,
                    'status': TRANSACTION_PRESENTMENT_STATUS,
                    'human_readable_description': None,
                    'transfers': [
                        {
                            'amount': self.get_amount_repr(
                                self.transfer_amount),
                            'id': transfer.id
                        }
                    ]
                }
            ],
        })

    def test__transactions_in_valid_time_range__successfull(self):
        yesterday = self.user_account.created_at + datetime.timedelta(days=1)
        response = self.get_user_transactions_by_request(
            {'begin_ts': datetime_to_timestamp(yesterday)})
        self.assertDictEqual(response.data,
                             {
                                 'count': 0,
                                 'next': None,
                                 'previous': None,
                                 'results': [],
                             })

    @skip('Need forcing auth before object selection -- not implemented')
    def test__non_authorized_user__got_403(self):
        fake_user_account = self.create_account_with_amount()
        response = self.get_user_transactions_by_request(
            user_id=fake_user_account.user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test__non_authenticated_user__got_403(self):
        response = self.get_user_transactions_by_request(user_for_auth=None)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
