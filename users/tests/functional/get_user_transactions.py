import datetime

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, \
                                force_authenticate

from processing.models.transactions import TRANSACTION_PRESETMENT_STATUS
from card_issuing_excercise.utils import datetime_to_timestamp
from card_issuing_excercise.utils.tests import CreateAccountMixin, \
                                               CreateTransactionMixin                                               
from users.views import TransactionsView, \
                        TRANSACTIONS_PER_PAGE


# TODO: rm copy paste from balance test and 
# TODO: store transaction description!!
class GetUserTransactionsTestCase(CreateAccountMixin, 
                                  CreateTransactionMixin, TestCase):
   
    '''
    Functional test for transactions API.
    '''

    def setUp(self):
        # create user with balance
        self.user_account = self.create_account_with_amount()
        self.settlement_account = self.create_settlement_account()
        #self.revenue_account = self.create_revenue_account()
        self.base_amount = self.sender_account.base_account.amount
        self.reserved_amount = self.sender_account.reserved_account.amount
        self.transfer_amount = decimal.Decimal(0.3) * self.base_amount
        #self.real_transfered_amount = Transaction.objects.get_amount_for_reserve(self.transfer_amount)
        #self.settlement_coeff = decimal.Decimal(0.7)
        self.authorization_transaction = self.create_transaction(
            from_account=self.sender_account.base_account,
            to_account=self.sender_account.reserved_account,
            amount=self.transfer_amount)
        self.presentment_transaction = self.create_transaction(
            code=self.transaction.code, amount=self.transfer_amount,
            status=TRANSACTION_PRESETMENT_STATUS,
            from_account=self.sender_account.base_account,
            to_account=self.settlement_account.base_account,
        )
 
    ##
    # Helper
    ##

    def get_user_transactions_by_request(self, *args, **kwargs):
        #TODO: rm copy paste from balance view
        '''
        Constructs and executes request for balance API.
        '''
        request_factory = APIRequestFactory()
        request = request_factory.get(
            '/api/v1/user/{}/transactions/'.format(kwargs.get('user_id'), self.user_account.user_id),
            *args)
        if not kwargs.get('skip_auth'):
            force_authenticate(request, self.account_user.user)
        return TransactionsView.as_view()(request)

    ##
    # Tests
    ##

    def test__paginated_transactions__successfull(self):
        response = get_user_transaction_by_request({'pg': 2})
        self.assertDictEqual(response.data,
            {
                'has_prev_page': False,
                'pg': 2,
                'transactions': [],
                'transactions_per_page': TRANSACTIONS_PER_PAGE,
                'transactions_number': 0,
            }) 
        

    def test__transactions_in_valid_time_range__successfull(self):
        yesterday = self.user_account.created_at - datetime.tiedelta(days=1)
        response = get_user_transaction_by_request({'begin_ts': datetime_to_ts(yesterday)})
        self.assertDictEqual(response.data,
            {
                'has_prev_page': False,
                'pg': 1,
                'transactions': [
                     {
                         'created_at': datetime_to_ts(self.presentment_transaction.created_at),
                         'id': self.presentment_transaction.id,
                         'transfers': [
                             {'amount': self.transfer_amount}
                         ]
                     }
                 ],
                'transactions_per_page': TRANSACTIONS_PER_PAGE,
                'transactions_number': 1,
            })


    def test__non_authorized_user__got_403(self):
        response = self.get_user_transaction_by_request(user_id=self.user_account.user_id + 1)
        self.self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test__non_authenticated_user__got_403(self):
        response = self.get_user_transaction_by_request(skip_auth=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


