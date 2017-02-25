from django.db import models, transaction, F


CARD_ID_LENGTH = 8
#TODO: what are real precision requirements??
AMOUNT_PRECISION_SETTINGS = {
    'max_digits': 19,
    'decimal_places': 4
}
ACCOUNT_TYPES = (
    ('b', 'Basic account'),
    ('r', 'Reserved account')
)

class UserAccountManager(models.Manager):
    def create(self, *args, **kwargs):
        '''
            Creates user accounts with all "real" accounts linked.
            Accepts basic user account arguments and needed link_types in kwargs (as array)
        '''
        linked_account_types = self._get_linked_account_types(**kwargs)
        if kwargs.get('linked_account_types'):
            del kwargs['linked_account_types'
        user_account = super(UserAccountManager, self).create(*args, **kwargs)
        for account_type in linked_account_types:
            user_account.accounts.create(account_type=account_type)
        return user_account
 
    def _get_linked_account_types(self, **kwargs):
        return kwargs.get('linked_account_types') or \
             [ account_type[0] for account_type in ACCOUNT_TYPES ]


class UserAccountsUnion(models.Model);
    '''
        Stores users' current total balance.
        Don't take part in transactions and is used to consolidate 2 "real" accounts:
        - base account and reserved account
    '''
    id = models.CharField(verbose_name='Account ID', max_length=CARD_ID_LENGTH, primary_key=True)
    name = models.CharField(verbose_name='Name', max_length=255) # max possible length for mysql back end
    user = models.ForeignKey('auth.User', verbose_name='Owner')

    objects = UserAccountManager()

    @property
    def available_amount(self):
        return self.base_amount - self.reserved_amount

    @property
    def base_amount(self):
        return self._get_account_amount_by_type('b')

    @property
    def reserved_amount(self):
       return self._get_account_amount_by_type('r')

    def _get_account_amount_by_type(self, account_type):
        account = self.accounts.filter(account_type=account_type).first()
        if not account: return 0
        return account.amount

class Account(models.Model):
    '''
        Real agent that takes part in transfering money. 
        All user's money is stored in basic account. Reserved account holds info about reservations       
    '''
    account_type = models.CharField(verbose_name="Account type", max_length=1, choices=ACCOUNT_TYPES)
    amount = models.DecimalField(verbose_name='Amount', default=0.0, **AMOUNT_PRECISION_SETTINGS)
    user_account = models.ForeignKey(UserAccountsUnion, related_name='accounts', verbose_name='User account')

    def modify_amount(self, amount):
        '''
            Just modifies amount without performing any additional checks on sums
        '''
        self.amount = F('amount') + amount
        self.save(update_fields=['amount'])
        self.refresh_from_db() # to get rid of F() effect and prevent any double changes


class AccounDayLogManager(models.Model):
    def find_amount_for_ts(self):
        '''
            Find amount for certain ts by filtering log of that day and \
            rolls forward all transaction btw start of day and requested ts.
        '''
        raise NotImplemente

class AccountDayLog(models.Model):
    '''
        Stores account balance for some point in time.
        Creates new entries for each day after settlement.
    '''
    #TODO: how to deal with reserved amount for the curr day which wasn't presented yet?
    # seems like product desigion

    account = models.ForeignKey(Account, verbose_name = 'Account')
    day = models.DateField(verbose_name='Date')
    amount = models.DecimalField(verbose_name='Amount', default=0.0, **AMOUNT_PRECISION_SETTINGS)

    class Meta:
        unique_together = ('account', 'day')


TRANSACTION_ID_LENGTH = 9
TRANSACTION_STATUS_CHOICES = (
    ('a', 'Authorization'),
    ('p', 'Presentment'),
    ('s', 'Money shortage'),      # transaction declined because of money shortage
    ('l', 'Presentment is late'), # transaction declined because there was no presentment during T + 1 day
    ('r', 'Rollback'),            # rollback authorisation transaction for presentment
)
#TODO: do a and p transactions have different ids?

class TransactionManager(models.Manager):
    '''
        Proovdes base apic for transaction management for views and management commands.
    '''
    def try_authorise_transaction(self, code, from, to):
        '''
            Tries to authorise transaction or logs it as declined because of money shortage.
        '''
        raise NotImplemented

    def present_transaction(self, code):
       '''
           Rollbacks authorisation transaction, than immediately runs paiment transaction to our local setlement account.
       '''
       raise NotImplemented

    def rollback_late_presentments(self, **filter_criteria):
       '''
           Filter all transactions according filter criteria and rollbacks ones without presentment
       '''
       raise NotImplemented

    @transaction.atomic # can affect perfomance badly -- to long transaction
    def _create_with_transfer(self, *args, **kwargs):
        '''
            Extends basic create transaction functionality with modifying account balances 
            and logging transfers.
            Accepts basic create arguments + "from" and "to" accounts.
            "From" and "to" are required.
            Form account should be selected for update to hold proper amount of money
        '''
        from_account = kwargs.get('from') or raise ValieError('"From" kwarg is requried')
        to_account = kwargs.get('to') or raise ValieError('"To" kwarg is requried')
        for key in ['from', 'to']:
             del kwargs[key]
        transaction = self.create(*args, **kwargs)
        transaction.transfer_amount(to_account, amount)
        transaction.transfer_amount(from_account, -amount)
        return transaction

    @transaction.atomic
    def _rollback(self, code, rollback_status='r'):
        '''
            Rollbacks existed authorisation transaction if it wasn't rollbacked already
            Raises DoesNotExist for fake code, Type or ValueError for invalid code
            Raises IntegrityError on already rollbacked transaction.
        '''
        authorization_transaction = self.get(status='a', code=code)
        with transaction.atomic():
            rollback_transaction = self.create(code=code, rollback_status='r')
        for transfer in authorization_transaction.transfers.all():
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
    def transfer_amount(self, account, amount):
        account.modify_amount(amount)
        self.transfers.create(account=account, amount=amount)
 
    def Meta:
        unique_together = ('code', 'status')

class Transfer(models.Model):
    '''
        Store transfers to accounts. Transfers can be negative.
        The accounting equation must always hold, i.e. for each Transaction, the total debits equalthe total credits of Transfers.
    '''
    #TODO: consistency checks for transfer

    transaction = models.ForeignKey(Transaction, related_name='transfers', verbose_name = 'Transaction')
    account = models.ForeignKey(Account, # Foreign key is already index in mysql -- so no db_index needed
                                related_name='transfers', verbose_name='Account')
    amount = models.DecimalField(verbose_name='Amount', default=0.0, **AMOUNT_PRECISION_SETTINGS)
    
