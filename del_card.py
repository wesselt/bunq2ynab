import json
import sys

from lib import bunq
from lib import bunq_api
from lib.config import config


config.parser.add_argument("bunq_user_name",
    help="Bunq user name (retrieve using 'python3 list_user.py')")
config.parser.add_argument("card_id",
    help="Bunq card id (retrieve using 'python3 list_cards.py')")
config.parser.add_argument("status",
    help="Status to set card to")
config.load()

bunq_user_id = bunq_api.get_user_id(config.get("bunq_user_name"))

card_id = config["card_id"]
status = config["status"].upper()
print("Setting card {} to status {}....".format(card_id, status))

method = ("v1/user/{}/card/{}"
          .format(bunq_user_id, card_id))
data = {"status": status}
bunq.put(method, data)
