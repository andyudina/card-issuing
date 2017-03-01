from django.db import models

from card_issuing_excercise.settings import AMOUNT_PRECISION_SETTINGS 


class Transfer(models.Model):

    '''
    Store transfers to accounts. Transfers can be negative.
    The accounting equation must always hold, i.e. for each Transaction, the total debits equalthe total credits of Transfers.
    '''

    #TODO: consistency checks for transfer

    transaction = models.ForeignKey('Transaction', related_name='transfers', verbose_name = 'Transaction')
    account = models.ForeignKey('Account', # Foreign key is already index in mysql -- so no db_index needed
                                related_name='transfers', verbose_name='Account')
    amount = models.DecimalField(verbose_name='Amount', default=0.0, **AMOUNT_PRECISION_SETTINGS)

