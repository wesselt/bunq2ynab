# spin up temporary webserver running on port 3000
# open OAuth authorization request URL in browser

# capture the data coming from bunq and stop webserver
# exchange token with bunq for access token
# print the access token as the api token!
from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser
import os
import sys
from urllib.parse import urlparse, parse_qs, urlencode
import requests


class MyRequestHandler(BaseHTTPRequestHandler):
    def _set_response(self, content_type="text/html", response_code=200):
        self.send_response(response_code)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_GET(self):
        print(f"Got a response from Bunq!")

        parsed_url = urlparse(self.path)
        query_parameters = parse_qs(parsed_url.query)

        self.server.response_state = query_parameters["state"][0]
        self.server.response_code = query_parameters["code"][0]

        self.send_response(200)
        self.end_headers()
        self.wfile.write(
            str.encode(
                "<div>Authentication successful, you can close this window now.</div>"
            )
        )


bunq_base_url = "https://oauth.bunq.com/auth"
client_id = os.environ["CLIENT_ID"]
client_secret = os.environ["CLIENT_SECRET"]
state = "kerk"
port = 3000
redirect_url = f"http://localhost:{port}"

bunq_params = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_url,
    "state": state,
}

# Encode the parameters
encoded_params = urlencode(bunq_params)

# From https://beta.doc.bunq.com/basics/oauth#authorization-request
# construct the complete URL with parameters
bunq_url = f"{bunq_base_url}?{encoded_params}"

webbrowser.open(bunq_url)

server_address = ("", port)
httpd = HTTPServer(server_address, MyRequestHandler)

print(f"Starting server on port {port}...")
httpd.handle_request()

if state != httpd.response_state:
    print(
        "Oauth state does not match, something fishy is going on! Please remove the oauth app from your bunq account and try again."
    )
    sys.exit(1)


bunq_base_token_url = "https://api.oauth.bunq.com/v1/token"
bunq_token_params = {
    "grant_type": "authorization_code",
    "code": httpd.response_code,
    "redirect_uri": redirect_url,
    "client_id": client_id,
    "client_secret": client_secret,
}

# Encode the parameters
encoded_token_params = urlencode(bunq_token_params)

# From https://beta.doc.bunq.com/basics/oauth#token-exchange
# construct the complete URL with parameters
bunq_token_url = f"{bunq_base_token_url}?{encoded_token_params}"

response = requests.post(bunq_token_url)


if response.status_code != 200:
    print(
        f"Token request failed with status code: {response.status_code} with content: {response.text}"
    )
    sys.exit(1)


access_token = response.json()["access_token"]

print(f"You have successfully created an access token for Bunq: {access_token}")
