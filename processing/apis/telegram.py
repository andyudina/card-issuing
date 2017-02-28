'''This is the mock wrapper around Telegram webhooks'''

class TelegramAPI:

    '''
    Mocks alarming to Telegram channels.
    '''

    def alarm_schema_err(self, *args, **kwargs):
        '''
        Sends telegram messages to all stakeholders when Schema communications fail.
        Should be top priority alarms.
        '''
        pass
  
 
