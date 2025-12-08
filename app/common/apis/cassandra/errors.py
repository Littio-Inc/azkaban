"""Cassandra API client errors."""

from app.common.errors import APIClientError


class CassandraAPIClientError(APIClientError):
    """Error raised when Cassandra API client encounters an issue."""

    pass  # noqa: WPS420, WPS604
