'''card_issuing_excercise URL Configuration'''

from django.conf.urls import url, include

api_urlpatterns = [
    url(r'^request/', include('card_issuing_excercise.apps.processing.urls')),
    url(r'^user/', include('card_issuing_excercise.apps.users.urls')),
]

urlpatterns = [
    url(r'^api/v1/', include(api_urlpatterns)),
]
