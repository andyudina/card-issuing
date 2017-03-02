'''Serialize and validate schema request'''

from rest_framework import serializers

from apps.processing.models.accounts import CARD_ID_LENGTH
from apps.processing.models.transactions import TRANSACTION_ID_LENGTH
from card_issuing_excercise.settings import AMOUNT_PRECISION_SETTINGS


class SchemaRequestSerializer(serializers.Serializer):

    '''
    Serializer for schema request.
    Just does JSON parsing.
    Not necessary fields are ommited
    '''

    type = serializers.CharField(max_length=255)
    card_id = serializers.CharField(max_length=CARD_ID_LENGTH)
    transaction_id = serializers.CharField(max_length=TRANSACTION_ID_LENGTH)
    billing_amount = serializers.DecimalField(**AMOUNT_PRECISION_SETTINGS)
    billing_currency = serializers.CharField(max_length=255)
    settlement_amount = serializers.DecimalField(
        required=False, **AMOUNT_PRECISION_SETTINGS)
    settlement_currency = serializers.CharField(required=False, max_length=255)
