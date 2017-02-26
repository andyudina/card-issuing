from django.db import models, \
                      transaction, IntegrityError

from card_issuing_excercise.settings import AUTHORISATION_OVERHEAD


TRANSACTION_ID_LENGTH = 9

TRANSACTION_AUTHORIZATION_STATUS = 'a'
TRANSACTION_PRESETMENT_STATUS = 'p'
TRANSACTION_MONEY_SHORTAGE_STATUS = 's'
TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS = 't'
TRANSACTION_ROLLBACKED_STATUS = 'r'
TRANSACTION_LOAD_MONEY_STATUS = 'l'

TRANSACTION_STATUS_CHOICES = (
    (TRANSACTION_AUTHORIZATION_STATUS,           'Authorization'),
    (TRANSACTION_PRESETMENT_STATUS,              'Presentment'),
    # transaction declined because of money shortage
    (TRANSACTION_MONEY_SHORTAGE_STATUS,          'Money shortage'),   
    # transaction declined because there was no presentment during T + 1 day           
    (TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS, 'Presentment is exceeded TTL'), 
    # rollback authorisation transaction for presentment
    (TRANSACTION_ROLLBACKED_STATUS,              'Rollback'),                    
    # special transaction for loading money, 
    # don't need authorisation - presentment scheme
    (TRANSACTION_LOAD_MONEY_STATUS,              'Load money'),                  
)

class IssuerTransactionError(ValueError):

    '''
    Custom errors for transaction management.
    Possible error codes:
    - already_done (for reduplicated transactions)
    - not_enough_money
    '''
    pass


