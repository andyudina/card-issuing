from rest_framework import serializers


class BalanceRequestSerializer(serializers.Serializer):

    '''
    Serializer for balance request.
    Just does JSON parsing.
    '''

    ts = serializers.IntegerField(required=False) # timestamp


class TransactionRequestSerializer(serializers.Serializer):

    '''
    Serializer for transaction request.
    Just does JSON parsing.
    '''

    begin_ts = serializers.IntegerField(required=False) # timestamp
    end_ts = serializers.IntegerField(required=False) # timestamp