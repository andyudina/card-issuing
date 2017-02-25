from django.conf.urls import url

from processing.views import SchemaWebHook

urlpatterns = [
    url(r'^$', SchemaWebHook.as_view()),
]
