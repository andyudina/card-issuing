## Realization details

- **Directories structure**:  
card_issuing_excercise/   
&nbsp;&nbsp;&nbsp;&nbsp;apps/   
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;apis/                 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;currency_converter/    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;fraud_detector/ 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;processing/   
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;unique_id_generator/   
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;users/    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;utils/ 
&nbsp;&nbsp;&nbsp;&nbsp;settings/ 
docs/  
manage.py  

- **Apps short description**
  - *apis*: wrappers for external APIs (currecny conerter api, sms gateway, email services etc.)
  - *currency_converter*: module for on-the-fly currency convertion
  - *fraud_detector*: on-the-fly fraud detection
  - *processing*: core module for transactions processing. Also provides web hook for the Schema and misc management commands (settlement, load money etc..)
  - *unique_id_generator*: robust unique sequence generator. Used for getting unique transaction IDs on money loading.
  - *users*: provides user public API. (balances/transactions history)
  - *utils*: misc utility functions
  
- **Core business logic is stored in two django apps**: one for communication with Schema, another for interactions with user. 
*Processing* module encapsulates transaction/transfers/account management, business logic and provides Webhook for the Schema. 
*User* module provides a public API with user info. 
Separating logic in two apps can be a bit redundant for current purposes, but supports further growth. 
The main idea: user interaction and real money processing should be done by different components.
All accounts related tables are stored in processing app as they are more about transactions than user properties.
  
  
- **All actions are stored as transfers**. The transfer is a base entity that stores money movements between accounts during all types of transactions. Transfers are related to transaction and balanced (sum of all transfer amounts of one transaction is zero). All agents, who accept or transfer money should be represented by distinct accounts.
  - *Authorization transaction*. Every user has two accounts: real one and one "reserved", used for reserving money after authorization request. So authorization request is designed as a transfer between these two accounts related to one user.
  - *Presentment request* is a transferring between user account and "inner settlement account". Inner settlement account holds our debts to the Schema and accumulates amounts that would be transferred to the Schema during everyday settlement. While handling presentment request, we firstly rollback authorization request by transferring money for reserving account to base one, and then transfer money from basic account to "inner settlement account".
  - *Settlement* is processed as transferring money from the "inner settlement account" to some abstract "external schema account". Real transfering and communcating with the Schema API during settlement went out of scope.
  - *Loading money* is processed as transferring money from some "external user loading account" to base user account.
Latest two accounts are "external" to our system, so we don't manage their amounts.
  
- **There are two types of accounts in the system**. There is so-called "union account" which related to a particular user. This account can be either basic (real user) or one of special system types which is used for handling settlements, loading money, etc. Each basic "union account" has two related "real accounts", which take part in transforming: real account, holding available amount, and reserved one, holding reserved by authorization transaction amounts.

- **All transactions are stored as equal entities** with different statuses. Statuses are:
  - Authorization
  - Presentment
  - Settlement
  - Rollback of authorization transaction during presentment
  - Fail on money shortage (this type don't have any transfering)
  - Rollback of outdated authorization transaction
  
- **Transaction rollback creates new transferings**. Amounts are opposite to initial ones.

- **Pair "transaction id" + "transaction status" is unique** to prevent duplication.

- **Currency changes are mitigated by authorizing a little bigger sum of money than requested**. 
  Overhead is defined in settings for simplicity.  
  
- **The period of reserving sums is also defined in settings.** 
  When it ends, money are transformed from reservation account to basic one and outdated transaction is rollbacked.
