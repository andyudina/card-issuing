import datetime

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, \
                                force_authenticate

from card_issuing_excercise.utils import datetime_to_timestamp
from card_issuing_excercise.utils.tests import CreateAccountMixin
from users.views import BalanceView


#TODO: refactor
# - interchange blabla_account.amount to blabla_amount
class GetUserBalanceTestCase(CreateAccountMixin, TestCase):
   
    '''
    Functional test for transactions API.
    '''

    def setUp(self):
        # create user with balance
        self.user_account = self.create_account_with_amount()

    ##
    # Helper
    ##

    def get_user_balance_by_request(self, *args, **kwargs):
        '''
        Constructs and executes request for balance API.
        '''
        request_factory = APIRequestFactory()
        request = request_factory.get(
            '/api/v1/user/{}/balance/'.format(kwargs.get('user_id'), self.user_account.user_id),
            *args)
        if not kwargs.get('skip_auth'):
            force_authenticate(request, self.user_account.user)
        return BalanceView.as_view()(request)

    ##
    # Tests
    ##

    def test__current_balance__successfull(self):
        response = self.get_user_balance_by_request()
        amount = self.user_account.base_account.amount
        self.assertDictEqual(response.data,
             {
                 'available_amount': amount,
                 'total_amount': anount
             })           

    def test__balance_in_past__successfull(self):
        date_before = self.user_account.created_at - datetime.timedelta(days=1)
        response = self.get_user_balance_by_request({'ts': datetime_to_timestamp(date_before)})
        self.assertDictEqual(response.data,
             {
                 'available_amount': 0,
                 'total_amount': 0
             })

    def test__non_authenticated_user__got_403(self):
        response = self.get_user_balance_by_request(skip_auth=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)     
   
    def test__non_authorized_user__got_403(self):
        response = self.get_user_balance_by_request(user_id=self.user_account.user_id + 1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
