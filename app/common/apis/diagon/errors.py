"""Diagon API client errors."""

from app.common.errors import APIClientError


class DiagonAPIClientError(APIClientError):
    """Error raised when Diagon API client encounters an issue."""

    pass  # noqa: WPS420, WPS604
