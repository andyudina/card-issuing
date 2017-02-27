from django.core.management.base import BaseCommand, CommandError

from processing.models import Account, Transaction, Transfer


class LoadMoneyCommand(BaseCommand):
    help = 'Loads money to  user account'
