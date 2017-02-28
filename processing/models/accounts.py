from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned, \
                                   ObjectDoesNotExist
from django.db import models

from processing.models.accounts_day_log import AccountDayLog
from processing.models.transfers import Transfer
from card_issuing_excercise.settings import AMOUNT_PRECISION_SETTINGS 
from card_issuing_excercise.utils import date_from_ts, to_start_day_from_ts, \
                                         is_in_future


CARD_ID_LENGTH = 8
#TODO: refactor short repr usage -- should use constans with verbose names instead

##
## ACCOUNT TYPES
##

# Account types support transfers unification  for authorization accounts:
# Each regular user has 2 accounts for available money and reserved one
# Authorization transaction is processed like transfering btw 
# basic account and reserved account of one user

BASIC_ACCOUNT_TYPE = 'b'
RESERVED_ACCOUNT_TYPE = 'r'
ACCOUNT_TYPES = (
    (BASIC_ACCOUNT_TYPE, 'Basic account'),
    (RESERVED_ACCOUNT_TYPE, 'Reserved account')
)

##
## USER ACCOUNT ROLES
##

# All transfers are unified by roles mechanism:
# we process revenues, settlements and money load the same way as other transactions:
# by transfering amounts from one account to another.
# Transfering money to or from external agents like decreasing dept to Schema during settlement
# or loading money directly to user account is processed like transfering money  to some exteral accounts
# which total amount is not managed by us

REAL_USER_ACCOUNT_ROLE = 'b'
INNER_SETTLEMENT_ACCOUNT_ROLE = 'is'
EXTERNAL_LOAD_MONEY_ACCOUNT_ROLE = 'el'
EXTERNAL_SETTLEMENT_ACCOUNT_ROLE = 'es'
REVENUE_ACCOUNT_ROLE = 'r'

ACCOUNT_ROLE_TYPES = (
    # basic user account
    (REAL_USER_ACCOUNT_ROLE, 'Real user'),
    # account which holds our depts to the Schema
    (INNER_SETTLEMENT_ACCOUNT_ROLE, 'Inner settlement account'),
    # external account from which money is loaded
    (EXTERNAL_LOAD_MONEY_ACCOUNT_ROLE, 'External load money account'),
    # the Schema external account, where we transfer money during settlement
    (EXTERNAL_SETTLEMENT_ACCOUNT_ROLE, 'External settlement account'),
    # Account that holds our revenue
    (REVENUE_ACCOUNT_ROLE, 'Inner revenue account')
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
        # TODO: check how select for update in subquery works
        return self.prefetch_related(
                    models.Prefetch(
                       'accounts', 
                        queryset=Account.objects.select_for_update()
                    )
               ).get(id = account_id)

    # TODO: generate unique card ids on the fly
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

    ##
    # Helpers for creating an retieving special accounts
    ##

    def create_inner_settlement_account(self):
        return self.create_special_account(INNER_SETTLEMENT_ACCOUNT_ROLE)

    def create_external_load_money_account(self):
        return self.create_special_account(EXTERNAL_LOAD_MONEY_ACCOUNT_ROLE)

    def create_external_settlement_account(self):
        return self.create_special_account(EXTERNAL_SETTLEMENT_ACCOUNT_ROLE )

    def create_revenue_account(self):
        return self.create_special_account(REVENUE_ACCOUNT_ROLE)

    def create_special_account(self, role):
        '''
        Helper for creating special account of specified type.
        For simplicity binds it to root user.
        Fails if there is no one.
        Checks if accout already exists and returns it
        instead of creating new one
        '''
        try:
            return self.get(role=role)
        except ObjectDoesNotExist:
            root_user = self._get_root_user()
            return self.create(user=root_user, role=role, 
                               card_id=role, name=role,
                               linked_account_types=[BASIC_ACCOUNT_TYPE,])
        except MultipleObjectsReturned:
            raise ValueError('More than one {} acc'.format(role))

    def _get_root_user(self):
        '''
        Helper which tries to get superuser 
        or raises ValueError
        '''
        try:
            return User.objects.get(username='root', is_superuser=True)
        except User.DoesNotExist:
            raise ValueError('No superuser found')

    def get_inner_settlement_account(self):
        return self.get_special_account_or_none(INNER_SETTLEMENT_ACCOUNT_ROLE)

    def get_external_load_money_account(self):
        return self.get_special_account_or_none(EXTERNAL_LOAD_MONEY_ACCOUNT_ROLE)

    def get_external_settlement_account(self):
        return self.get_special_account_or_none(EXTERNAL_SETTLEMENT_ACCOUNT_ROLE)

    def get_revenue_account(self):
        return self.get_special_account_or_none(REVENUE_ACCOUNT_ROLE)

    #TODO: cover getters with units
    def get_special_account_or_none(self, role):
        try:
            return self.get(role=role)
        # let caller deside what to do if smth bad has happened
        # caller shouldn't know what ind of "bad" occured
        # all errors are equal for him
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            return None



class UserAccountsUnion(models.Model):

    '''
    Stores users' current total balance.
    Don't take part in transactions and is used to consolidate 2 "real" accounts:
     - base account and reserved account
    '''

    # inner card_id should be sensible info.
    # so we user auto increment filed to identify user account instead
    card_id = models.CharField(verbose_name='Account ID', max_length=CARD_ID_LENGTH, 
                               unique=True)
    created_at = models.DateTimeField(verbose_name='Created at', auto_now_add=True)
    name = models.CharField(verbose_name='Name', max_length=255) # max possible length for mysql back end
    user = models.ForeignKey('auth.User', verbose_name='Owner')
    role = models.CharField(verbose_name='Role', max_length=2, 
                            default=REAL_USER_ACCOUNT_ROLE, choices=ACCOUNT_ROLE_TYPES)

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
        return self._get_account_amount_by_type(BASIC_ACCOUNT_TYPE)

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
        return self._get_account_amount_by_type(RESERVED_ACCOUNT_TYPE)

    @property
    def base_account(self):        
        '''
        Shortcut for base account, which stores currently avialable sum of money.
        '''
        return self._get_account_by_type(BASIC_ACCOUNT_TYPE)

    @property
    def reserved_account(self):
        '''
        Shortcut for reserved account, which stores currently reserved sum of money.
        '''
        return self._get_account_by_type(RESERVED_ACCOUNT_TYPE)

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
        return nearest_accounts.get(BASIC_ACCOUNT_TYPE, 0), \
               nearest_accounts.get(RESERVED_ACCOUNT_TYPE, 0)

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
        return transfer_diffs.get(BASIC_ACCOUNT_TYPE, 0), \
               transfer_diffs.get(RESERVED_ACCOUNT_TYPE, 0)
        

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

