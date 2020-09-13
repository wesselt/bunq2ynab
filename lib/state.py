import json
import os


from lib.parameter_store import parameter_store
from lib import helpers
from lib.log import log


# -----------------------------------------------------------------------------

class State:
    state_fn = helpers.fname_to_path("state.json")
    ssm_path = "bunq2ynab-state"

    def __init__(self):
        self.state = {
            "private_key": "",
            "private_key_for_api_token": "",
            "installation_token": "",
            "device_registered": "",
            "session_token": "",
            "aws_callback": ""
        }
        self.loaded = False


    def load(self):
        if self.loaded:
            return
        if os.environ.get("AWS_REGION"):
            log.info('Fetching SSM state {0}'.format(self.ssm_path))
            resp = parameter_store.fetch_parameter(self.ssm_path)
            self.state.update(json.loads(resp))
        else:
            if os.path.exists(self.state_fn):
                # make sure we have write access
                with open(self.state_fn, "r+") as f:
                    self.state.update(json.load(f))
            else:
                # Write exmpty state
                self.write_state()
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
        self.write_state()


    def write_state(self):
        if os.environ.get("AWS_REGION"):
            log.info('Writing SSM state {0}'.format(self.ssm_path))
            parameter_store.put_parameter(self.ssm_path,
                json.dumps(self.state, indent=4))
        else:
            with open(self.state_fn, "w") as f:
                json.dump(self.state, f, indent=4)
    

state = State()
