## API description

**Base Url:** /api/v1/

**Schema:** https

**Urls:** 
  1. The Schema webhook
    - Uri:    /request/
    - Method: POST
    - Params:
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
    - Responses:  
      *returns empty response. success/error is determined by error code*
      - Success:
        - 200 OK
      - Errors:
        - 400 BAD REQUEST: Invalid request format. Required fields are missing or invalid fields format.
        - 403 FORBIDDEN: Card with specified id does not have enough money for the transaction
        - 404 NOT FOUND: Authorization transaction with specified id does not exist
        - 406 NOT ACCEPTABLE: Card id owner does not exist
        - 409 CONFLICT: Duplicate transaction
        - 500 SERVER ERROR: We encountered an internal error during request processing and temporary anavailable. 
        (For example currency converter is down and we can't be sure that the transaction will be saved correctly)

  2. Trasactions for user  
    *Returns paginated user transactions. Returns money loads and presentment transactions only*  
    *Transactions are ordered by creation date in descending order*
    - Uri:    /user/(?P\<account_id\>\d+)/transaction/
    - Method: GET
    - Params:
      - begin_ts: int (can be null)
      - end_ts: int (can be null)
      - page: int (can be null - then return first page)

**Response**
*Returns 200 OK and JSON for success, empty response with error code for error*
- Success:
  - Code: 200 OK
  - Response stucture:
  - *Example:*
 ```json
    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
                {
                    "created_at": 1488473323,
                    "id": 1,
                    "status": 'p',
                    "human_readable_description": "Awesome Air Jordan sneakers.",
                    "transfers": [
                        {
                            "amount": "91.00"
                            "id": 1
                        }
                    ]
                }
            ],
    }
```
  - *Description:*
      - count: number of transactions in specified time range (int)
      - next: next page if exists (str or null)
      - previous: previous page url if exists (str or null)
      - results: array of transactions, sorted by creation time in descending order  
        transaction consists of this fields:
          - id (int)
          - status: specifies whether it was presentment transaction, or money loading (str)
          - human_readable_description: transaction description. Is formed on transaction creation and stored in db. (string or null)
          - transfers: Array of user transfers
            - amount: transfer amount. can be negative (string)
            - id (int)

- Errors:
  - 400 BAD REQUEST: Invalid request format
  - 403 FORBIDDEN: Non authorized or non authenticated user
  - 404 NOT FOUND: Account with such id does not exist  

  3. Balance for user
    - Uri:    /user/(?P\<account_id\>\d+)/balance/
    - Method: GET
    - Params: 
      - ts: int (can be null - return current balance then)

**Response**
*Returns 200 OK and JSON for success, empty response with error code for error*
- Success:
  - Code: 200 OK
  - Response structure
  - *Example*
```json
{
  "available_amount": "91.01",
  "total_amount": "10.21"
}
```
  - *Description:*
      - available_amount: (string)
      - total_amount: available_amount + reserved_amount (string)
- Errors:
  - 400 BAD REQUEST: Invalid request format
  - 403 FORBIDDEN: Non authorzed or non authenticated user
  - 404 NOT FOUND: Account with such id does not exist
