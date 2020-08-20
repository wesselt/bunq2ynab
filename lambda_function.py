from lib.sync import Sync
from lib.config import config


def lambda_handler(event, context):
    config.load()
    sync = Sync()
    sync.populate()
    sync.synchronize()
