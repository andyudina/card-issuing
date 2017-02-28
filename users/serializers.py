from rest_framework import serializers


class BalanceRequestSerializer(serializers.Serializer):

    '''
    Serializer for balance request.
    Just does JSON parsing.
    '''

    ts = serializers.IntegerField(required=False) # timestamp

