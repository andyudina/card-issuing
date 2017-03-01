from rest_framework import serializers

from apps.processing.models import Transaction, \
                              Transfer
from utils import datetime_to_timestamp


class TimestampField(serializers.ReadOnlyField):

    '''
    Custom serializer to represent datetime as timestamp
    '''

    def to_representation(self, value):
        return datetime_to_timestamp(value)


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        exclude = ('account', 'transaction')


class TransactionSerializer(serializers.ModelSerializer):
    created_at = TimestampField()
    transfers = TransferSerializer(many=True)

    class Meta:
        model = Transaction
        exclude = ('code', ) #Don't expose transaction ids