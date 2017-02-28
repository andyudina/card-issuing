from django.conf.urls import url

from users.views import TransactionsView, BalanceView 

urlpatterns = [
    url(r'^(?P<id>\d+)/transactions/$', TransactionsView.as_view()),
    url(r'^(?P<id>\d+)/balance/$', BalanceView.as_view()),
]

