from lib import bunq
from lib import bunq_api
from lib.config import config


config.parser.add_argument("bunq_user_name", nargs="?",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
config.parser.add_argument("bunq_account_name", nargs='?',
    help="Bunq account name (retrieve using 'python3 list_user.py')")
config.parser.add_argument("toggle_category", nargs='?',
    help="Callback category to toggle (f.e. MUTATION)")
config.parser.add_argument("toggle_url", nargs='?',
    help="URL to receive the callback (f.e. https://yourdomain.com:12345)")
config.load()


def update_notifications(nfs):
    new_notifications = []
    removed_notification = False
    for nfi in nfs:
        for nf in nfi.values():
            if (nf["category"] == config.get("toggle_category") and
              nf.get("notification_target", None) == config.get("toggle_url")):
                print("Removing callback...")
                removed_notification = True
            else:
                new_notifications.append({
                    "category": nf["category"],
                    "notification_target": nf["notification_target"]
                })

    if not removed_notification:
        print("Adding callback...")
        new_notifications.append({
            "category": config.get("toggle_category"),
            "notification_target": config.get("toggle_url"),
        })
    return new_notifications


bunq_user_id = bunq_api.get_user_id(config.get("bunq_user_name"))
if config.get("bunq_account_name"):
    bunq_account_id = bunq_api.get_account_id(bunq_user_id,
                                               config.get("bunq_account_name"))
    method = ("v1/user/" + bunq_user_id + "/monetary-account/" +
              bunq_account_id + "/notification-filter-url")
    old_nfs = bunq.get(method)
    new_nfs = update_notifications(old_nfs)
    bunq.post(method, {"notification_filters": new_nfs})
else:
    method = "v1/user/" + bunq_user_id + "/notification-filter-url"
    old_nfs = bunq.get(method)
    new_nfs = update_notifications(old_nfs)
    bunq.post(method, {"notification_filters": new_nfs})
