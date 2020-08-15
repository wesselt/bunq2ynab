from lib.sync import Sync
from lib.config import config


config.load()


def lambda_handler(event, context):
    sync = Sync()
    sync.populate()
    sync.synchronize()
