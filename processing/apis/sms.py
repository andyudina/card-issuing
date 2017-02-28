'''This is the mock wrapper around SMS Gateway API'''

class SmsAPI:

    '''
    Mocks alarming by sms.
    Gateway should be covered by monitoring.
    '''

    def alarm_schema_err(self, *args, **kwargs):
        '''
        Sends sms to all stakeholders when Schema communications fail.
        Should be top priority alarms.
        '''
        pass
  
 
