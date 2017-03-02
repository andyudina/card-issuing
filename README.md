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
    URI:    /user/(?P\<user_id\>\d+)/transaction/
    METHOD: GET
    PARAMS:
      - begin_ts: int (can be null)
      - end_ts: int (cab be null)

  3. Balance for user
    URI:    /user/(?P\<user_id\>\d+)/balance/
    METHOD: GET
    PARAMS: 
      - datetime_ts: int (can be null)

REALISATION DETAILS:
- Directories structire:
  /
  - apis/ wrappers for external apis
  - apps/ directory with django apps
     - processing/ transactions processing core
     - users/      supports users interface
  - card_issuing_excercise/ settings|urls|wsgi entry point
  - currency_converter/
  - utils/ misc utils
  - unique_id_generator/ external server for unique robust ids generation
 
- I've split whole project into two web-apps: one for communication with Schema, another for interactions with user. 
  That can be a bit redundant for current purposes, but supports further growth. 
  The main idea: user iteraction and real money processing should be done by different components.
  All account realted tables are stored in processing app as they are more about transactions than user properties.
- All actions are stored as transfers. So all agents, who acept or transfer money should be represented with distinct accounts.
  Every user has two accounts: real one and one "fake", used for reserving money after authorization request. 
  So authorization request is designed as a trasfer btw this two accounts.
  Presentment request fistly rollback authorization request, transfering money for reserving account to basic,
  and then transfers money from basic account to Issuer settlement account.
  Settlement is logged as transfering money from settlement account to some abstract "external schema account".
  Loading money is logged as trasfering money from some "external user loading account" to base user account.
  Latest two accounts are "external" to our system, so we don't manage their amounts.
- Currency changes are mitigated by authorizing a little bigger sum of money than requested. Overhead is defined in settings for simplicity.
- The period of reserving sums is also defined in settings. When it ends, money are transformed from reservation account to basic one.

WHAT WENT OUT OF SCOPE:
- Security checks are not implemented nor for user nor for Schema webhook.
  What MUST be done:
  - Check user authorisation and permissions on every request
  - Authenticate JSON webhook for Schema and close its location by API on front-end web server
  - Tune base django security settings: DEBUG, ALLOWED_HOSTS etc.
- Communications with the Schema during the settlement process is also not implemented and mocked.
- Time zones management. We work in GMT and don't do any assumptions about users' time zone.
- Consistency checking on errors. There are a few points in application, 
  where we can asssume that smth could have broken our consistency.
  For example, what if presentment transaction was created, but reserved funds were not released.
  We should carry out integrity checks for such broken transactions periodicly and on specific event (like IntegrityError from database)
  The checks should be done in background by celery etc.
- Perfomance optionizations were completely skipped, but marked in TODOs
- Only public methods of all classes were covered tests.
- Monitorings: all 500 err, APIS, transactions quantity should be monitored
- There is no support for transfering btw users accounts - only through schema. 
  Though core supports this, API is not implemented.

ROADMAP:
28.02:
- views + management commands + tests
01.03:
- currency subsystem mock + tests + descriptions to transactions + tests refactoring
02.03
- core models refactoring + lint + grammar checks
