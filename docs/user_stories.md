## User stories

### Ths Schema
- Schema sends authorizing request on user payment and gets 200 OK if user have enough money or 403 otherwise.
  If user has wnough money, we reserve sum on his account. 
- Schema sends presentment request and gets 200 OK on valid request or 403 otherwise.
  We deduct funds from cardholder account. Now we have a debt to the Scheme. Money moves from user account to our settlement account.
- Every day money is send to the Scheme. We reduce debt to the schema and deduct money from our settlemet account. 
  We save difference btw settlement_amount and billable_amount as our revenue.

### User API
- User can query all presented transactions in specific time range.
- User can query his balance at specific point at time.
- We can load user money by management command.
