'''Tests public API which returns balance of current user'''

import datetime

from rest_framework import status

from utils import datetime_to_timestamp
from utils.tests import UserAPITestCase


class GetUserBalance(UserAPITestCase):

    '''Functional test for transactions API'''

    def setUp(self):
        # create user with balance
        self.user_account = self.create_account_with_amount()

    ##
    # Helper
    ##

    def get_user_balance_by_request(self, *args, **kwargs):
        '''Constructs and executes request for balance API'''
        return self.get_resource_for_user(
            'balance', *args,
            user_id=kwargs.get('user_id', self.user_account.id),
            user_for_auth=kwargs.get('user_for_auth', self.user_account.user))
    ##
    # Tests
    ##

    def test__current_balance__successfull(self):
        response = self.get_user_balance_by_request()
        amount = self.user_account.base_amount
        self.assertDictEqual(response.data,
                             {
                                 'available_amount': amount,
                                 'total_amount': amount
                             })

    def test__balance_in_past__successfull(self):
        date_before = self.user_account.created_at - datetime.timedelta(days=1)
        response = self.get_user_balance_by_request(
            {'ts': datetime_to_timestamp(date_before)})
        self.assertDictEqual(response.data,
                             {
                                 'available_amount': 0,
                                 'total_amount': 0
                             })

    def test__non_authenticated_user__got_403(self):
        response = self.get_user_balance_by_request(user_for_auth=None)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test__non_authorized_user__got_403(self):
        fake_user_account = self.create_account_with_amount()
        response = self.get_user_balance_by_request(
            user_id=fake_user_account.user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
