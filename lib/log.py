import logging


def set_format(fmt):
    # Define our logging formatter
    formatter = logging.Formatter(fmt)

    # Create our stream handler and apply the formatting
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Add the stream handler to the logger
    log.handlers = []
    log.addHandler(stream_handler)


def load_config(config):
    if config["verbose"] or config["headers"]:
        log.setLevel(logging.DEBUG)
    elif config["log_level"]:
        log.setLevel(config["log_level"].upper())
    if config["detailed"]:
        set_format("%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d) " +
            "| %(message)s")


log = logging.getLogger()
log.setLevel(logging.INFO)
log.propagate = False
set_format("%(message)s")