#TODO: need more pure functions for better unit testing. Too much side effects is a pain
#TODO: pass all arguments in kwargs -- it will be much more readable
class TransactionManager(models.Manager):

    '''
    Provides base API for transaction management for views and management commands.
    Don't know anything about account types.
    Raises IssuerTransactionError with string error code on failure 
    '''

    def try_authorise_transaction(self, code, amount, **accounts):
        '''
        Tries to authorise transaction or logs it as declined because of money shortage.
        Assume that form_account has already selected for update and therefore is safe to race conditions.
        '''
        from_account, to_account = self._validate_base_accounts(**accounts)
        amount_for_reserve = self.get_amount_for_reserve(amount)
        if from_account.available_amount < amount_for_reserve:
            # decline
            try:
                self.create(code=code, status=TRANSACTION_MONEY_SHORTAGE_STATUS)
            except IntegrityError: # it is ok if transaction has alreafy been processed
                pass
            raise IssuerTransactionError('not_enough_money')
        try:
            self._create_with_transfer(from_acount=from_account, to_account=to_account,
                                       code=code, status=TRANSACTION_AUTHORIZATION_STATUS, 
                                       amount=amount_for_reserve)
        except IntegrityError: # transaction have already been processed
            raise IssuerTransactionError('already_done')

    @transaction.atomic # too many atomics in prod -- bad for perfomance
    def present_transaction(self, code, billable_amount, 
                            settlement_amount, **accounts):
        '''
        Rollbacks authorisation transaction, than immediately runs payment transaction to our local setlement account.
        Accepts 3 types of acccount:
        - from_account
        - to_account
        - extra_account. -- account to which difference btw billable and settlement will be transfered
        '''
        # TODO: in real production all changes in account amounts should be bulked. 
        # It's better to bulk them on lower level, mb custom extention for connector, 
        # and let code on higher levels of abstractions call rollbacks and presentment methods one by one.
        from_account, to_account = self._validate_base_accounts(**accounts)
        amount_diff = billable_amount - settlement_amount
        if amount_diff != 0 and not accounts.get('extra_account'):
            raise ValueError('Extra account needed')
        try:
            # TODO: checks for transactions "sanity" should be placed here
            # from_account should be equal from_account 
            rollback_transaction = self._rollback(code)
        except DoesNotExist:
            # there was no authorisation transaction
            raise IssuerTransactionError('already_done')
        except IntegrityError:
            # transaction was already rollbacked
            # TODO: place for consistency checking
            # What if transactions was rollback, but was not presented?
            raise IssuerTransactionError('already_done')
        try:
            transaction = self._create_with_transfer(from_acount=from_account, to_account=to_account,
                                       code=code, status=TRANSACTION_PRESETMENT_STATUS, amount=billable_amount)
        except IntegrityError:
            # rollback was not done but presentment transaction was created
            # TODO: should definetly go through consistency checking
            raise IssuerTransactionError('already_done')
        
        if not amount_diff: return
        # Transfer amount difference to extra_account
        transaction.add_transfer(from_account, extra_account, amount_diff)

    def rollback_late_presentment(self, code):
        '''
        Rollback transaction which was late for presentment
        '''
        try:
            return self._rollback(code, status=TRANSACTION_PRESENTMANT_IS_TOO_LATE_STATUS)
        except IntegrityError:
            pass # ok if already rollbacked

    #TODO: need perfomace optimization. Though its not critical as runs at the background
    def get_non_presented_transactions_before(self, created_before_dt):
        '''
        Filter transactions that were created before specific date and were not presented
        '''
        filter_range = [
            created_before_dt - datetime.timedelta(days=1), 
            created_before_dt]
        authorized_transactions_codes = self.filter(created_at__range=filter_range, status=TRANSACTION_AUTHORIZATION_STATUS).\
                                             values_list('code', flat=True)
        completed_transaction_codes = self.filter(status=TRANSACTION_PRESETMENT_STATUS, code__in=authorized_transactions_codes).\
                                      values_list('code', flat=True)
        completed_transaction_codes = {t.code: 1 for code in completed_transaction_codes}
        return filter(lambda code: completed_transactions.get(code) is None, authorized_transactions_codes)


    def get_amount_for_reserve(self, amount):
        '''
        Calculates real ammount that have to be stored including overhead
        '''
        return amount * (100 + AUTHORISATION_OVERHEAD) / 100

    def _validate_base_accounts(self, **accounts):
        '''
        Helper for validating that required accounts are presented
        '''
        from_account = accounts.get('from_account')
        if not from_account: raise ValueError('from_account is required')
        to_account = accounts.get('to_account')
        if not to_account: raise ValueError('to_account is required')
        return from_account, to_account

    @transaction.atomic # can affect perfomance badly -- to long transaction
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
        amount  = kwargs.get('amount')
        if not amount: raise ValueError('"amount" kwarg is required')
        for key in ['from_account', 'to_account', 'amount']:
            del kwargs[key]
        with transaction.atomic(): # for correct Integrity error processing
            transaction = self.create(*args, **kwargs)
        transaction.add_transfer(from_account, to_account, amount)
        return transaction

    @transaction.atomic
    def _rollback(self, code, rollback_status=TRANSACTION_ROLLBACKED_STATUS):
        '''
        Rollbacks existed authorisation transaction if it wasn't rollbacked already
        Raises DoesNotExist for fake code, Type or ValueError for invalid code
        Raises IntegrityError on already rollbacked transaction.
        '''
        authorization_transaction = self.get(status=TRANSACTION_AUTHORIZATION_STATUS, code=code)
        with transaction.atomic():
            rollback_transaction = self.create(code=code, rollback_status=rollback_status)
        # Don't use select_for_update here as it is redundant:
        # Our authorisation system proved that account has enough money already
        for transfer in authorization_transaction.transfers.select_related('account').all():
            rollback_transaction.transfer_amount(transfer.account, -transfer.amount)
        return rollback_transaction


class Transaction(models.Model):

    '''
    Stores transaction meta info
    '''

    code = models.CharField(verbose_name='Transaction ID', db_index=True, max_length=TRANSACTION_ID_LENGTH)
    created_at = models.DateTimeField(verbose_name='Created at', auto_now_add=True)
    status = models.CharField(verbose_name='Status', max_length=1, choices=TRANSACTION_STATUS_CHOICES)

    objects = TransactionManager()

    @transaction.atomic
    def add_transafer(self, from_account, to_account, amount):
        '''
        Transfers sum from one account to another in one database transaction
        '''
        self._transfer_amount(to_account, amount)
        self._transfer_amount(from_account, -amount)
    
    def _transfer_amount(self, account, amount):
        '''
        Helper for saving transfer for one participant
        '''
        account.modify_amount(amount)
        self.transfers.create(account=account, amount=amount)
 
    class Meta:
        unique_together = ('code', 'status')

