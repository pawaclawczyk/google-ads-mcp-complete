"""Fixtures for integration tests (requires real Google Ads credentials)."""

import os
import pytest

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv is a main dep; this is a safety guard only


@pytest.fixture(scope="session")
def customer_id():
    cid = os.getenv("TEST_CUSTOMER_ID")
    if not cid:
        pytest.skip("TEST_CUSTOMER_ID env var not set; skipping integration tests")
    return cid.replace("-", "")


@pytest.fixture(scope="session")
def budget_tools(customer_id):  # noqa: F811 (shadows outer scope intentionally)
    from src.auth import GoogleAdsAuthManager
    from src.error_handler import ErrorHandler
    from src.tools_budgets import BudgetTools

    try:
        auth = GoogleAdsAuthManager()
        error_handler = ErrorHandler()
        return BudgetTools(auth, error_handler)
    except Exception as exc:
        pytest.skip(f"Could not initialise BudgetTools: {exc}")
