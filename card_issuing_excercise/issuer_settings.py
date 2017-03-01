'''
Issuer specific settings: 
- overhead on authorisation transaction in percents
- TTL for authorisation transaction without presentment in days
'''

AUTHORISATION_OVERHEAD = 20
AUTHORISATION_TRANSACTION_TTL = 5
#TODO: what are real precision requirements??
AMOUNT_PRECISION_SETTINGS = {
    'max_digits': 19,
    'decimal_places': 4
}

DEFAULT_CURRENCY = 'EUR'

ROOT_USERNAME = 'root'