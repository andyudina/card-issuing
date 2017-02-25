from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.parsers import JSONParser


class SchemaWebHook(APIView):
    '''
        Handels paiment requests from the Schema.
        For both authorisation and presentment requests.
    '''
    
    #TODO: should custom quotes be supported?
    parser_classes = (JSONParser,)

    def post(self, request, format=None):
        return HttpResponse
