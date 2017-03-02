''' Handles transactions related business logic'''

import datetime
import decimal

from django.db import models, \
    transaction, IntegrityError

from card_issuing_excercise.settings import AUTHORISATION_OVERHEAD
from card_issuing_excercise.apps.unique_id_generator.generator import \
    UniqueIDGenerator
from card_issuing_excercise.apps.utils import dict_to_base64


TRANSACTION_ID_LENGTH = 9

# Transaction statuses

TRANSACTION_AUTHORIZATION_STATUS = 'a'
TRANSACTION_PRESENTMENT_STATUS = 'p'
TRANSACTION_MONEY_SHORTAGE_STATUS = 'z'  # z for zero ;)
TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS = 't'
TRANSACTION_ROLLBACKED_STATUS = 'r'
TRANSACTION_LOAD_MONEY_STATUS = 'l'
TRANSACTION_SETTLEMENT_STATUS = 's'

TRANSACTION_STATUS_CHOICES = (
    (TRANSACTION_AUTHORIZATION_STATUS, 'Authorization'),
    (TRANSACTION_PRESENTMENT_STATUS, 'Presentment'),
    # transaction declined because of money shortage
    (TRANSACTION_MONEY_SHORTAGE_STATUS, 'Money shortage'),
    # transaction declined because there was no presentment during T + 1 day
    (TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS,
     'Presentment is exceeded TTL'),
    # rollback authorisation transaction for presentment
    (TRANSACTION_ROLLBACKED_STATUS, 'Rollback'),
    # special transaction for loading money,
    # don't need authorisation - presentment scheme
    (TRANSACTION_LOAD_MONEY_STATUS, 'Load money'),
    # special status for logging transfering our debt to Schema
    (TRANSACTION_SETTLEMENT_STATUS, 'Settle day transactions'),
)


class IssuerTransactionError(ValueError):

    '''
    Custom errors for transaction management.
    Possible error codes:
    - already_done (for reduplicated transactions)
    - not_enough_money
    '''

    @property
    def code(self):
        '''
        Shortcut for error code
        '''
        return self.args[0]


# Transaction error codes

TRANSACTION_ERROR_ALREADY_DONE = 'already_done'
TRANSACTION_ERROR_NOT_ENOUGH_MONEY = 'not_enough_money'
TRANSACTION_ERROR_DOES_NOT_EXISTS = 'does_not_exists'
TRANSACTION_ERROR_INVALID_CONFIGURATION = 'invalid_issuer_configuration'
TRANSACTION_ERROR_INVALID_FORMAT = 'invlid_format'
TRANSACTION_ERROR_INVALID_USER = 'invalid_user'

