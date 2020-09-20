from pprint import pprint

from lib import bunq
from lib import bunq_api
from lib.config import config


config.parser.add_argument("bunq_user_name", nargs="?",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
config.parser.add_argument("bunq_account_name", nargs='?',
    help="Bunq account name (retrieve using 'python3 list_user.py')")
config.parser.add_argument("toggle_url", nargs='?',
    help="URL to receive the callback (f.e. https://yourdomain.com:12345)")
config.load()


user_id = bunq_api.get_user_id(config.get("bunq_user_name"))
account_id = bunq_api.get_account_id(user_id, config.get("bunq_account_name"))
url = config.get("toggle_url")
nfs = bunq_api.get_notification_filters(user_id, account_id)
found = False
for nfi in nfs:
    cb = next(iter(nfi.values()))
    if (cb["category"] == "MUTATION" and
        cb["notification_target"] == url):
       found = True

if found:
    print("Removing toggle...")
    bunq_api.remove_callback(user_id, account_id, "bunq2ynab-toggle")
else:
    print("Adding toggle...")
    bunq_api.add_callback(user_id, account_id, "bunq2ynab-toggle", url)
