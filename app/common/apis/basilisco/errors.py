"""Basilisco API client errors."""

from app.common.errors import APIClientError


class BasiliscoAPIClientError(APIClientError):
    """Error raised when Basilisco API client encounters an issue."""

    pass  # noqa: WPS420, WPS604
