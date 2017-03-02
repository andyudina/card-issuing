'''Model for caching balance for specified day'''

from django.db import models

from card_issuing_excercise.settings import AMOUNT_PRECISION_SETTINGS


class AccountDayLog(models.Model):

    '''
    Stores account balance for some point in time.
    Creates new entries for each day after settlement.
    '''

    account = models.ForeignKey(
        'Account', related_name='account_logs', verbose_name='Account')
    date = models.DateField(verbose_name='Date')
    amount = models.DecimalField(
        verbose_name='Amount', default=0.0, **AMOUNT_PRECISION_SETTINGS)

    class Meta:
        unique_together = ('account', 'date')
