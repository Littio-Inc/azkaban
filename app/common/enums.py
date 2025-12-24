"""Common enums for the Azkaban service."""

from enum import StrEnum


class Environment(StrEnum):
    """Represents the different deployment environments of the application."""

    LOCAL = "local"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class UserRole(StrEnum):
    """Represents user roles in the system."""

    ADMIN = "admin"
    USER = "user"


class TOTPStatus(StrEnum):
    """Represents TOTP configuration status."""

    NOT_CONFIGURED = "not_configured"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    DEACTIVATED = "deactivated"


class Provider(StrEnum):
    """Represents monetization providers."""

    KIRA = "kira"
    COBRE = "cobre"
    SUPRA = "supra"
