''' This is stub. Test realisation was skipped '''

from django.test import TestCase

from apps.processing.models.transactions import Transaction


class GetReserveAmount(TestCase):

    '''
    Stub for units for Transaction.objects.get_amount_for_reserve
    '''

    def test__positive_amount__valid_return(self):
        pass

    def test__negative_amount__valid_return(self):
        pass

    def test__valid_non_decimal_amount__valid_return(self):
        pass

        