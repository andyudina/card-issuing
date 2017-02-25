GOAL: JSON back-end for a fintech company actinga as an Issuer

USER STORIES:
- Schema sends authorizing request on user payment and gets 200 OK if user have enough money or 403 otherwise.
  If user has wnough money, we reserve sum on his account. 
- Schema sends presentment request and gets 200 OK on valid request or 403 otherwise.
  We deduct funds from cardholder account. Now we have a debt to the Scheme. Money moves from user account to our settlement account.
- Every day money is send to the Scheme. We reduce debt to the schema and deduct money from our settlemet account. 
  We save difference btw settlement_amount and billable_amount as our revenue.
- User can query all presented transactions in specific time range.
- User can query his balance at specific point at time.
- We can load user money by management command.

API SCHEMA:
BASE_URL: /api/v1/
SCHEMA: https
URLS:
  1. The Schema webhook
    URI:    /requests/
    METHOD: POST
    PARAMS:
       - type: string
       - card_id: string
       - transaction_id: string
       - merchant_name: string
       - merchant_country: string
       - merchant_mcc: string
       - billing_amount: string
       - billing_currency: string
       - transaction_amount: string
       - transaction_curreny: string
       - settlement_amount: string (can be null)
       - settlement_amount: string (can be null)

  2. Trasactions for user
    URI:    /user/(?P<user_id>\d+)/transactions/
    METHOD: GET
    PARAMS:
      - begin_ts: int (can be null)
      - end_ts: int (cab be null)

  3. Balance for user
    URI:    /user/(?P<user_id>\d+)/balance/
    METHOD: GET
    PARAMS: 
      - datetime_ts: int (can be null)

WHAT WENT OUT OF SCOPE:
- Security checks are not implemented nor for user nor for Schema webhook.
  What MUST be done:
  - Check user authorisation and permissions on every request
  - Authenticate JSON webhook for Schema and close its location by API on front-end web server
  - Tune base django security settings: DEBUG, ALLOWED_HOSTS etc.
- Communications with the Schema during the settlement process is also not implemented and mocked.
- Time zones management. We work in GMT and don't do any assumptions about users' time zone.

REALISATION DETAILS:
- I've split whole project into two web-apps: one for communication with Schema, another for interactions with user. 
  That can be a bit redundant for current purposes, but supports further growth. 
  The main idea: user iteraction and real money processing should be done by different components.
  All account realted tables are stored in processing app as they more about transactions than user properties.
