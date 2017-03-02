'''Tests initialization command'''

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase


from card_issuing_excercise.apps.processing.models.accounts import \
    UserAccountsUnion
from card_issuing_excercise.settings import ROOT_USERNAME


class InitializeBeforeStatup(TestCase):

    '''
    Functional test for initialization on startup 
    management command
    '''

    def test__root_account_exists(self):
        call_command('initialize_before_startup')
        self.assertTrue(
            User.objects.filter(username=ROOT_USERNAME).exists())

    def test__inner_settlement_account_exists(self):
        call_command('initialize_before_startup')
        self.assertIsNotNone(
            UserAccountsUnion.objects.get_inner_settlement_account())

    def test__external_load_money_account_exists(self):
        call_command('initialize_before_startup')
        self.assertIsNotNone(
            UserAccountsUnion.objects.get_external_load_money_account())

    def test__external_settlement_exists(self):
        call_command('initialize_before_startup')
        self.assertIsNotNone(
            UserAccountsUnion.objects.get_external_settlement_account())

    def test__revenue_account_exists(self):
        call_command('initialize_before_startup')
        self.assertIsNotNone(
            UserAccountsUnion.objects.get_revenue_account())
