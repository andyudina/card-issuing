from django.test import TestCase
from rest_framework.test import APIRequestFactory

from processing.models.transactions import Transaction, \
                                           TRANSACTION_PRESENTMENT_STATUS
from processing.views import SchemaWebHook
from card_issuing_excercise.utils.tests import CreateAccountMixin, \
                                               CreateTransactionMixin, \
                                               TestTransactionAPIMixin


# TODO: checks for invalid format
class PresentmentRequestTestCase(CreateAccountMixin, CreateTransactionMixin,
                                 TestTransactionAPIMixin, TestCase):

   
    '''
    Functional test for presentment Schema webhook.
    Checks ret codes and modification in database.
    '''

    def setUp(self):
        self.sender_account = self.create_account_with_amount()
        self.settlement_account = self.create_settlement_account()
        self.revenue_account = self.create_revenue_account()
        self.base_amount = self.sender_account.base_account.amount
        self.reserved_amount = self.sender_account.reserved_account.amount
        self.transfer_amount = decimal.Decimal(0.5) * self.base_amount
        self.real_transfered_amount = Transaction.objects.get_amount_for_reserve(self.transfer_amount)
        self.settlement_coeff = decimal.Decimal(0.7)
        self.authorization_transaction = self.create_transaction(
             from_account=self.sender_account.base_account,
             to_account=self.sender_account.reserved_account,
             amount=self.transfer_amount)

    ##
    # Helpers
    ##

    def create_duplicated_presentment_transaction(self, **kwargs):
        '''
        Helper for transaction duplication emulation
        '''
        self.create_transaction(
            code=self.transaction.code, amount=self.transfer_amount,
            status=TRANSACTION_PRESETMENT_STATUS,
            from_account=self.sender_account.base_account,
            to_account=self.settlement_account.base_account,
        )
        return self.create_presentment_transaction_by_request()

    def create_presentment_transaction_by_request(self, **kwargs):
        '''
        Helper for presentment transaction creation using API
        '''
        request_factory = APIRequestFactory()
        request = request_factory.post('/api/v1/request/',
            self.create_schema_request(type='presentment', 
                                       account_id=self.sender_account.id,
                                       transaction_code=self.authorization_transaction.code,
                                       amount=self.transfer_amount, **kwargs))
        return SchemaWebHook.as_view()(request)

    def test__valid_presentment_request__retcode(self):
        response =  self.create_presentment_transaction_by_request()
        self.assertEqual(response.status_code, status.HTTP_200_OK)        

    def test__valid_presentment_request__sender_base_amount_deducted(self):
        self.create_presentment_transaction_by_request()
        self.check_account_result_sum(self.sender_account.base_account.id,
                                      self.base_amount - self.transfer_amount)

    def test__valid_presentment_request__sender_reserved_amount_deducted(self):
        self.create_presentment_transaction_by_request()
        self.check_account_result_sum(
            self.sender_account.reserved_account.id, 0.0)

    def test__valid_presentment_request__reciever_base_amount_increased(self):
        self.create_presentment_transaction_by_request()
        self.check_account_result_sum(self.settlement_account.base_account.id,
                                      self.transfer_amount * self.settlement_coeff)

    def test__valid_presentment_request__revenue_amount_increased(self):
        self.create_presentment_transaction_by_request()
        self.check_account_result_sum(self.revenue_account.base_account.id,
                                      self.transfer_amount * (1 - self.settlement_coeff))

    def test__invalid_user_request__retcode(self):
        response = self.create_presentment_transaction_by_request(account_id='INVALID')
        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

    def test__invalid_transaction_request__retcode(self):
        response = self.create_presentment_transaction_by_request(transaction_code='INVALID')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__duplicate_transaction__retcode(self):
        response = self.create_duplicated_presentment_transaction()
        self.assertEqual(reponse.status_code, status.HTTP_409_CONFLICT)

    def test__duplicate_transaction__sender_base_amount_not_modified(self):
        self.create_duplicated_presentment_transaction()
        self.check_account_result_sum(self.sender_account.base_account.id,
                                      self.base_amount - self.real_transfer_amount)

    def test__duplicate_transaction__sender_reserved_amount_not_modified(self):
        self.self.create_duplicated_presentment_transaction()
        self.check_account_result_sum(self.sender_account.reserved_account.id,
                                      self.real_transfer_amount)

    def test__duplicate_transaction__reciever_base_amount_not_modified(self):
        self.self.create_duplicated_presentment_transaction()
        self.check_account_result_sum(
            self.settlement_account.base_account.id, 0.0)

    def test__duplicate_transaction__revenue_not_modified(self):
        self.create_duplicated_presentment_transaction()
        self.check_account_result_sum(
            self.revenue_account.base_account.id, 0.0)


