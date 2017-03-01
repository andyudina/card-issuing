'''This is the mock module for schema API wrapper'''

class SchemaAPI:

    '''
    Mock for API with schema communication
    '''
    
    def transfer_debts_to_schema(self, *args, **kwargs):
        '''
        Mock method for transfering money at the settlement 
        '''
        pass

    class SchemaError(ValueError):

        '''
        Custom Error class. 
        Represents errors with schema communications
        '''
        
        @property
        def info(self):
            '''
            Shortcut for error info
            '''
            return self.args[0]        
        

