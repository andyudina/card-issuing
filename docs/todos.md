## TODOs

- Security checks are not implemented nor for user, nor for Schema webhook.
  What MUST be done:
  - Check user authorisation and permissions on every request. 
  - Authenticate JSON webhook for Schema and close its location by API on front-end web server
  - Tune base django security settings: DEBUG, ALLOWED_HOSTS etc.
  
- Communications with the Schema during the settlement process is also not implemented and replaced with stub...
- ...along with other external apis: sms/email/telegram etc API wrappers are not implemented

- Currency converter subsystem is replaced with stub.

- Unique ID generator for transactions is also to be done.

- Time zones management. We work in GMT and don't make any assumptions about users' time zone.

- Extra transaction validations for fraud detection. Like different merchants for authorization and presentment transaction.

- Consistency checking for errors. There are a few points in the application, where we can assume that something could have broken our consistency. For example, what if presentment transaction was created, but reserved funds were not released.
We should carry out integrity checks for such broken transactions periodically and on specific event (like IntegrityError from database) The checks should be done in the background by celery etc.

- Performance optimizations were completely skipped.

- Monitorings: all 500 errors, our and external API accessibility, transactions quantity should be monitored.

- There is no API for transferring between our users' accounts - all transactions should go through Schema.
Though core supports this, the API is not implemented.

- Test coverage is insufficient even for most detailed modules. Should be covered with tests:
  - Requesting API methods with invalid parameters.
  - Transactions pagination, sorting, etc in user public API.
  - Utils

- Load tests and race conditions, tests should be done. Race conditions, tests can be done by accessing the database in different threads simultaneously. For load tests we can use hit based systems, I personally prefer Yandex tank.

- Further refactoring and improvements:
  - more verbose custom errors in test helpers
  - checking encodings on transaction request (mb non utf-8)
  - generation of human readable description
  - more verbose amounts managements in tests
  ...

