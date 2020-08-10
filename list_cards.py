import json
import sys
from pprint import pprint

from lib import bunq
from lib import bunq_api
from lib.config import config


config.parser.add_argument("bunq_user_name",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
config.load()

bunq_user_id = bunq_api.get_user_id(config.get("bunq_user_name"))

method = ("v1/user/{0}/card".format(bunq_user_id))
cards = bunq.get(method)
for cc in cards:
    for k, v in cc.items():
        print("{0:<10} {1}".format(
            v["id"],
            v["product_type"]).lower())
        print("     {0}{1}".format(
            v["type"],
            "/" + v["sub_type"] if v["sub_type"] != "NONE" else "").lower())
        print("     {0}{1}".format(
            v["status"],
            "/" + v["sub_status"] if v["sub_status"] != "NONE" else "").lower())
        for pan in v["primary_account_numbers"]:
            print("        \"{}\"     {}".format(
                pan["description"],
                pan["type"].lower()))

