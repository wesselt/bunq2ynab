import logging
import os


def set_format(fmt):
    # Define our logging formatter
    formatter = logging.Formatter(fmt)

    # Create our stream handler and apply the formatting
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Add the stream handler to the logger
    log.handlers = []
    log.addHandler(stream_handler)


loglevel_set = False


def set_log_level(source, loglevel):
    global loglevel_set
    if loglevel_set:
        return
    loglevel_set = True
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise Exception('Invalid log level "{}" from {}'
                        .format(loglevel, source))
    log.setLevel(loglevel.upper())


log = logging.getLogger()
if os.environ.get("LOG_LEVEL"):
    set_log_level("environment variable", os.environ["LOG_LEVEL"])
else:
    log.setLevel(logging.INFO)
log.propagate = False
set_format("%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d) " +
    "| %(message)s")
