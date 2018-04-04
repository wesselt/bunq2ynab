# bunq2ynab

A python script to upload BUNQ transactions to YNAB

## Installation

1. Install [Python 3](https://www.python.org/) and [pyOpenSSL](https://pyopenssl.org/en/stable/install.html).  (This worked for me on Debian: `sudo pip3 install pyopenssl`.)
2. Create a BUNQ "API key" in the BUNQ mobile app.  Click your picture, then Security, API keys, then
add a key using the plus on the top right.  Choose to "Reveal" the API key and share it.  Store the API key 
in "api_token.txt".
3. Verify that the link with BUNQ works by requesting the list of users and accounts:
```
    python3 list_user.py
```
4. Create a YNAB "Personal Access Token" in the YNAB website https://app.youneedabudget.com/settings/developer.
Store the token in "personal_access_token.txt".
5. Verify that the link with YNAB works by requesting the list of budgets:
```
    python3 list_budget.py
```
6. You're all set to upload transactions!  Pick a BUNQ userid and accountid from `list_user.py`, and a 
YNAB budgetid and accountid from `list_budget.py`, and run:
```
    python3 bunq2ynab.py <bunq userid> <bunq accountid> <ynab budgetid> <ynab accountid>
```

## What bunq2ynab does to read transactions from BUNQ

1. Generate a public/private keypair
2. Register the keypair with BUNQ through the "installation" endpoint.  Store the returned installation token 
and the server's public key
3. Register your IP with BUNQ through the "device-server" endpoint
4. Get a session token through the "session-server" endpoint.  Store the returned  session token
5. Prepare a CSV export using the "user/xxx/monetary-account/xxx/customer-statement" endpoint
6. Retrieve the CSV using the "user/xxx/monetary-account/xxx/customer-statement/content" endpoint
7. Delete the CSV using the "user/xxx/monetary-account/xxx/customer-statement" endpoint

## What bunq2ynab does to upload transactions to YNAB

1. Post the transactions to the "v1/budgets/xxx/transactions/bulk" endpoint

## Links

- BUNQ API documentation: https://doc.bunq.com/
- YNAB API documentation: https://api.youneedabudget.com/
- YNAB API endpoints: https://api.youneedabudget.com/v1
- Request YNAB API access here: https://github.com/ynab/ynab-sdk-js
