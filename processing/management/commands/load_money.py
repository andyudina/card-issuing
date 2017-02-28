import decimal

from django.core.management.base import BaseCommand, CommandError

from processing.models import Transaction, UserAccountsUnion


class Command(BaseCommand):
    help = '''Loads money to user account
              Usage: load_money <cardholder> <amount> <currency>'''

    def add_arguments(self, parser):
        parser.add_argument('account_id', type=str)
        parser.add_argument('amount', type=decimal.Decimal)
        parser.add_argument('currency', type=str)

    def handle(self, *args, **options):
        try:
            user_account = UserAccountsUnion.objects.get(id=options.get('account_id'))
        except UserAccountsUnion.DoesNotExist:
            return
        load_money_account = UserAccountsUnion.objects.get_external_load_money_account()
        Transaction.objects.load_money(options.get('amount'),
                                       load_money_account.base_account,
                                       user_account.base_account)
