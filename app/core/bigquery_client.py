"""BigQuery client bootstrap.
Authentication is handled automatically by the google-cloud SDK when
`GOOGLE_APPLICATION_CREDENTIALS` points to a service-account JSON key file.
For local dev you can also set `BIGQUERY_PROJECT_ID` and `BIGQUERY_KEY_FILE`
explicitly; in production both are inferred from the key file.
"""
from __future__ import annotations

import os

from google.cloud import bigquery

_client: bigquery.Client | None = None


def get_bigquery_client() -> bigquery.Client:
    """Return a process-wide BigQuery client, creating it on first call."""
    global _client

    if _client is not None:
        return _client

    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    key_filename = os.getenv("BIGQUERY_KEY_FILE")

    if key_filename:
        _client = bigquery.Client.from_service_account_json(
            key_filename, project=project_id
        )
    else:
        _client = bigquery.Client(project=project_id)

    return _client
