''' 
Stub module for detecting frauds
'''


class FraudDetector:

    '''
    Stub class for fraud detection.
    Can use mix of empirical rules, statistic probability calculations and ML.
    Stores passed and failed transactions info somewhere in NoSQL.
    Also should alarm about suspicious operations to analytics team
    '''

    def check_is_fraud(self, **transaction_info):
        '''
        Check if transaction is fraud and alarm to stakeholders.
        Returns "is_fraud" flag
        '''
        fraud_probability, detected_fraud_method = \
            self._get_highest_fraud_probability(transaction_info)
        if self._is_sure_fraud(fraud_probability):
            self._alarm_fraud(
                transaction_info=transaction_info,
                fraud_probability=fraud_probability,
                detected_fraud_method=detected_fraud_method)
            return True
        elif self._is_rather_suspicious(fraud_probability):
            self._alarm_suspicious(
                transaction_info=transaction_info,
                fraud_probability=fraud_probability,
                detected_fraud_method=detected_fraud_method)
        return False

    def _get_highest_fraud_probability(self, transaction_info):
        '''Iterates over all available method and returns highest probability'''
        highest_fraud_probability = 0
        detected_fraud_method = None
        for method in self._get_fraud_detection_methods():
            fraud_probability = method.get_fraud_probability(transaction_info)
            # if detected fraud - return immediately
            if fraud_probability >= SURE_FRAUD_TRESHOLD:
                return (fraud_probability, method)
            if fraud_probability > highest_fraud_probability:
                highest_fraud_probability = fraud_probability
                detected_fraud_method = method
        return (highest_fraud_probability, detected_fraud_method)

    def _is_sure_fraud(self, probability):
        '''
        Incapsulates fraud detection logic.
        By comparing probability with treshold for example
        '''
        pass

    def _is_rather_suspicious(self, probability):
        '''
        Detects suspicious transaction which needs further checks.
        Can also be done by comparing with treshold
        '''
        pass

    def _alarm_fraud(self, **kwargs):
        '''Alarm to analytics team about fraud'''
        pass

    def _alarm_suspicious(self, **kwargs):
        '''Alarm to analytics team about suspicious operation'''
        pass

    def _get_fraud_detection_methods(self):
        '''
        Returns list of fraud detector methods
        '''
        return []
