'''Management command for loading money to user account'''

import decimal

from django.core.management.base import BaseCommand

from card_issuing_excercise.apps.processing.models import Transaction, \
    UserAccountsUnion
from card_issuing_excercise.apps.currency_converter.converter import \
    Converter


class Command(BaseCommand):

    '''Loads money to user account and logs it as transfer'''

    help = '''Loads money to user account
              Usage: load_money <cardholder> <amount> <currency>'''

    def add_arguments(self, parser):
        parser.add_argument('card_id', type=str)
        parser.add_argument('amount', type=decimal.Decimal)
        parser.add_argument('currency', type=str)

    def handle(self, *args, **options):
        try:
            amount = Converter().get_amount_for_save(options.get('amount'),
                                                     options.get('currency'))
        except Converter.ConverterError:
            print('Can\'t convert currencies')
            return
        try:
            user_account = UserAccountsUnion.objects.get(
                card_id=options.get('card_id'))
        except UserAccountsUnion.DoesNotExist:
            print('User with card_id "{}" does not exist'.
                  format(options.get('card_id')))
            return
        load_money_account = UserAccountsUnion.objects.\
            get_external_load_money_account()
        transaction = Transaction.objects.load_money(
            amount,
            load_money_account.base_account,
            user_account.base_account)
        transaction.update_descriptions(options)
