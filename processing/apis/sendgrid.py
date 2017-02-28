'''This is the mock wrapper around Sendgrid emails API'''

class SendgridAPI:

    '''
    Mocks alarming by emails.
    '''

    def alarm_schema_err(self, *args, **kwargs):
        '''
        Sends emails to all stakeholders when Schema communications fail.
        Should be top priority alarms.
        '''
        pass
  
 
