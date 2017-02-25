from django.views.generic.base import View

class TransactionsView(View):
    '''
        Repsresents all presentment transactions for particular user in  a given time range.
        Accepts nill values. In this case it doesn't limit transactions in time frame.
    '''
    pass


class BalanceView(View):
    '''
        Show user's balance for a particular date and time. Accepts nill value for timestamp. 
        Returns current balance for this.
    '''
