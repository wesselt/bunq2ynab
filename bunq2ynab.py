import sys

from lib.sync import sync
from lib.config import config


config.parser.add_argument("--all", "-a", action="store_true",
    help="Synchronize all instead of recent transactions")
config.load()

sync.synchronize()
