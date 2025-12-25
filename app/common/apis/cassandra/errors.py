"""Cassandra API client errors."""

from app.common.errors import APIClientError


class CassandraAPIClientError(APIClientError):
    """Error raised when Cassandra API client encounters an issue."""

    def __init__(self, message: str, status_code: int | None = None, error_detail: dict | None = None) -> None:
        """Initialize Cassandra API client error.

        Args:
            message: Error message
            status_code: HTTP status code from Cassandra API (if available)
            error_detail: Error detail dictionary from Cassandra API (if available)
        """
        super().__init__(message)
        self.status_code = status_code
        self.error_detail = error_detail
