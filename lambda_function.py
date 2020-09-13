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
    for acc in sync.get_bunq_accounts():
        bunq_api.add_callback(acc["bunq_user_id"], acc["bunq_account_id"],
                              "bunq2ynab-lambda", url)


def lambda_handler(event, context):
    try:
        config.load()

        sync = Sync()
        sync.populate()
        add_callbacks(sync)
        result = sync.synchronize()
        return {
            "statusCode": 200,
            "body": result
        }
    except Exception as e:
        log.exception("Exception occurred")
        return {
            "statusCode": 500,
            "body": str(e)
        }
