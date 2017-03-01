from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from processing.models import UserAccountsUnion
from card_issuing_excercise.settings import ROOT_PASSWORD


class Command(BaseCommand):
    help = 'Create necessary models on startup'

    def handle(self, *args, **options):
        '''
        Create superuser and special accounts on startup
        '''
        self._create_root_if_not_exists()
        self._create_special_accounts()

    def _create_root_if_not_exists(self):
        try:
            User.objects.create_superuser('root', 'root', ROOT_PASSWORD)
        except IntegrityError:
            pass

    def _create_special_accounts(self):
        UserAccountsUnion.objects.create_inner_settlement_account()
        UserAccountsUnion.objects.create_external_load_money_account()
        UserAccountsUnion.objects.create_extra_settlement_account()
        UserAccountsUnion.objects.create_revenue_account()

