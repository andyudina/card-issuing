from django.core.management.base import BaseCommand, CommandError

from processing.models import Account, Transaction, Transfers


class LoadMoneyCommand(BaseCmmand):
    help = 'Loads money to  user account'
