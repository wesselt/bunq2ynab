# bunq2ynab

Bunq2ynab is a python script that synchronizes [bunq](https://bunq.com) accounts with [YNAB](https://youneedabudget.com) accounts.

You'll need a key from both parties to enable synchronization:
1. Create a BUNQ "API key" in the BUNQ mobile app.  On the profile tab (3rd icon bottom row), click the dots to the top right, then Security & Preferences, then Developers, then API keys, then "Add API Key".  Choose to "Reveal" the API key and share it.
2. Create a YNAB "Personal Access Token" in the YNAB website https://app.youneedabudget.com/settings/developer.
Store the token in "personal_access_token.txt".  If you don't see the developer section, [request it here](https://support.youneedabudget.com/t/x1p42s/unable-to-generate-api-access-token-no-developer-section-under-my-account).

An easy way to run bunq2ynab is in the Amazon cloud.  You can also run bunq2ynab on a local python installation.  Both options are explained below.

## Running from the AWS Serverless Application Store

TODO

## Command line installation

1. Install [Python 3](https://www.python.org/) and the required dependencies: `pip3 install -r requirements.txt`.  Bunq2ynab depends on [Requests](http://docs.python-requests.org/en/master/) and [pyOpenSSL](https://pyopenssl.org/en/stable/install.html) to communicate with bunq, [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) for AWS integration, and [libminiupnpc](http://miniupnp.free.fr/) to run behind a NAT gateway.
2. Create a file "config.json" with contents like:
```
{
    "api_token": "your bunq api key",
    "personal_access_token": "your ynab personal access token",
    "accounts": [{
        "bunq_account_name": "my bunq account",
        "ynab_budget_name": "my ynab budget",
        "ynab_account_name": "my ynab account"
    }]
}
```
3. Verify that the link with BUNQ works by requesting the list of users and accounts:
```
    python3 list_user.py
```
4. Verify that the link with YNAB works by requesting the list of budgets:
```
    python3 list_budget.py
```

## Manual synchronization

1. The bunq2ynab.py script synchronizes once:
```
    python3 bunq2ynab.py --all
```

## Automatic synchronization

1. Run `auto_sync.py` to set up a callback and start listening for push notifications.  If you have a private IP, the script will look for a UPNP gateway and set up a port forward. 
```
    python3 auto_sync.py
```
2. Auto synch tries to run as reliably as possible.  It refreshes the port forward every 8 hours and synchs periodically even without a forward.

## Links

- BUNQ API documentation: https://doc.bunq.com/
- YNAB API documentation: https://api.youneedabudget.com/
- YNAB API endpoints: https://api.youneedabudget.com/v1
- Request YNAB API access here: https://github.com/ynab/ynab-sdk-js
