# bunq2ynab

Bunq2ynab is a Python script that synchronizes [bunq](https://bunq.com) accounts with [YNAB](https://youneedabudget.com) accounts.

You'll need a key from both bunq and YNAB to enable synchronization:
1. Create a bunq "API key" in the bunq mobile app.  On the profile tab (3rd icon bottom row), click the dots to the top right, then Security & Preferences, then Developers, then API keys, then "Add API Key".  Choose to "Reveal" the API key and share it.
2. Create a YNAB "Personal Access Token" in the YNAB website through the top-left menu, then Account Settings, then Developers. Or you can follow this link straight to the Developers page: https://app.youneedabudget.com/settings/developer.

The easiest way to run bunq2ynab is in the Amazon cloud.  You can also run bunq2ynab on a local python installation.  Both options are explained below.

## Running from the AWS Serverless Application Store

TODO

## Local Python installation

Bunq2ynab requires [Python 3.5](https://www.python.org/) or higher.  Install this however you like; on my [Raspberry Pi](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/) with [Raspbian](https://www.raspbian.org/), it's `sudo apt-get python3`.  You can install the required Python packages with your OS's version of `pip3 install -r requirements.txt`.

1. Clone the repository:
```
git clone git@github.com:wesselt/bunq2ynab.git
```
2. Create a file "config.json" with contents like the one below.  You can enter `*` or omit the row entirely to have bunq2ynab match accounts by name.  Note that if you wildcard the YNAB budget name, one bunq account may end up synching with multiple YNAB accounts in different budgets.
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
3. Verify that the link with bunq works by requesting the list of users and accounts:
```
    python3 list_user.py
```
4. Verify that the link with YNAB works by requesting the list of budgets:
```
    python3 list_budget.py
```

## Manual synchronization

The bunq2ynab.py script synchronizes once.
```
    python3 bunq2ynab.py
```
Add `--all` to force it to synchronize all transactions.  You can run this from a cron job to synchronize on a schedule.

## Automatic synchronization

Run `auto_sync.py` to set up a callback and start listening for push notifications.  If you have a private IP, the script will look for a UPNP gateway and set up a port forward. 
```
    python3 auto_sync.py
```
Auto synch tries to run as reliably as possible.  Every 8 hours it refreshes the port forward.  This way it keeps working when your ISP assigned IP changes.  After refreshing the port forward, auto_synch synchronizes even if it has not received a callback.

## Links

- bunq API documentation: https://doc.bunq.com/
- YNAB API documentation: https://api.youneedabudget.com/
- YNAB API endpoints: https://api.youneedabudget.com/v1
