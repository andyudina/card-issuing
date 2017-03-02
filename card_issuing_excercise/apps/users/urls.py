from django.conf.urls import url

from card_issuing_excercise.apps.users.views import TransactionsView, BalanceView 

urlpatterns = [
    url(r'^(?P<id>\d+)/transaction/$', TransactionsView.as_view()),
    url(r'^(?P<id>\d+)/balance/$', BalanceView.as_view()),
]

