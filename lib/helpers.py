import os
import sys


def fname_to_path(fname):
    dname = os.path.dirname(sys.argv[0])
    return os.path.join(dname, fname)


def set_environment(name, value):
    print("Setting environment {} = {}".format(name, value))
    os.environ[name.upper()] = value


def get_environment(name):
    return os.environ.get(name.upper())
