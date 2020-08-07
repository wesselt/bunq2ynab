import argparse
import json
import logging
import os
import sys

from lib import helpers
from lib import log as log_module
from lib.log import log


class Config:
    config_fn = helpers.fname_to_path("config.json")

    def __init__(self):
       self.parser = argparse.ArgumentParser()
       self.add_default_arguments()


    def add_default_arguments(self):
        self.parser.add_argument("--log-level",
            help="Set log level to debug, info, warning, error, or critical")
        self.parser.add_argument("-v", "--verbose",
            action="store_const", const="True",
            help="Show content of JSON messages")
        self.parser.add_argument("-vv", "--headers",
            action="store_const", const="True",
            help="Show HTTP headers")
        self.parser.add_argument("--single-ip",
            action="store_const", const="True",
            help="Register BUNQ device-server with a single IP address " +
                "instead of a wildcard for all IPs.")
        self.parser.add_argument("-d", "--detailed",
            action="store_const", const=True,
            help="Write detailed logs, including timestamp and source line")


    def load(self):

        # Add command line settings
        args = self.parser.parse_args()
        self.config = {}
        for k, v in vars(args).items():
            self.config[k] = v
        self.read_json_config()

        log_module.load_config(self)


    def __getitem__(self, name):
        if not hasattr(self, "config"):
            raise Exception("Load config before using it")
        if not name in self.config:
            raise Exception("Unknown configuration \"{}\"".format(name))
        return self.config[name]


    def get(self, name, default=None):
        if not hasattr(self, "config"):
            raise Exception("Load config before using it")
        return self.config.get(name, default)


    def read_json_config(self):
        if not os.path.exists(self.config_fn):
            example_config = {
                "api_token": "enter bunq api key here",
                "personal_access_token": "enter ynab token here"
            }
            with open(self.config_fn, "w") as f:
                json.dump(example_config, f, indent=4)
            log.critical("Missing configuration.  Example created, please " +
                "edit " + self.config_fn)
            sys.exit(1)

        with open(self.config_fn) as f:
            self.config.update(json.load(f))

        if (self.config["api_token"] == "enter bunq api key here" or
            self.config["personal_access_token"] == "enter ynab token here"):
            log.critical("Configuration incomplete, please edit " +
                self.config_fn)
            sys.exit(1)


config = Config()
