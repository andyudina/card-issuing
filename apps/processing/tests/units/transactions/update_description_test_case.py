import decimal
from base64 import b64decode
from json import loads
from unittest import skip

from django.test import TestCase

from utils import dict_to_base64
from utils.tests import TransactionBaseTestCase


class UpdateDescription(TransactionBaseTestCase):

    '''
    Test for updating sdescriptions and generating base64
    '''

    def setUp(self):
        self.transaction = self.create_transaction()

    ##
    # Helpers
    ##
    def check_base64_dict(self, base64str, dict_to_compare):
        '''
        Converts base64str to dict and compares it with initial
        '''
        result_dict = loads(b64decode(
                            base64str.encode()).decode())
        self.assertDictEqual(result_dict, dict_to_compare)

    ##
    # Tests
    ##

    @skip('Not implemented yet')
    def test__human_description_for_presentment_transaction__all_fields_rendered(self):
        pass

    @skip('Not implemented yet')
    def test__human_description_for_authorization_transaction__all_fields_rendered(self):
        pass

    @skip('Not implemented yet')
    def test__human_description_for_load_money_transaction__all_fields_rendered(self):
        pass

    def test__base64_description_for_empty_dict__is_empty_string(self):
        base64str = dict_to_base64({})
        self.assertEqual(base64str, '')

    def test__base64_description_for_ascii__is_valid(self):
        initial_dict = {'test': 'test'}
        base64str = dict_to_base64(initial_dict)
        self.check_base64_dict(base64str, initial_dict)

    def test__base64_description_for_unicode__is_valid(self):
        initial_dict = {'test': 'это юникод'}
        base64str = dict_to_base64(initial_dict)
        self.check_base64_dict(base64str, initial_dict)

    def test__base64_description_for_non_json_convertabe__is_valid(self):
        initial_dict = {'test': decimal.Decimal('10.0')}
        base64str = dict_to_base64(initial_dict)
        self.check_base64_dict(base64str, {'test': '10.0'})


