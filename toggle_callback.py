import bunq
import json
import sys


bunq_user_name = sys.argv[1]
toggle_category = sys.argv[2]
toggle_url = sys.argv[3]


bunq_user_id = bunq.get_user_id(bunq_user_name)
method = "v1/user/{0}".format(bunq_user_id)
users = bunq.get(method)
for u in [u["UserPerson"] for u in users]:
    print("User: {0} ({1})".format(u["display_name"], u["id"]))
    new_notifications = []
    removed_notification = False
    for nf in u["notification_filters"]:
        if (nf["notification_delivery_method"] == "URL" and
              nf["category"] == toggle_category and
              nf.get("notification_target", None) == toggle_url):
            print("Removing callback...")
            removed_notification = True
        else:
            # Preserve any other callback
            new_notifications.append(nf)

    if not removed_notification:
        print("Adding callback...")
        new_notifications.append({
            "category": toggle_category,
            "notification_delivery_method": "URL",
            "notification_target": toggle_url,
        })
    print("Updating user...")
    data = {
        "notification_filters": new_notifications
    }
    method = "v1/user-person/{0}".format(bunq_user_id)
    users = bunq.put(method, data)
