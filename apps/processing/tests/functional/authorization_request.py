import decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.processing.models.transactions import Transaction, \
                                                TRANSACTION_AUTHORIZATION_STATUS
from apps.processing.views import SchemaWebHook 
from utils.tests import ShemaWebHookBaseTestCase


class AuthorizationRequestTestCase(ShemaWebHookBaseTestCase):
   
    '''
    Functional test for authorization Schema webhook.
    Checks ret codes and modification in database.
    '''

    def setUp(self):
        self.user_account = self.create_account_with_amount()
        self.arrange_amounts()

    ##
    # Helper methods
    ##

    # Arrangements

    def arrange_amounts(self):
        self.base_amount = self.user_account.base_account.amount
        self.reserved_amount = self.user_account.reserved_account.amount
        self.transfer_amount = decimal.Decimal(0.5) * self.base_amount
        self.real_transfer_amount = Transaction.objects.get_amount_for_reserve(
                                                        self.transfer_amount)

    # Shortcuts

    def create_authorization_transaction_by_request(self, **kwargs):
        '''
        Helper for transaction creation using API
        '''
        request_factory = APIRequestFactory()
        schema_params = {
            'amount': self.transfer_amount, 
            'card_id': self.user_account.card_id}
        schema_params.update(kwargs)
        request = request_factory.post('/api/v1/request/',
            self.create_schema_request(**schema_params),
            format='json')
        return SchemaWebHook.as_view()(request)

    def create_duplicate_transaction_by_request(self):
        '''
        Helper for duplicationg transaction using API
        '''
        transaction_code = 'DUBLE'
        self.create_transaction(code=transaction_code, 
                                status=TRANSACTION_AUTHORIZATION_STATUS)
        return self.create_authorization_transaction_by_request(transaction_code=transaction_code)

    def create_not_enough_money_transaction_by_request(self):
        '''
        Helper for creating transaction wich requests more money, than user has.
        '''
        return self.create_authorization_transaction_by_request(amount=self.base_amount * 2)

    ##
    # Test methods
    ##

    def test__valid_authorization_request__retcode(self):
        response = self.create_authorization_transaction_by_request()        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test__valid_authorization_request__base_amount_deducted(self):
        response = self.create_authorization_transaction_by_request()
        self.check_account_result_amount(self.user_account.base_account.id,
                                      self.base_amount - self.real_transfer_amount)

    def test__valid_authorization_request__reserved_amount_increased(self):
        response = self.create_authorization_transaction_by_request()
        self.check_account_result_amount(self.user_account.reserved_account.id,
                                      self.real_transfer_amount)

    def test__invalid_user_request__retcode(self):
        response = self.create_authorization_transaction_by_request(card_id='INVALID')
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test__duplicate_transaction__retcode(self):
        response = self.create_duplicate_transaction_by_request()
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test__duplicate_transaction__base_amount_not_modified(self):
        self.create_duplicate_transaction_by_request()
        self.check_account_result_amount(self.user_account.base_account.id,
                                         self.base_amount)


    def test__duplicate_transaction__reserved_amount_not_modified(self):
        self.create_duplicate_transaction_by_request()
        self.check_account_result_amount(self.user_account.reserved_account.id,
                                      self.reserved_amount)

    def test__not_enough_money__retcode(self):
        response = self.create_not_enough_money_transaction_by_request()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test__not_enough_money__base_amount_not_modified(self):
        self.create_not_enough_money_transaction_by_request()
        self.check_account_result_amount(self.user_account.base_account.id,
                                      self.base_amount)

    def test__not_enough_money__reserved_amount_not_modified(self):
        self.create_not_enough_money_transaction_by_request()
        self.check_account_result_amount(self.user_account.reserved_account.id,
                                      self.reserved_amount)

    ## currency tests - not implemented
    def test__currency_exchanged__successfull(self):
        pass

    def test__currency_api_is_down__get_500(self):
        pass

