import os
import sys


def fname_to_path(fname):
    dname = os.path.dirname(sys.argv[0])
    return os.path.join(dname, fname)
