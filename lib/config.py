import argparse
import json
import os
import sys

from lib import helpers


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
            help="Use environment instead of state.json to store tokens")


    def load(self):
        self.read_json_config()

        # Add command line settings
        args = self.parser.parse_args()
        for k, v in vars(args).items():
            self.config[k] = v


    def __getitem__(self, name):
        return self.get(name)


    def get(self, name, default=None):
        if not self.config:
            raise Exception("Load config before using it")
        return self.config.get(name, default)


    def read_json_config(self):
        if not os.path.exists(self.config_fn):
            example_config = {
                "api-token": "enter bunq api key here",
                "personal-access-token": "enter ynab token here"
            }
            with open(self.config_fn, "w") as f:
                json.dump(example_config, f, indent=4)
            print("Missing configuration.  Created an example, please " +
                  "edit and update config.json.")
            sys.exit(1)

        with open(self.config_fn) as f:
            self.config = json.load(f)

        if (self.config["api_token"] == "enter bunq api key here" or
            self.config["personal_access_token"] == "enter ynab token here"):
            print("Missing configuration, please edit and update config.json.")
            sys.exit(1)


config = Config()
