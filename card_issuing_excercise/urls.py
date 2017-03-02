'''card_issuing_excercise URL Configuration'''

from django.conf.urls import url, include

api_urlpatterns = [
    url(r'^request/', include('apps.processing.urls')),
    url(r'^user/', include('apps.users.urls')),
]

urlpatterns = [
    url(r'^api/v1/', include(api_urlpatterns)),
]
