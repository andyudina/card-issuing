'''This is the stub module for currecny API wrapper'''

class CurrencyAPI:

    '''
    Stub for API with schema communication
    '''

    def get_exchange_rate(self, *args, **kwargs):
        '''Stub method for looking up currencies'''
        return 1

    class CurrencyAPIError(ValueError):

        '''
        Custom Error class. 
        Represents errors with schema communications
        '''
        
        @property
        def info(self):
            '''Shortcut for error info'''
            return self.args[0]        
        
