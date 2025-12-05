"""Common error classes for the application."""


class ServiceError(Exception):
    """Base exception for service errors."""

    message: str
    metadata: dict | None

    def __init__(self, message: str, metadata: dict | None = None) -> None:
        """Initialize service error.

        Args:
            message: Error message
            metadata: Optional error metadata
        """
        super().__init__(message)
        self.message = message
        self.metadata = metadata


class MissingCredentialsError(ServiceError):
    """Error raised when required credentials are missing."""

    pass  # noqa: WPS420, WPS604


class APIClientError(ServiceError):
    """Error raised when API client encounters an issue."""

    pass  # noqa: WPS420, WPS604
