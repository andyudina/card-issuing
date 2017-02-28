from django.apps import AppConfig
from django.db import IntegrityError


class ProcessingConfig(AppConfig):
    name = 'processing'

    def ready(self):
        '''
        Create superuser and special accounts on startup
        '''
        self._create_root_if_not_exists()
        self._create_special_accounts()

    def _create_root_if_not_exists(self):
        from django.contrib.auth.models import User
        from card_issuing_excercise.settings import ROOT_PASSWORD
        try:
            User.objects.create_superuser('root', 'root', ROOT_PASSWORD)
        except IntegrityError:
            pass

    def _create_special_accounts(self):
        from .models import UserAccountsUnion
        UserAccountsUnion.objects.create_inner_settlement_account()
        UserAccountsUnion.objects.create_external_load_money_account()
        UserAccountsUnion.objects.create_extra_settlement_account()
        UserAccountsUnion.objects.create_revenue_account()
