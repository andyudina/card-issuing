''' This is stub. Test realisation was skipped '''

from django.test import TestCase

from apps.processing.models.transactions import Transaction


class SettlementTransaction(TestCase):

    '''
    Stub for units for Transaction.objects.settle_day_transactions
    '''

    def test__valid_transaction__settlement_account_amount_changed(self):
        pass

    def test__valid_transaction__settlement_transfer_exists(self):
        pass

    def test__duplicate_transaction__throw_error(self):
        pass

    def test__duplicate_transaction__settlement_amount_not_modified(self):
        pass
        
