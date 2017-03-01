import decimal

from django.core.management.base import BaseCommand, CommandError

from apps.processing.models import Transaction, UserAccountsUnion
from currency_converter.converter import Converter


class Command(BaseCommand):
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
        except Converter.ConverterError as e:
            print('Can\'t convert currencies')
            return
        try:
            user_account = UserAccountsUnion.objects.get(card_id=options.get('card_id'))
        except UserAccountsUnion.DoesNotExist:
            print('User with card_id "{}" does not exist'.\
                   format(options.get('card_id')))
            return
        load_money_account = UserAccountsUnion.objects.get_external_load_money_account()
        Transaction.objects.load_money(options.get('amount'),
                                       load_money_account.base_account,
                                       user_account.base_account)
