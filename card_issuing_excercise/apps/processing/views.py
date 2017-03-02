''' Schema Web hook view'''

from django.http import HttpResponse

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser

from card_issuing_excercise.apps.currency_converter.converter import Converter
from card_issuing_excercise.apps.processing.models import UserAccountsUnion, \
    Transaction
from card_issuing_excercise.apps.processing.models.transactions import \
    IssuerTransactionError
from card_issuing_excercise.apps.processing.serializers import \
    SchemaRequestSerializer


class SchemaWebHook(APIView):

    '''
    Handles payment requests from the Schema.
    For both authorisation and presentment requests.
    '''

    parser_classes = (JSONParser,)

    def post(self, request, format=None):
        # check user exists
        try:
            self._process_request(request)
        except IssuerTransactionError as err:
            return HttpResponse(
                status=self._get_http_status_by_code(err.code))
        return HttpResponse()

    def _process_request(self, request):
        '''
        Shortcut for the Schema request processing.
        Raises IssuerTransactionError.
        Used for simple and unified errors management
        '''
        request_serializer = SchemaRequestSerializer(data=request.data)

        if not request_serializer.is_valid():
            raise IssuerTransactionError(
                Transaction.Errors.INVALID_FORMAT)
        request_data = request_serializer.data
        try:
            request_data = self._convert_amounts_currencies_inplace(
                request_data)
        except Converter.ConverterError:
            # send 500 explicitly if converter is down
            raise IssuerTransactionError(
                Transaction.Errors.INVALID_CONFIGURATION)
        # check account exists
        # TODO: put it into serizlizer
        account = self._get_account_by_card_id(
            request_data.get('card_id'))
        if not account:
            raise IssuerTransactionError(
                Transaction.Errors.INVALID_USER)
        transaction = self._create_transaction(account, request_data)
        transaction.update_descriptions(request_data)

    def _create_transaction(self, account, request):
        '''
        Shortcut for different creating transaction.
        Depends on type specified in request
        '''
        request_type = request.get('type')
        if request_type == 'authorization':
            return self._process_authorization_request(account, request)
        elif request_type == 'presentment':
            return self._process_presentment_request(account, request)
        raise IssuerTransactionError(Transaction.Errors.INVALID_FORMAT)

    def _process_authorization_request(self, account, request):
        return Transaction.objects.try_authorise_transaction(
            request.get('transaction_id'), request.get('billing_amount'),
            from_account=account.base_account,
            to_account=account.reserved_account)

    def _process_presentment_request(self, account, request):
        # get inner settlement account and revenue account
        # we should fail with 500 here fast
        # if it is not presented - it means that whole start up was broken
        settlement_account = UserAccountsUnion.objects.\
            get_inner_settlement_account()
        revenue_account = UserAccountsUnion.objects.\
            get_revenue_account()
        if settlement_account is None or \
                revenue_account is None:
            raise IssuerTransactionError(
                Transaction.Errors.INVALID_CONFIGURATION)
        return Transaction.objects.present_transaction(
            request.get('transaction_id'),
            request.get('billing_amount'), request.get('settlement_amount'),
            from_account=account.base_account,
            to_account=settlement_account.base_account,
            extra_account=revenue_account.base_account)

    def _get_account_by_card_id(self, card_id):
        # TODO: check if account has rights to do transaction
        '''
        Helper for retrieving account.
        '''
        # we depends on inner integrity checks
        # and don't need to check if multiple objects returned
        return UserAccountsUnion.objects.\
            filter(card_id=card_id).first()

    def _get_http_status_by_code(self, code):
        '''
        Maps inner error codes to http statuses
        '''
        CODE_TO_HTTP_STATUS = {
            Transaction.Errors.ALREADY_DONE: status.HTTP_409_CONFLICT,
            Transaction.Errors.DOES_NOT_EXISTS: status.HTTP_404_NOT_FOUND,
            Transaction.Errors.NOT_ENOUGH_MONEY: status.HTTP_403_FORBIDDEN,
            Transaction.Errors.INVALID_FORMAT: status.HTTP_400_BAD_REQUEST,
            Transaction.Errors.INVALID_USER: status.HTTP_406_NOT_ACCEPTABLE,
            Transaction.Errors.INVALID_CONFIGURATION: status.HTTP_500_INTERNAL_SERVER_ERROR}
        DEFAULT_HTTP_STATUS = status.HTTP_400_BAD_REQUEST
        return CODE_TO_HTTP_STATUS.get(code, DEFAULT_HTTP_STATUS)

    # Currencies helpers

    def _convert_amounts_currencies_inplace(self, amounts):
        '''
        Helper for amount cconvertion.
        Raises ConverterError
        '''
        for amount_type in ['billing', 'settlement']:
            if not amounts.get(amount_type + '_amount'):
                continue
            amounts[amount_type + '_amount'] = \
                self._get_amount_in_inner_currency(
                amounts.get(amount_type + '_amount'),
                amounts.get(amount_type + '_currency'))
        return amounts

    def _get_amount_in_inner_currency(self, amount, source_currency):
        '''
        Helper for currecny converting
        '''
        return Converter().get_amount_for_save(amount, source_currency)
