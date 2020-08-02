import argparse
import json
import os


from lib import helpers
from lib.config import config


# -----------------------------------------------------------------------------

class State:
    state_fn = helpers.fname_to_path("state.json")

    def __init__(self):
        self.state = {
            "private_key": "",
            "private_key_for_api_token": "",
            "installation_token": "",
            "device_registered": "",
            "session_token": ""
        }
        self.loaded = False


    def load(self):
        if config.get("environment"):
            for k in self.state:
                self.state[k] = helpers.get_environment(k)
        else:
            if os.path.exists(self.state_fn):
                # make sure we have write access
                with open(self.state_fn, "r+") as f:
                    self.state.update(json.load(f))
            else:
                self.write_json()
        self.loaded = True


    def get(self, name):
        if not self.loaded:
            self.load()
        if name in self.state:
            return self.state[name]
        raise Exception("State {} not found".format(name))


    def set(self, name, value):
        if not self.loaded:
            self.load()
        if name not in self.state:
            raise Exception("Cannot set unknown state: {}".format(name))
        self.state[name] = value
        if config.get("environment"):
            helpers.set_environment(name, value)
        else:
            self.write_json()


    def write_json(self):
        with open(self.state_fn, "w") as f:
            json.dump(self.state, f, indent=4)
    


state = State()
