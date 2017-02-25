from django.core.management.base import BaseCommand, CommandError

from processing.models import Account, Transaction, Transfers


class BatchSettleCommand(BaseCmmand):
    help = 'Batch process for settlement and accounting revenue'
