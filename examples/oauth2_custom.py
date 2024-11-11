# Example sourced from:
# https://dlthub.com/docs/general-usage/http/rest-client#oauth-20-authorization

# From the docs:
# Unfortunately, most OAuth 2.0 implementations vary, and thus you might need to subclass OAuth2ClientCredentials
# and implement build_access_token_request() to suit the requirements of the specific authorization server you want to interact with.

from typing import Dict, Any
from base64 import b64encode

import dlt
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import OAuth2ClientCredentials

class OAuth2ClientCredentialsHTTPBasic(OAuth2ClientCredentials):
    """Used e.g. by Zoom Video Communications, Inc."""
    def build_access_token_request(self) -> Dict[str, Any]:
        authentication: str = b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        return {
            "headers": {
                "Authorization": f"Basic {authentication}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "data": self.access_token_request_data,
        }

auth = OAuth2ClientCredentialsHTTPBasic(
    access_token_url=dlt.secrets["sources.zoom.access_token_url"],  # "https://zoom.us/oauth/token"
    client_id=dlt.secrets["sources.zoom.client_id"],
    client_secret=dlt.secrets["sources.zoom.client_secret"],
    access_token_request_data={
        "grant_type": "account_credentials",
        "account_id": dlt.secrets["sources.zoom.account_id"],
    },
)
client = RESTClient(base_url="https://api.zoom.us/v2", auth=auth)

response = client.get("/users")