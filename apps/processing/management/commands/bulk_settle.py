''' Management command for bulk settlement and outdated transactions rollback'''

import datetime

from django.core.management.base import BaseCommand

from apis import SchemaAPI, TelegramAPI, \
    SmsAPI, SendgridAPI
from apps.processing.models import Transaction, \
    UserAccountsUnion
from card_issuing_excercise.settings import AUTHORISATION_TRANSACTION_TTL
from utils import to_start_day


class Command(BaseCommand):

    '''
    Sends settlement debts to schema in bulk 
    and rollbacks outdated transactions
    '''

    help = 'Batch process for settlements and outdated transactions management'

    def handle(self, *args, **kwargs):
        # do some magic with Schema API
        # and log it as our transactions
        self._transfer_settlements_to_schema()
        # and rollback pld transactions
        self._rollback_outdated_transactions()

    def _transfer_settlements_to_schema(self):
        '''
        Communicates with the SchemaAPI and processes settlement transfers.
        Raises ValueError if smth bad happened.
        '''
        inner_settlement_account = UserAccountsUnion.objects.\
            get_inner_settlement_account()
        external_settlement_account = UserAccountsUnion.objects.\
            get_external_settlement_account()
        try:
            SchemaAPI().transfer_debts_to_schema(
                amount=inner_settlement_account.base_amount)
            self._log_settlement_transaction(
                inner_settlement_account=inner_settlement_account,
                external_settlement_account=external_settlement_account)
        except SchemaAPI.SchemaError as error:
            self._alarm_schema_error(error.info)

    def _log_settlement_transaction(self, **kwargs):
        '''
        Saves info of successfull settlements as our transfers
        '''
        # so error-prone logic. should be rewrighten after requirements are
        # specified
        Transaction.objects.settle_day_transactions(
            kwargs.get('inner_settlement_account').base_amount,
            kwargs.get('inner_settlement_account').base_account,
            kwargs.get('external_settlement_account').base_account)

    def _alarm_schema_error(self, err_info):
        '''
        Sends schema error to all monitoring channels.
        '''
        TelegramAPI().alarm_schema_err(err_info)
        SmsAPI().alarm_schema_err(err_info)
        SendgridAPI().alarm_schema_err(err_info)

    def _rollback_outdated_transactions(self):
        '''
        Rollbacks all old authorization transactions 
        without prsentment transactions
        '''
        transactions_date_treshold = \
            self._get_transactions_date_treshold()
        outdated_transaction_codes = Transaction.objects.\
            get_non_presented_transactions_before(transactions_date_treshold)
        for code in outdated_transaction_codes:
            Transaction.objects.rollback_late_presentment(code)

    def _get_transactions_date_treshold(self):
        '''
        Get date all transactions before which are outdated
        '''
        return to_start_day(
            datetime.datetime.now() -
            datetime.timedelta(days=AUTHORISATION_TRANSACTION_TTL))
