import logging
import logging.handlers
import subprocess


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address = '/dev/log')
log.addHandler(handler)


def application(environ, start_response):
    log.debug("Incoming call")
    log.debug("Remove address = %s", environ["REMOTE_ADDR"])
    start_response('200 OK', [('Content-Type', 'application/json')])

    # Check Content-Type header
    #if environ.get("HTTP_CONTENT_TYPE", None) != "application/json":
    #    log.debug("Expected JSON content")
    #    return [b'{"error": "Expected JSON content"}']

    # Retrieve body
    #length = int(environ.get('CONTENT_LENGTH', '0'))
    #if not length:
    #    log.debug("Body is empty")
    #    return [b'{"error": "Body is empty"}']
    #body = environ['wsgi.input'].read(length)
    #log.debug(body)

    # Start synch script in background
    try:
        p = subprocess.Popen("bash ../run_bunq2ynab.sh", shell=True,
             stdin=None, stdout=None, stderr=None, close_fds=True)
        log.debug("Process started")
    except e:
        log.debug("Failed to start process")
        log.debug(e)
        return [b'{"error": "Error processing message"}']

    return [b'{"hannibal": "I love it when the plan comes together"}']
