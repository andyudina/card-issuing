## API description

**Base Url:** /api/v1/

**Schema:** https

**Urls:** 
  1. The Schema webhook
    - Uri:    /requests/
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

  2. Trasactions for user
    - Uri:    /user/(?P\<user_id\>\d+)/transaction/
    - Method: GET
    - Params:
      - begin_ts: int (can be null)
      - end_ts: int (cab be null)

  3. Balance for user
    - Uri:    /user/(?P\<user_id\>\d+)/balance/
    - Method: GET
    - Params: 
      - ts: int (can be null)
