## Realization details

- **Directories structure**:

card_issuing_excercise/  
--apps/    
------apis/                *wrappers for external APIs*   
------currency_converter/  *incapsulates currency convertations business logic*  
------processing/          *transactions processing core*      
------unique_id_generator/ *external server for unique robust ids generation*  
------utils/               *misc utils*  
------users/               *supports users API*   
--settings/                *Django/security/issuer-specific settings*  
docs/  
manage.py
  
- **Core business logic is stored in two web apps**: one for communication with Schema, another for interactions with user. 
  That can be a bit redundant for current purposes, but supports further growth. 
  The main idea: user iteraction and real money processing should be done by different components.
  All account realted tables are stored in processing app as they are more about transactions than user properties.
  
  
- **All actions are stored as transfers**. So all agents, who acept or transfer money should be represented with distinct accounts.
  Every user has two accounts: real one and one "fake", used for reserving money after authorization request. 
  So authorization request is designed as a trasfer btw this two accounts.
  Presentment request fistly rollback authorization request, transfering money for reserving account to basic,
  and then transfers money from basic account to Issuer settlement account.
  Settlement is logged as transfering money from settlement account to some abstract "external schema account".
  Loading money is logged as trasfering money from some "external user loading account" to base user account.
  Latest two accounts are "external" to our system, so we don't manage their amounts.
  
  
- **Currency changes are mitigated by authorizing a little bigger sum of money than requested**. 
  Overhead is defined in settings for simplicity.
  
  
- **The period of reserving sums is also defined in settings.** 
  When it ends, money are transformed from reservation account to basic one.
