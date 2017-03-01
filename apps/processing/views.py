from django.http import HttpResponse

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser

from apps.processing.models import UserAccountsUnion, \
                                   Transaction
from apps.processing.models.transactions import IssuerTransactionError                             
from apps.processing.serializers import SchemaRequestSerializer
from currency_converter.converter import Converter

# TODO: refactor error codes -- 
# they should be somewhere in one place with verbose names
class SchemaWebHook(APIView):

    '''
        Handles payment requests from the Schema.
        For both authorisation and presentment requests.
    '''
    
    parser_classes = (JSONParser,)

    def post(self, request, format=None):
        # check user exists
        request_serializer = SchemaRequestSerializer(data=request.data)
        if request_serializer.is_valid():
            request_data = request_serializer.data
            for amount_type in ['billing', 'settlement']:
                if not request_data.get(amount_type + '_amount'):
                    continue
                try:
                    request_data[amount_type + '_amount'] = self._get_amount_in_inner_currency(
                        request_data.get(amount_type + '_amount'),
                        request_data.get(amount_type + '_currency'))
                except Converter.ConverterError as e:
                    # send 500 explicitly
                    return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)                    
            # check account exists
            # TODO: put it into serizlizer
            account = self._get_account_by_card_id(
                           request_data.get('card_id'))
            if not account:
                return HttpResponse(status=status.HTTP_406_NOT_ACCEPTABLE)
            # 
            request_type = request_serializer.data.get('type')
            if request_type == 'authorization':
                return self._process_authorization_request(account,
                                                           request_data)
            elif request_type == 'presentment':
                return self._process_presentment_request(account,
                                                          request_data)
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def _process_authorization_request(self, account, request):
        try:
            transaction = Transaction.objects.try_authorise_transaction(
                request.get('transaction_id'), request.get('billing_amount'),
                from_account=account.base_account,
                to_account=account.reserved_account)
            return HttpResponse()
        except IssuerTransactionError as err:
            return HttpResponse(status=self._get_http_status_by_code(err.code))

    def _process_presentment_request(self, account, request):
        # get inner settlement account and revenue account
        # we should fail with 500 here fast 
        # if it is not presented - it means that whole start up was broken
        settlement_account = UserAccountsUnion.objects.get_inner_settlement_account()
        revenue_account = UserAccountsUnion.objects.get_revenue_account()
        if settlement_account is None or \
                revenue_account is None:
            # send 500 explicitly
            return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            transaction = Transaction.objects.present_transaction(
                request.get('transaction_id'),
                request.get('billing_amount'), request.get('settlement_amount'),
                from_account=account.base_account,
                to_account=settlement_account.base_account,
                extra_account=revenue_account.base_account)
            return HttpResponse()
        except IssuerTransactionError as err:
            return HttpResponse(status=self._get_http_status_by_code(err.code))

    def _get_account_by_card_id(self, card_id):
        # TODO: check if account has rights to do transaction
        '''
        Helper for retrieving account.
        '''
        # we depends on inner integrity checks 
        # and don't need to check if multiple objects returned
        return UserAccountsUnion.objects.filter(card_id=card_id).first()

    def _get_http_status_by_code(self, code):
        '''
        Maps inner error codes to http statuses
        '''
        CODE_TO_HTTP_STATUS = {
            'already_done': status.HTTP_409_CONFLICT,
            'does_not_exists': status.HTTP_404_NOT_FOUND,
            'not_enough_money': status.HTTP_403_FORBIDDEN,
        }
        DEFAULT_HTTP_STATUS = status.HTTP_400_BAD_REQUEST
        return CODE_TO_HTTP_STATUS.get(code, DEFAULT_HTTP_STATUS)

    def _get_amount_in_inner_currency(self, amount, source_currency):
        '''
        Helper for currecny converting
        '''
        return Converter().get_amount_for_save(amount, source_currency)