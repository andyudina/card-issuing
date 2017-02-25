from django.conf.urls import url

from users.views import TransactionsView, BalanceView 

urlpatterns = [
    url(r'^(?P<user_id>\d+)/transactions/$', TransactionsView.as_view()),
    url(r'^(?P<user_id>\d+)/balance/$', BalanceView.as_view()),
]
