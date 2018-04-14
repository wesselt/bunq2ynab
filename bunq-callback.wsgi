import logging
import logging.handlers
import subprocess


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address='/dev/log')
log.addHandler(handler)


def try_application(environ):
    log.debug("Remove address = %s", environ["REMOTE_ADDR"])
    log.debug("Starting process...")
    subprocess.Popen("/bin/bash ../run_bunq2ynab.sh", shell=True,
                     stdin=None, stdout=None, stderr=None, close_fds=True)
    log.debug("Process started")


def application(environ, start_response):
    log.debug("Incoming call")
    try:
        try_application(environ)
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [b'{"hannibal": "I love it when the plan comes together"}']
    except Exception as e:
        log.debug("Exception processing message")
        log.debug(e)
        start_response('500 ERROR', [('Content-Type', 'application/json')])
        return [b'{"murdock": "Looks like we\'re going to crash"}']
