from django.db import models


CARD_ID_LENGTH = 8
#TODO: what are real precision requirements??
AMOUNT_PRECISION_SETTINGS = {
    'max_digits': 19,
    'decimal_places': 4
}

class Account(models.Model):
    '''
        Stores current account balance
    '''
    id = models.CharField(verbose_name='Account ID', max_length=CARD_ID_LENGTH, primary_key=True)
    name = models.CharField(verbose_name='Name', max_length=255) # max possible length for mysql back end
    amount = models.DecimalField(verbose_name='Amount', default = 0.0, **AMOUNT_PRECISION_SETTINGS)
    reserved_amount = models.DecimalField(verbose_name='Reserved amount', default = 0.0, **AMOUNT_PRECISION_SETTINGS)

    @property
    def free_amount(self):
        return self.amount - self.reserved_amount


class AccountDayLog(models.Model):
    '''
        Stores account balance for some point in time.
        Creates new entries for each day after settlement.
    '''
    #TODO: how to deal with reserved amount for the curr day which wasn't presented yet?
    # seems like product desigion

    account = models.ForeignKey(Account, verbose_name = 'Account')
    day = models.DateField(verbose_name='Date')
    amount = models.DecimalField(verbose_name='Amount', default = 0.0, **AMOUNT_PRECISION_SETTINGS)
    reserved_amount = models.DecimalField(verbose_name='Reserved amount', default = 0.0, **AMOUNT_PRECISION_SETTINGS)

    class Meta:
        unique_together = ('account', 'day')


TRANSACTION_ID_LENGTH = 9
TRANSACTION_STATUS_CHOICES = (
    ('a', 'Authorization'),
    ('p', 'Presentment'),
    ('s', 'Money shortage'),      # transaction desclined because of money shortage
    ('l', 'Presentment is late'), # transaction declined because there was no presentment during T + 1 day
)

class Transaction(models.Model):
    '''
        Stores transaction meta info
    '''
    id = models.CharField(verbose_name='Transaction ID', max_length=TRANSACTION_ID_LENGTH, primary_key=True)
    created_at = models.DateTimeField(verbose_name='Created at', auto_now_add = True)
    status = models.CharField(verbose_name='Status', max_length=1, choices=TRANSACTION_STATUS_CHOICES)


class Transfer(models.Model):
    '''
        Store transfers to accounts. Transfers can be negative.
        The accounting equation must always hold, i.e. for each Transaction, the total debits equalthe total credits of Transfers.
    '''
    #TODO: consistency checks for transfer

    transaction = models.ForeignKey(Transaction, verbose_name = 'Transaction')
    account = models.ForeignKey(Account, verbose_name = 'Account')
    ammount = models.DecimalField(verbose_name='Amount', default = 0.0, **AMOUNT_PRECISION_SETTINGS)
    
