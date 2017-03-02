## User stories

### Ths Schema
- Schema sends authorizing a request on user payment and gets 200 OK if the user has enough money or 403 otherwise.
  If the user has enough money, we reserve sum on his account.
  User can request transaction in arbitrary currency. 
- Schema sends presentment request and gets 200 OK on valid request or 403 otherwise.
  We deduct funds from cardholder account. Now we have a debt to the Scheme. Money moves from user account to our settlement account.
- Every day money is sent to the Scheme. We reduce the debt to the schema and deduct money from our settlement account.
  We save difference btw settlement_amount and billable_amount as our revenue.
  
### User API
- User can query all presented transactions in specific time range.
- User can query his balance at specific points in time.
- We can load user money by a management command in arbitrary currency.