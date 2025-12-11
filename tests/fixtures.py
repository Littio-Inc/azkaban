"""Shared test fixtures and constants for Cassandra API tests."""

from decimal import Decimal

from app.common.apis.cassandra.dtos import QuoteResponse

# Test constants
CURRENCY_USD = "USD"
CURRENCY_COP = "COP"
QUOTE_ID_TEST = "quote123"

# Timestamp constants
TEST_TIMESTAMP = "2024-01-01T00:00:00"
TEST_TIMESTAMP_UTC = "2024-01-01T00:00:00Z"


def create_test_quote_response(quote_id: str = QUOTE_ID_TEST) -> QuoteResponse:
    """Create a test QuoteResponse with default values.

    Args:
        quote_id: Quote ID to use

    Returns:
        QuoteResponse with test data
    """
    return QuoteResponse(
        quote_id=quote_id,
        base_currency=CURRENCY_USD,
        quote_currency=CURRENCY_COP,
        base_amount=Decimal("100.0"),
        quote_amount=Decimal("1000.0"),
        rate=Decimal("10.0"),
        balam_rate=Decimal("1.5"),
        fixed_fee=Decimal("0"),
        pct_fee=Decimal("0"),
        status="active",
        expiration_ts=TEST_TIMESTAMP,
        expiration_ts_utc=TEST_TIMESTAMP_UTC,
    )

