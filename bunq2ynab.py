from lib.sync import Sync
from lib.config import config
import os


config.load()


sync = Sync()
sync.populate()
sync.synchronize()
