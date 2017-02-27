from django.db import models

from processing.models.accounts_day_log import AccountDayLog
from processing.models.transfers import Transfer
from card_issuing_excercise.settings import AMOUNT_PRECISION_SETTINGS 
from card_issuing_excercise.utils import date_from_ts, to_start_day_from_ts, \
                                          is_in_future


CARD_ID_LENGTH = 8
#TODO: refactor short repr usage -- should use constans with verbose names instead
ACCOUNT_TYPES = (
    ('b', 'Basic account'),
    ('r', 'Reserved account')
)

class UserAccountManager(models.Manager):

    '''
    Miscellaneous changes of default manager functionality.
    '''

    # Use inheritance not mixins, as all new added functionality won't be reused elsewhere

    def get_account_for_update(self, account_id):
        '''
        Prefetches related "real" accounts safely for next update,
        using select_for_update.
        '''
        # TODO: chck how select for update in subquery works
        return self.prefetch_related(
                    models.Prefetch(
                       'accounts', 
                        queryset=Account.objects.select_for_update()
                    )
               ).get(id = account_id)

    def create(self, *args, **kwargs):
        '''
        Creates user accounts with all "real" accounts linked.
        Accepts basic user account arguments and needed link_types in kwargs (as array)
        '''
        linked_account_types = self._get_linked_account_types(**kwargs)
        if kwargs.get('linked_account_types'):
            del kwargs['linked_account_types']
        user_account = super(UserAccountManager, self).create(*args, **kwargs)
        for account_type in linked_account_types:
            user_account.accounts.create(account_type=account_type)
        return user_account
 
    def _get_linked_account_types(self, **kwargs):
        return kwargs.get('linked_account_types') or \
               [ account_type[0] for account_type in ACCOUNT_TYPES ]


class UserAccountsUnion(models.Model):

    '''
    Stores users' current total balance.
    Don't take part in transactions and is used to consolidate 2 "real" accounts:
     - base account and reserved account
    '''

    id = models.CharField(verbose_name='Account ID', max_length=CARD_ID_LENGTH, primary_key=True)
    created_at = models.DateTimeField(verbose_name='Created at', auto_now_add=True)
    name = models.CharField(verbose_name='Name', max_length=255) # max possible length for mysql back end
    user = models.OneToOneField('auth.User', verbose_name='Owner')

    objects = UserAccountManager()

    @property
    def current_amounts_tuple(self):
        '''
        Tuple representation of both types of amounts that user have:
        - total amount (reserved + available) and available.
        '''
        return (self.real_amount, self.base_amount)
   
    @property
    def real_amount(self):
        '''
        Sum of available amount and reserved amounts
        '''
        return self.base_amount + self.reserved_amount

    @property
    def base_amount(self):
        '''
        Shortcut for currently available sum
        '''
        return self._get_account_amount_by_type('b')

    @property
    def available_amount(self):
        '''
        More readable alias for base amount
        '''
        return self.base_amount

    @property
    def reserved_amount(self):
        '''
        Shortcut for currently reserved sum
        '''
        return self._get_account_amount_by_type('r')

    @property
    def base_account(self):        
        '''
        Shortcut for base account, which stores currently avialable sum of money.
        '''
        return self._get_account_by_type('b')

    @property
    def reserved_account(self):
        '''
        Shortcut for reserved account, which stores currently reserved sum of money.
        '''
        return self._get_account_by_type('r')

    def _get_account_by_type(self, account_type):
        '''
        Helper for getting related account by type
        '''
        return self.accounts.filter(account_type=account_type).first()

    def _get_account_amount_by_type(self, account_type):
        '''
        Helper for getting related account amount by account_type
        '''
        account = self._get_account_by_type(account_type)
        if not account: return 0
        return account.amount

    def get_amounts_for_ts(self, date_ts=None):
        '''
        Returns amount for particular point at time.
        For non set date_ts returns current amount.
        Return two amounts: real_amount (base + reserved) and available amount (just base)
        '''
        if not date_ts: return self.current_amounts_tuple
        if is_in_future(date_ts): return self.current_amounts_tuple
        start_day_date = to_start_day_from_ts(date_ts)
        date = date_from_ts(date_ts)
        if self.created_at > date: return (0, 0)
        if self.created_at > start_day_date:
            # don't have any logs yet at this point
            base_amount, reserved_amount = (0, 0)
        else:
            base_amount, reserved_amount = self._get_amounts_for_date(start_day_date)
        base_amount_diff, reserved_amount_diff = self._roll_forward_in_time_range(start_day_date, date)
        return (base_amount + base_amount_diff + reserved_amount + reserved_amount_diff), \
               (base_amount + base_amount_diff)

    def _get_amounts_for_date(self, start_day_date):
        '''
        Find amount for particular point at time.
        Don't check weather they exists or not.
        '''
        nearest_accounts = self.accounts.filter(account_logs__date=start_day_date).\
                                         values('account_type', 'account_logs__amount')
        nearest_accounts = {account['account_type']: account['account_logs__amount']
                            for account in nearest_accounts}
        return nearest_accounts.get('b', 0), nearest_accounts.get('r', 0)

    def _roll_forward_in_time_range(self, begin_date, end_date):
        '''
        Calculates the result of all transfers in given time period
        for all linked accounts
        '''

        transfer_diffs = Transfer.objects.\
            filter(transaction__created_at__range=[begin_date, end_date]).\
            filter(account_id__in=[a.id for a in self.accounts.all()]).\
            values('account__account_type').\
            annotate(amount_diff = models.Sum('amount'))
        transfer_diffs = {t['account__account_type']:t['amount_diff'] for t in transfer_diffs}
        return transfer_diffs.get('b', 0), transfer_diffs.get('r', 0)
        

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
        self.amount = models.F('amount') + amount
        self.save(update_fields=['amount'])
        self.refresh_from_db() # to get rid of F() effect and prevent any double changes