class TransactionManager(models.Manager):

    '''
    Provides base API for transaction management for views and management commands.
    Don't know anything about account types.
    Raises IssuerTransactionError with string error code on failure 
    '''

    def try_authorise_transaction(self, code, amount, **accounts):
        '''
        Tries to authorise transaction or logs it as declined because of money shortage.
        Assume that form_account has already selected for update 
        and therefore is robust to race conditions.
        '''
        from_account, to_account = self._validate_base_accounts(**accounts)
        amount_for_reserve = self.get_amount_for_reserve(amount)
        if from_account.amount < amount_for_reserve:
            # decline
            try:
                self.create(
                    code=code, status=TRANSACTION_MONEY_SHORTAGE_STATUS)
            # it is ok if transaction has already been processed
            except IntegrityError:
                pass
            raise IssuerTransactionError(
                TRANSACTION_ERROR_NOT_ENOUGH_MONEY)
        try:
            return self._create_with_transfer(
                from_account=from_account,
                to_account=to_account,
                code=code, amount=amount_for_reserve,
                status=TRANSACTION_AUTHORIZATION_STATUS)
        except IntegrityError:  # transaction have already been processed
            raise IssuerTransactionError(TRANSACTION_ERROR_ALREADY_DONE)

    @transaction.atomic  # too many atomics in prod -- bad for perfomance
    def present_transaction(self, code, billable_amount,
                            settlement_amount, **accounts):
        '''
        Rollbacks authorisation transaction, 
        than immediately runs payment transaction to our local setlement account.
        Accepts 3 types of acccount:
        - from_account
        - to_account
        - extra_account -
        account to which difference btw billable and settlement will be transfered

        Returns presented transaction, not rollbacked one.
        '''
        # TODO: in real production all changes in account amounts should be bulked.
        # It's better to bulk them on lower level, may be custom extention for connector,
        # and let code on higher levels of abstractions call rollbacks and
        # presentment methods one by one.
        billable_amount = decimal.Decimal(billable_amount)
        settlement_amount = decimal.Decimal(settlement_amount)
        from_account, to_account = self._validate_base_accounts(**accounts)
        amount_diff = billable_amount - settlement_amount
        extra_account = accounts.get('extra_account')
        if billable_amount != settlement_amount and not extra_account:
            raise ValueError('Extra account needed')
        try:
            # TODO: checks for transactions "sanity" should be placed here
            # from_account should be equal from_account
            self._rollback(code)
        except Transaction.DoesNotExist:
            # there was no authorisation transaction
            raise IssuerTransactionError(
                TRANSACTION_ERROR_DOES_NOT_EXISTS)
        except IntegrityError:
            # transaction was already rollbacked
            # TODO: place for consistency checking
            # What if transactions was rollback, but was not presented?
            raise IssuerTransactionError(
                TRANSACTION_ERROR_ALREADY_DONE)
        try:
            presntment_transaction = self._create_with_transfer(
                from_account=from_account, to_account=to_account,
                code=code, status=TRANSACTION_PRESENTMENT_STATUS,
                amount=settlement_amount)
        except IntegrityError:
            # rollback was not done but presentment transaction was created
            # TODO: should definetly go through consistency checking
            raise IssuerTransactionError(TRANSACTION_ERROR_ALREADY_DONE)

        if not amount_diff:
            return presntment_transaction
        # Transfer amount difference to extra_account
        presntment_transaction.add_transfer(
            from_account, extra_account, amount_diff)
        return presntment_transaction

    def rollback_late_presentment(self, code):
        '''
        Rollback transaction which was late for presentment
        '''
        try:
            return self._rollback(code,
                                  TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS)
        except IntegrityError:
            pass  # ok if already rollbacked

    def settle_day_transactions(self, amount, from_account, to_account):
        '''
        Logs day settlement as our inner transfers.
        Indempotent to multiple runs
        '''
        code = self.get_code_for_date_and_status(TRANSACTION_SETTLEMENT_STATUS)
        try:
            return self._create_with_transfer(
                from_account=from_account, amount=amount,
                to_account=to_account, code=code,
                status=TRANSACTION_SETTLEMENT_STATUS)
        except IntegrityError:
            return self.get(code=code,
                            status=TRANSACTION_SETTLEMENT_STATUS)

    def load_money(self, amount, from_account, to_account):
        '''
        Logs loading money as transfering some "external" account
        '''
        code = UniqueIDGenerator().get_new(length=TRANSACTION_ID_LENGTH)
        return self._create_with_transfer(from_account=from_account,
                                          to_account=to_account, code=code,
                                          status=TRANSACTION_LOAD_MONEY_STATUS,
                                          amount=amount)

    # TODOL cover with tests
    def get_code_for_date_and_status(self, status):
        '''
        Helper for generating unique code for our "service" transactions
        like transfering settlements or loading money
        '''
        today = datetime.date.today()
        return ''.join([status.upper(), today.strftime('%Y%m%d')])

    # TODO: need perfomace optimization. Though its not critical as runs at
    # the background
    def get_non_presented_transactions_before(self, created_before_dt):
        '''
        Filter transactions that were created before specific date and were not presented
        '''
        filter_range = [
            created_before_dt - datetime.timedelta(days=1),
            created_before_dt]
        authorized_transactions_codes = self.filter(
            created_at__range=filter_range,
            status=TRANSACTION_AUTHORIZATION_STATUS).\
            values_list('code', flat=True)
        completed_transaction_codes = self.filter(
            status=TRANSACTION_PRESENTMENT_STATUS,
            code__in=authorized_transactions_codes).\
            values_list('code', flat=True)
        completed_transaction_codes = {
            code: 1 for code in completed_transaction_codes}
        return filter(
            lambda code: completed_transaction_codes.get(code) is None,
            authorized_transactions_codes)

    def get_amount_for_reserve(self, amount):
        '''
        Calculates real ammount that have to be stored including overhead
        '''
        return decimal.Decimal(amount) * \
            decimal.Decimal((100 + AUTHORISATION_OVERHEAD) / 100)

    def _validate_base_accounts(self, **accounts):
        '''
        Helper for validating that required accounts are presented
        '''
        from_account = accounts.get('from_account')
        if not from_account:
            raise ValueError('from_account is required')
        to_account = accounts.get('to_account')
        if not to_account:
            raise ValueError('to_account is required')
        return from_account, to_account

    @transaction.atomic  # can affect perfomance badly -- to long transaction
    def _create_with_transfer(self, *args, **kwargs):
        '''
        Extends basic create transaction functionality with modifying account balances 
        and logging transfers.
        Accepts basic create arguments + "from" and "to" accounts.
        "from_account" and "to_account" and "amount" are required.
        "From" account should be selected for update to hold proper amount of money.
        Throws IntegrityError on code + status duplication.
        '''
        from_account, to_account = self._validate_base_accounts(**kwargs)
        amount = kwargs.get('amount')
        if amount is None:
            raise ValueError('"amount" kwarg is required')
        for key in ['from_account', 'to_account', 'amount']:
            del kwargs[key]
        with transaction.atomic():  # for correct Integrity error processing
            issuer_transaction = self.create(*args, **kwargs)
        issuer_transaction.add_transfer(from_account, to_account, amount)
        return issuer_transaction

    @transaction.atomic
    def _rollback(self, code, rollback_status=TRANSACTION_ROLLBACKED_STATUS):
        '''
        Rollbacks existed authorisation transaction if it wasn't rollbacked already
        Raises DoesNotExist for fake code, Type or ValueError for invalid code
        Raises IntegrityError on already rollbacked transaction.
        '''
        authorization_transaction = self.get(
            status=TRANSACTION_AUTHORIZATION_STATUS, code=code)
        with transaction.atomic():
            rollback_transaction = self.create(
                code=code, status=rollback_status)
        # Don't use select_for_update here as it is redundant:
        # Our authorisation system proved that account has enough money already
        for transfer in authorization_transaction.transfers.\
                select_related('account').all():
            rollback_transaction.transfer_amount(
                transfer.account, -transfer.amount)
        return rollback_transaction


