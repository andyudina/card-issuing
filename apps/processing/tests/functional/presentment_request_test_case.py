''' Tests Schema Webhook for presentment transction'''

import decimal

from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.processing.models.transactions import TRANSACTION_PRESENTMENT_STATUS
from apps.processing.views import SchemaWebHook
from utils.tests import ShemaWebHookBaseTestCase


class PresentmentRequest(ShemaWebHookBaseTestCase):

    '''
    Functional test for presentment Schema webhook.
    Checks return codes and modification in database.
    '''

    def setUp(self):
        self.arrange_accounts()
        self.arrange_amounts()
        self.arrange_transaction()

    ##
    # Helpers
    ##

    # Arrangements

    def arrange_accounts(self):
        self.sender_account = \
            self.create_account_with_amount()
        self.settlement_account = \
            self.create_settlement_account()
        self.revenue_account = \
            self.create_revenue_account()

    def arrange_amounts(self):
        self.base_amount = self.sender_account.base_account.amount
        self.reserved_amount = self.sender_account.reserved_account.amount
        self.transfer_amount = decimal.Decimal(0.5) * self.base_amount
        # no coeff in presentment tests for simplicity
        self.authorization_amount = self.transfer_amount
        self.settlement_coeff = decimal.Decimal(0.7)
        self.settlement_amount = self.settlement_coeff * self.transfer_amount

    def arrange_transaction(self):
        self.authorization_transaction = self.create_transaction(
            from_account=self.sender_account.base_account,
            to_account=self.sender_account.reserved_account,
            amount=self.transfer_amount)

    #  Shortcuts

    def create_duplicated_presentment_transaction(self, **kwargs):
        '''
        Helper for transaction duplication emulation
        '''
        self.create_transaction(
            code=self.authorization_transaction.code,
            status=TRANSACTION_PRESENTMENT_STATUS,
        )
        return self.create_presentment_transaction_by_request()

    def create_presentment_transaction_by_request(self, **kwargs):
        '''
        Helper for presentment transaction creation using API
        '''
        request_factory = APIRequestFactory()
        schema_params = {
            'type': 'presentment',
            'card_id': self.sender_account.card_id,
            'transaction_code': self.authorization_transaction.code,
            'amount': self.transfer_amount,
            'settlement_amount': self.settlement_amount}
        schema_params.update(kwargs)
        request = request_factory.post('/api/v1/request/',
                                       self.create_schema_request(
                                           **schema_params),
                                       format='json')
        return SchemaWebHook.as_view()(request)

    def test__valid_presentment_request__retcode(self):
        response = self.create_presentment_transaction_by_request()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test__valid_presentment_request__sender_base_amount_deducted(self):
        self.create_presentment_transaction_by_request()
        self.check_account_result_amount(
            self.sender_account.base_account.id,
            self.base_amount - self.transfer_amount)

    def test__valid_presentment_request__sender_reserved_amount_deducted(self):
        self.create_presentment_transaction_by_request()
        self.check_account_result_amount(
            self.sender_account.reserved_account.id, 0.0)

    def test__valid_presentment_request__reciever_base_amount_increased(self):
        self.create_presentment_transaction_by_request()
        self.check_account_result_amount(
            self.settlement_account.base_account.id,
            self.transfer_amount * self.settlement_coeff)

    def test__valid_presentment_request__revenue_amount_increased(self):
        self.create_presentment_transaction_by_request()
        self.check_account_result_amount(
            self.revenue_account.base_account.id,
            self.transfer_amount * (1 - self.settlement_coeff))

    def test__invalid_user_request__retcode(self):
        response = self.create_presentment_transaction_by_request(
            card_id='INVALID')
        self.assertEqual(
            response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test__invalid_transaction_request__retcode(self):
        response = self.create_presentment_transaction_by_request(
            transaction_code='INVALID')
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND)

    def test__duplicate_transaction__retcode(self):
        response = self.create_duplicated_presentment_transaction()
        self.assertEqual(
            response.status_code, status.HTTP_409_CONFLICT)

    def test__duplicate_transaction__sender_base_amount_not_modified(self):
        self.create_duplicated_presentment_transaction()
        self.check_account_result_amount(
            self.sender_account.base_account.id,
            self.base_amount - self.authorization_amount)

    def test__duplicate_transaction__sender_reserved_amount_not_modified(self):
        self.create_duplicated_presentment_transaction()
        self.check_account_result_amount(
            self.sender_account.reserved_account.id,
            self.authorization_amount)

    def test__duplicate_transaction__reciever_base_amount_not_modified(self):
        self.create_duplicated_presentment_transaction()
        self.check_account_result_amount(
            self.settlement_account.base_account.id, 0.0)

    def test__duplicate_transaction__revenue_not_modified(self):
        self.create_duplicated_presentment_transaction()
        self.check_account_result_amount(
            self.revenue_account.base_account.id, 0.0)

    # currency tests - not implemented
    def test__currency_exchanged__successfull(self):
        pass

    def test__currency_api_is_down__get_500(self):
        pass
