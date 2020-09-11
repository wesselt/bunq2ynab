from lib.sync import Sync
from lib.config import config
from lib.log import log


def lambda_handler(event, context):
    try:
        config.load()
        sync = Sync()
        sync.populate()
        result = sync.synchronize()
        return {
            "statusCode": 200,
            "body": result
        }
    except Exception as e:
        log.exception(e)
        raise
