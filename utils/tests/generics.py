'''Generic TestCases'''

from django.test import TestCase

from .mixins import CreateAccountMixin, \
    CreateTransactionMixin, \
    TestTransactionMixin, \
    TestTransactionAPIMixin, \
    TestUsersAPIMixin

# Base classes for test cases


class TransactionBaseTestCase(CreateAccountMixin, CreateTransactionMixin,
                              TestTransactionMixin, TestCase):

    '''
    Base class for testing transactions logic
    '''
    pass


class ShemaWebHookBaseTestCase(CreateAccountMixin, CreateTransactionMixin,
                               TestTransactionAPIMixin, TestCase):

    '''
    Base class for testing schema web hook
    '''
    pass


class UserAPITestCase(CreateAccountMixin,
                      TestUsersAPIMixin, TestCase):

    '''
    Base class for testing user api views
    '''
    pass
