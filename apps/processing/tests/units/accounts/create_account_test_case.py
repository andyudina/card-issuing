import datetime

from django.test import TestCase

from apps.processing.models.accounts import UserAccountsUnion, \
                                            BASIC_ACCOUNT_TYPE, \
                                            REVENUE_ACCOUNT_ROLE
from card_issuing_excercise.settings import ROOT_USERNAME
from utils.tests import CreateAccountMixin



class CreateNewAccount(CreateAccountMixin, 
                       TestCase):

    '''
    Test account creation logic
    '''

    def setUp(self):
        self.user = self.create_user()

    ##
    # Helpers
    ##

    def create_basic_account(self, **kwargs):
        '''
        Helper for creating basic account with both links
        '''
        return UserAccountsUnion.objects.create(user=self.user, 
                                                card_id=kwargs.get('card_id', 'TESTID'))

    def create_revenue_account(self, **kwargs):
        return UserAccountsUnion.objects.\
                                 create_special_account(REVENUE_ACCOUNT_ROLE)

    def create_account_with_one_link(self, **kwargs):
        return UserAccountsUnion.objects.create(user=self.user, 
                                                card_id=kwargs.get('card_id', 'TESTID2'),
                                                linked_account_types=[BASIC_ACCOUNT_TYPE,])

    def check_account_has_link(self, user_account, link_type):
        '''
        Check that specific account link exists
        '''
        self.assertTrue(user_account.accounts.\
                                     filter(account_type=link_type).exists())

    def check_account_has_proper_links_number(self, 
                                              user_account, links_number):
        '''
        Check account links number
        '''
        self.assertEqual(
             user_account.accounts.count(), links_number)

    ##
    # Testers
    ##

    def test__create_new_user_basic_account__has_basic_link(self):
        account = self.create_basic_account()
        self.check_account_has_link(account, BASIC_ACCOUNT_TYPE)

    def test__create_new_user_basic_account__has_revenue_link(self):
        account = self.create_basic_account()
        self.check_account_has_link(account, REVENUE_ACCOUNT_ROLE)

    def test__create_new_user_basic_account__links_number(self):
        account = self.create_basic_account()
        self.check_account_has_proper_links_number(account, 2)

    def test__create_special_account__success(self):
        account = self.create_revenue_account()
        self.assertEqual(account.role, REVENUE_ACCOUNT_ROLE)

    def test__create_special_account__owned_by_superuser(self):
        account = self.create_revenue_account()
        self.assertEqual(account.user.username, ROOT_USERNAME)

    def test__create_duplicate_special_account__new_not_created(self):
        for try_number in range(2):
            self.create_revenue_account()    
        self.assertEqual(
            UserAccountsUnion.objects.filter(role=REVENUE_ACCOUNT_ROLE).count(), 1)


    def test__create_new_user_account_with_specified_type__link_created(self):
        account = self.create_account_with_one_link()
        self.check_account_has_link(account, BASIC_ACCOUNT_TYPE)

    def test__create_new_user_account_with_specified_type__has_only_one_link(self):
        account = self.create_account_with_one_link()
        self.check_account_has_proper_links_number(account, 1)


