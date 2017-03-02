''' 
Stub module for converting currencies.
Uses extrnal api to determine exchange rates
'''

from card_issuing_excercise.apps.apis import CurrencyAPI
from card_issuing_excercise.settings import DEFAULT_CURRENCY


class Converter:

    '''
    Stub class for currency convertation.
    Also handles currency API monitoring and errors alarming.
    Throws errors if API can't be reached.
    Transactions are supposed to fail then
    '''

    def get_amount_for_save(self, amount, source_currency):
        '''
        Converts amount into Issuer currecny
        '''
        if source_currency == DEFAULT_CURRENCY:
            return amount
        return amount * \
            self.get_exhange_rate(DEFAULT_CURRENCY, source_currency)

    def get_exhange_rate(self, to_currency, from_currency):
        '''
        Get currencies exchange rate by CurrencyAPI.
        Incapsulates response cache mechanism and deals with API errors
        '''
        rate = self._get_rate_from_cache(to_currency, from_currency)
        if rate:
            return rate
        return self._get_rate_from_api(to_currency, from_currency)

    def _get_rate_from_cache(self, to_currency, from_currency):
        '''
        Get rates from cache.
        Cache TTL is managed by cache server.
        Returns None for empty cache
        '''
        return None

    def _get_rate_from_api(self, to_currency, from_currency):
        '''
        Get currencies exchange rate by CurrencyAPI.
        Deals with API Errors
        '''
        try:
            rate = CurrencyAPI().get_exchange_rate(to_currency, from_currency)
            self._update_in_cache(rate, to_currency, from_currency)
            return rate
        except CurrencyAPI.CurrencyAPIError as error:
            self._alarm_api_error(error.info)
            raise Converter.ConverterError('api_error')

    def _update_in_cache(self, rate,
                         to_currency, from_currency):
        '''
        Updates currency rate in cache
        '''
        pass

    def _alarm_api_error(self, info):
        '''
        Alarm all stakeholders by sms, telegram, etc
        '''
        pass

    class ConverterError(ValueError):

        '''
        Error class for convertation API
        '''

        @property
        def info(self):
            return self.args[0]
