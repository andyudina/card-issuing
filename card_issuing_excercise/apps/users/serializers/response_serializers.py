'''Serializes public user API responses'''

from rest_framework import serializers

from card_issuing_excercise.apps.processing.models import \
    Transaction, \
    Transfer
from card_issuing_excercise.apps.utils import datetime_to_timestamp


class TimestampField(serializers.ReadOnlyField):

    '''Represents datetime as timestamp'''

    def to_representation(self, value):
        return datetime_to_timestamp(value)


class TransferSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transfer
        exclude = ('account', 'transaction')


class TransactionSerializer(serializers.ModelSerializer):

    '''Transaction model serializer'''

    created_at = TimestampField()
    transfers = TransferSerializer(many=True)

    class Meta:
        model = Transaction
        # Don't expose transaction ids
        exclude = ('code', 'base64_description')