class Transaction(models.Model):

    '''
    Stores transaction meta info
    '''

    code = models.CharField(
        verbose_name='Transaction ID',
        db_index=True, max_length=TRANSACTION_ID_LENGTH)
    created_at = models.DateTimeField(
        verbose_name='Created at', auto_now_add=True)
    human_readable_description = models.TextField(
        verbose_name='Human readable description', null=True, blank=True)
    base64_description = models.TextField(
        verbose_name='JSON from schema in base64', null=True, blank=True)
    status = models.CharField(
        verbose_name='Status', max_length=1,
        choices=TRANSACTION_STATUS_CHOICES)

    objects = TransactionManager()

    @transaction.atomic
    def add_transfer(self, from_account, to_account, amount):
        '''
        Transfers sum from one account to another in one database transaction
        '''
        self.transfer_amount(to_account, amount)
        self.transfer_amount(from_account, -amount)

    def transfer_amount(self, account, amount):
        '''
        Helper for saving transfer for one participant
        '''
        account.modify_amount(amount)
        self.transfers.create(account=account, amount=amount)

    # Update descriptions logic
    # Was deleberately taken out form transaction generation
    # As transaction manager should know how to create transaction
    # nd transaction itself is responsible for displaying to user
    def update_descriptions(self, info_in_json):
        '''
        Forms short description for user
        And saves whole json in base64
        '''
        self.human_readable_description = \
            self.generate_human_readable_description(
                info_in_json=info_in_json)
        # TODO: can be non utf-8 encodings
        # we should manage encoding according to our headers
        self.base64_description = dict_to_base64(info_in_json)
        update_fields = ['human_readable_description', 'base64_description']
        self.save(
            update_fields=update_fields)

    # TODO:
    def generate_human_readable_description(self, **kwargs):
        '''
        Stub for generationg user dscription according to transaction state
        and input info
        '''
        return self.get_status_display()

    class Meta:
        unique_together = ('code', 'status')

    class Errors:
        '''
        Incapsulates error codes.
        Makes imports simplier
        '''
        ALREADY_DONE = TRANSACTION_ERROR_ALREADY_DONE
        NOT_ENOUGH_MONEY = TRANSACTION_ERROR_NOT_ENOUGH_MONEY
        DOES_NOT_EXISTS = TRANSACTION_ERROR_DOES_NOT_EXISTS
        INVALID_CONFIGURATION = TRANSACTION_ERROR_INVALID_CONFIGURATION
        INVALID_FORMAT = TRANSACTION_ERROR_INVALID_FORMAT
        INVALID_USER = TRANSACTION_ERROR_INVALID_USER
