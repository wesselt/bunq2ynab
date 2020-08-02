import argparse
import json
import os

from lib import helpers


# -----------------------------------------------------------------------------

class Config:
    config_fn = helpers.fname_to_path("config.json")

    def __init__(self):
       self.parser = argparse.ArgumentParser()
       self.add_default_arguments()


    def add_default_arguments(self):
        self.parser.add_argument("-v", "--verbose",
            action="store_const", const="True",
            help="Show content of JSON messages")
        self.parser.add_argument("-vv", "--verboseverbose",
            action="store_const", const="True",
            help="Show JSON messages and HTTP headers")
        self.parser.add_argument("--single-ip",
            action="store_const", const="True",
            help="Register BUNQ device-server with a single IP address " +
                "instead of a wildcard for all IPs.")
        self.parser.add_argument("-e", "--environment",
            action="store_const", const=True,
            help="Use environment instead of config.json to store tokens")
        self.parser.add_argument("--api-token",
            action="store", help=argparse.SUPPRESS)
        self.parser.add_argument("--personal-access-token",
            action="store", help=argparse.SUPPRESS)


    def load(self):
        args = self.parser.parse_args()
        self.config = vars(args)

        json_config = self.read_json_config()

        for name in self.config:
            if self.config[name] is None:
                self.config[name] = helpers.get_environment(name)
            if self.config[name] is None:
                self.config[name] = json_config.get(name)


    def get(self, name):
        if not self.config:
            raise Exception("Load config before using it")
        if name in self.config:
            return self.config[name]
        raise Exception("Configuration {} not found".format(name))


    def read_json_config(self):
        if not os.path.exists(self.config_fn):
            example_config = {
                "api-token": "enter bunq api key here",
                "personal-access-token": "enter ynab token here"
            }
            with open(self.config_fn, "w") as f:
                json.dump(example_config, f, indent=4)

        with open(self.config_fn) as f:
            return json.load(f)


config = Config()
