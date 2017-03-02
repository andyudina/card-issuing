from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from card_issuing_excercise.apps.processing.views import SchemaWebHook

urlpatterns = [
    url(r'^$', csrf_exempt(SchemaWebHook.as_view())),
]
