from lib.sync import Sync
from lib.config import config
import os


def handler(event, context):
    config.parser.add_argument("--all", "-a", action="store_true",
                               help="Synchronize all instead of recent transactions")
    config.load()

    sync = Sync()
    sync.populate()
    sync.synchronize()


try:
    os.environ['AWS_EXECUTION_ENV']
except KeyError:
    handler({}, {})
