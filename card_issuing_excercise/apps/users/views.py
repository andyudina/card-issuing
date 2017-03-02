'''Views for public user API (transactions and balance)'''

from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView, \
    ListAPIView, get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from card_issuing_excercise.apps.processing.models import UserAccountsUnion
from card_issuing_excercise.apps.users.serializers import BalanceRequestSerializer, \
    TransactionRequestSerializer, \
    TransactionSerializer
from card_issuing_excercise.apps.users.permissions import IsAccountOwner


TRANSACTIONS_PER_PAGE = 20


class GetUserAccountMixin:

    '''
    Incapsulates common functionality for user accounts management:
    - account selection
    - managing permissions
    '''

    # TODO: force permissions checks before get_or_404
    # attacker can get our accout_ids by brute force

    lookup_field = 'id'
    queryset = UserAccountsUnion.objects.all()
    permission_classes = (IsAuthenticated, IsAccountOwner, )


class TransactionsPaginator(PageNumberPagination):

    '''Provides pagination settings'''

    page_size = TRANSACTIONS_PER_PAGE


class TransactionsView(GetUserAccountMixin,
                       ListAPIView):

    '''
    Repsresents all presentment transactions for particular user in  a given time range.
    Accepts nill values for time range. 
    In this case it doesn't limit transactions in time frame.
    '''

    pagination_class = TransactionsPaginator
    serializer_class = TransactionSerializer

    def get_object(self, *args, **kwargs):
        # rewrite get_object to avoid recursion
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = get_object_or_404(self.queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def filter_queryset(self, *args, **kwargs):
        user_account = self.get_object()
        request_serializer = TransactionRequestSerializer(
            data=self.request.query_params)
        if request_serializer.is_valid():
            return user_account.get_transactions(**request_serializer.data)
        raise ValidationError()


class BalanceView(GetUserAccountMixin,
                  GenericAPIView):

    '''
    Show user's balance for a particular date and time. 
    Accepts nill value for timestamp and returns current balance.
    '''

    def get(self, request, *args, **kwargs):
        user_account = self.get_object()
        request_serializer = BalanceRequestSerializer(
            data=request.query_params)
        if request_serializer.is_valid():
            amounts_tuple = user_account.get_amounts_for_ts(
                request_serializer.data.get('ts'))
            return Response({
                'available_amount': amounts_tuple[0],
                'total_amount': amounts_tuple[1]})
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)
