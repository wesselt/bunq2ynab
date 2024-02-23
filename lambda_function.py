import json
import traceback

from lib.sync import Sync
from lib.config import config
from lib.state import state
from lib.log import log
from lib import bunq_api


def add_callbacks(sync):
    url = state.get("aws_callback")
    log.info("SSM callback = \"{}\"".format(url))
    if not url:
        return
    log.info("Adding callbacks...")
    for uid in sync.get_bunq_user_ids():
        callback_marker = config.get("callback_marker") or "bunq2ynab-autosync"
        bunq_api.add_callback(uid, callback_marker, url)


def get_iban_from_event(event):
    body_str = event.get("body")
    if not body_str:
        log.info("No request body found")
        return
    try:
        body = json.loads(body_str)
    except json.JSONDecodeError as e:
        log.error("Error decoding quest body as JSON: {}".format(e))
        return
    nu = body.get("NotificationUrl", {})
    category = nu.get("category")
    if category != "MUTATION":
        log.error("Category is not MUTATION but {}".format(e))
        return
    iban = nu.get("object", {}).get("Payment", {}).get("alias", {}).get("iban")
    if not iban:
        log.error("No IBAN found in request body")
        return
    log.info("Found IBAN {} in request body".format(iban))
    return iban


def lambda_handler(event, context):
    try:
        config.load()
        iban = get_iban_from_event(event)

        sync = Sync()
        sync.populate()
        if iban:
            result = sync.synchronize_iban(iban)
        else:
            result = sync.synchronize()
        add_callbacks(sync)
        return {
            "statusCode": 200,
            "body": result
        }
    except Exception as e:
        log.exception("Exception occurred")
        return {
            "statusCode": 500,
            "body": traceback.format_exc()
        }
