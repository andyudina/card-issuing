## TODOs

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
  
- Perfomance optionizations were completely skipped, but marked in TODOs.

- Only public methods of all classes were covered tests.

- Monitorings: all 500 err, APIS, transactions quantity should be monitored.

- There is no support for transfering btw users accounts - only through schema.
  Though core supports this, API is not implemented.
