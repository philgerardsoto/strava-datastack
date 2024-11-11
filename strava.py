from typing import Dict, Any, Optional

import dlt
from dlt.sources.helpers.rest_client.auth import OAuth2ClientCredentials
from dlt.common.pendulum import pendulum
from dlt.sources.rest_api import (
    RESTAPIConfig,
    check_connection,
    rest_api_resources,
    rest_api_source,
)

class OAuth2ClientCredentialsHTTPRefresh(OAuth2ClientCredentials):
    def build_access_token_request(self) -> Dict[str, Any]:
        # Refresh token request doesn't require authentication (or base64 encoding)
        return {
            "headers": {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "data": self.access_token_request_data,
        }

def auth_strava():
    return OAuth2ClientCredentialsHTTPRefresh(
        access_token_url=dlt.secrets["sources.strava.credentials.access_token_url"],
        # Request body for a refresh token request
        access_token_request_data={
            "grant_type": "refresh_token",
            "refresh_token": dlt.secrets["sources.strava.credentials.refresh_token"], # refresh token scoped with read_all, activity:read_all, profile:read_all
            "client_id": dlt.secrets["sources.strava.credentials.client_id"],
            "client_secret": dlt.secrets["sources.strava.credentials.client_secret"],
            # "scope": dlt.secrets["sources.strava.credentials.scope"] <- could pass in a scope to limit scope of access token returned
        },
        default_token_expiration=21600,  # 6 hours in seconds
    )

@dlt.source(name="strava")
def strava_source():
    # Create a REST API configuration for the GitHub API
    # Use RESTAPIConfig to get autocompletion and type checking
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://www.strava.com/api/v3/",
            # we add an auth config if the auth token is present
            "auth": auth_strava(),
        },
        # The default configuration for all resources and their endpoints
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "replace",
            "endpoint": {
                "params": {
                    "per_page": 30, # default for strava; max is 200
                },
                "paginator": {
                    "type": "json_link",
                    "next_url_path": "pagination.next",
                },
            },
        },
        "resources": [
            # This is a simple resource definition,
            # that uses the endpoint path as a resource name:
            # "pulls",
            # Alternatively, you can define the endpoint as a dictionary
            # {
            #     "name": "pulls", # <- Name of the resource
            #     "endpoint": "pulls",  # <- This is the endpoint path
            # }
            # Or use a more detailed configuration:
            {
                "name": "activities",
                "primary_key": "id",
                "endpoint": {
                    "path": "activities",
                    # Query parameters for the endpoint
                    "params": {
                        "sort": "start_date",
                        "direction": "desc",
                        "state": "open",
                        # Define `since` as a special parameter
                        # to incrementally load data from the API.
                        # This works by getting the updated_at value
                        # from the previous response data and using this value
                        # for the `since` query parameter in the next request.
                        "since": {
                            "type": "incremental",
                            "cursor_path": "start_date",
                            "initial_value": pendulum.today().subtract(days=30).to_iso8601_string(),
                        },
                    },
                },
            },
            # The following is an example of a resource that uses
            # a parent resource (`activities`) to get the `activity_id`
            # and include it in the endpoint path:
            {
                "name": "activity_kudos",
                "primary_key": None,
                "endpoint": {
                    # The placeholder {activity_id} will be resolved
                    # from the parent resource
                    "path": "activities/{activity_id}/kudos",
                    "params": {
                        # The value of `activity_id` will be taken
                        # from the `id` field in the `activities` resource
                        "activity_id": {
                            "type": "resolve",
                            "resource": "activities",
                            "field": "id",
                        }
                    },
                },
                # Include data from `id` field of the parent resource
                # in the child data. The field name in the child data
                # will be called `_issues_id` (_{resource_name}_{field_name})
                "include_from_parent": ["id"],
            },
            {
                "name": "activity_streams",
                "primary_key": None,
                "max_table_nesting": 0, # the data field is an array, and this tells dlt not to flatten it out into another table (e.g. activity_streams__data); default is 1
                "endpoint": {
                    # The placeholder {issue_number} will be resolved
                    # from the parent resource
                    "path": "activities/{activity_id}/streams",
                    "params": {
                        # specifies the desired streams types (param for strava)
                        "keys": "time,distance,altitude,velocity_smooth,heartrate,cadence,watts,temp,moving,grade_smooth", # not used: latlng
                        "activity_id": {
                            "type": "resolve",
                            "resource": "activities",
                            "field": "id",
                        }
                    },
                },
                "include_from_parent": ["id"],
            }
        ],
    }

    yield from rest_api_resources(config)

def load_strava() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="rest_api_strava",
        destination='duckdb',
        dataset_name="rest_api_data",
        progress="log",
    )

    load_info = pipeline.run(strava_source())
    print(load_info)


if __name__ == "__main__":
    load_strava()
