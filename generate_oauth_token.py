# spin up temporary webserver running on port 3000
# open OAuth authorization request URL in browser

# capture the data coming from bunq and stop webserver
# exchange token with bunq for access token
# print the access token as the api token!
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from functools import partial
import webbrowser
import os
import sys
from urllib.parse import urlparse, parse_qs, urlencode
import uuid

from lib.config import config


class MyRequestHandler(BaseHTTPRequestHandler):
    def __init__(
        self,
        oauth_state,
        oauth_client_id,
        oauth_client_secret,
        oauth_redirect_url,
        *args,
        **kwargs,
    ):
        self.oauth_state = oauth_state
        self.oauth_client_id = oauth_client_id
        self.oauth_client_secret = oauth_client_secret
        self.oauth_redirect_url = oauth_redirect_url

        super().__init__(*args, **kwargs)

    def _set_response(self, content_type="text/html", response_code=200):
        self.send_response(response_code)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_GET(self):
        print(f"Got a response from Bunq!")

        parsed_url = urlparse(self.path)
        query_parameters = parse_qs(parsed_url.query)

        if self.oauth_state != query_parameters["state"][0]:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(
                str.encode(
                    "<div>Oauth state does not match, something fishy is going on! Please remove the oauth app from your bunq account and try again.</div>"
                )
            )
            return

        access_token = put_token_exchange(
            code=query_parameters["code"][0],
            oauth_client_id=self.oauth_client_id,
            oauth_client_secret=self.oauth_client_secret,
            oauth_redirect_url=self.oauth_redirect_url,
        )

        self.send_response(200)
        self.end_headers()
        self.wfile.write(
            str.encode(
                f"<div>Authentication successful! Access token for Bunq: {access_token}.</div>",
            )
        )
        self.wfile.write(
            str.encode(
                f"<div>Once you have copied the token you can close this window.</div>",
            )
        )


config.parser.add_argument("--oauth-client-id",
    help="OAuth client ID")
config.parser.add_argument("--oauth-client-secret",
    help="OAuth client secret")
config.parser.add_argument("--oauth-server-port", default=3000, type=int,
    help="OAuth server port (default: 3000)")
config.load()

server_port = config["oauth_server_port"]

oauth_state = str(uuid.uuid4())
oauth_client_id = config["oauth_client_id"]
oauth_client_secret = config["oauth_client_secret"]
oauth_redirect_url = f"http://localhost:{server_port}"


# From https://beta.doc.bunq.com/basics/oauth#token-exchange
def put_token_exchange(code, oauth_client_id, oauth_client_secret, oauth_redirect_url):
    bunq_base_token_url = "https://api.oauth.bunq.com/v1/token"
    bunq_token_params = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": oauth_client_id,
        "client_secret": oauth_client_secret,
        "redirect_uri": oauth_redirect_url,
    }

    # Encode the parameters
    encoded_token_params = urlencode(bunq_token_params)

    # From https://beta.doc.bunq.com/basics/oauth#token-exchange
    # construct the complete URL with parameters
    bunq_token_url = f"{bunq_base_token_url}?{encoded_token_params}"

    response = requests.post(bunq_token_url)
    return response.json()['access_token']


# From https://beta.doc.bunq.com/basics/oauth#authorization-request
def get_oauth_url(oauth_state, oauth_client_id, oauth_redirect_url):
    base_url = "https://oauth.bunq.com/auth"
    params = {
        "response_type": "code",
        "state": oauth_state,
        "client_id": oauth_client_id,
        "redirect_uri": oauth_redirect_url,
    }
    # Encode the parameters
    encoded_params = urlencode(params)
    url = f"{base_url}?{encoded_params}"
    return url


webbrowser.open(
    get_oauth_url(
        oauth_state=oauth_state,
        oauth_client_id=oauth_client_id,
        oauth_redirect_url=oauth_redirect_url,
    )
)

server_address = ("localhost", server_port)
handler = partial(
    MyRequestHandler,
    oauth_state,
    oauth_client_id,
    oauth_client_secret,
    oauth_redirect_url,
)
httpd = HTTPServer(server_address, handler)

print(f"Starting server on port {server_port}...")
httpd.handle_request()
print("Check the browser for the access token!")
