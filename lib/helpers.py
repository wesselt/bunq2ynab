import os
import sys


def fname_to_path(fname):
    dname = os.path.dirname(sys.argv[0])
    return os.path.join(dname, fname)


def format_seconds(total_secs):
    hours, remainder = divmod(total_secs, 60*60)
    minutes, remainder = divmod(remainder,60)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(remainder)
    if 10 <= hours:
       return "{} hours".format(hours)
    if hours and minutes:
        return "{} hours {} minutes".format(hours, minutes)
    if hours:
        return "{} hours".format(hours)
    if 10 <= minutes:
       return "{} minutes".format(minutes)
    if minutes and seconds: 
        return "{} minutes {} seconds".format(minutes, seconds)
    if minutes: 
        return "{} minutes".format(minutes)
    return "{} seconds".format(seconds)
