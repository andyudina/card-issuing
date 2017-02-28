from django.contrib.auth.models import User
from django.http import HttpRequest
from rest_framework import status
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from processing.models import UserAccountsUnion
from users.serializers import BalanceRequestSerializer
from users.permissions import IsAccountOwner


TRANSACTIONS_PER_PAGE = 20

class TransactionsView(GenericAPIView):
    '''
        Repsresents all presentment transactions for particular user in  a given time range.
        Accepts nill values. In this case it doesn't limit transactions in time frame.
    '''
    pass


class BalanceView(GenericAPIView):
    '''
        Show user's balance for a particular date and time. Accepts nill value for timestamp. 
        Returns current balance for this.
    '''
    
    permission_classes = (IsAuthenticated, IsAccountOwner, )
    serializer_class = BalanceRequestSerializer
    queryset = UserAccountsUnion.objects.all()
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        # TODO: force permissions checks before get_or_404
        # attacker can get our accout_ids by brute force
        user_account = self.get_object()
        balance_serializer = BalanceRequestSerializer(data=request.query_params)
        if balance_serializer.is_valid():
            amounts_tuple = user_account.get_amounts_for_ts(
                                         balance_serializer.data.get('ts'))
            return Response({                 
                'available_amount': amounts_tuple[0],
                'total_amount': amounts_tuple[1]})
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)


