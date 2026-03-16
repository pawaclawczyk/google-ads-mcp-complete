"""Shared fixtures for unit tests."""

import pytest
from unittest.mock import MagicMock

from google.ads.googleads.errors import GoogleAdsException

from src.auth import GoogleAdsAuthManager
from src.error_handler import ErrorHandler
from src.tools_budgets import BudgetTools


class MockGoogleAdsException(GoogleAdsException):
    """Minimal GoogleAdsException subclass for unit tests."""

    def __init__(self, error_codes=None):
        self.failure = MagicMock()
        errors = []
        for code in error_codes or []:
            err = MagicMock()
            err.error_code = code
            errors.append(err)
        self.failure.errors = errors


def make_mutate_response(resource_name: str) -> MagicMock:
    """Build a mock MutateCampaignBudgetsResponse with one result."""
    mock_result = MagicMock()
    mock_result.resource_name = resource_name
    mock_response = MagicMock()
    mock_response.results = [mock_result]
    return mock_response


@pytest.fixture
def mock_auth_manager():
    return MagicMock(spec=GoogleAdsAuthManager)


@pytest.fixture
def mock_error_handler():
    return MagicMock(spec=ErrorHandler)


@pytest.fixture
def mock_budget_service():
    return MagicMock()


@pytest.fixture
def mock_googleads_service():
    return MagicMock()


@pytest.fixture
def mock_client(mock_budget_service, mock_googleads_service):
    client = MagicMock()

    service_map = {
        "CampaignBudgetService": mock_budget_service,
        "GoogleAdsService": mock_googleads_service,
    }
    client.get_service.side_effect = lambda name: service_map[name]
    return client


@pytest.fixture
def budget_tools(mock_auth_manager, mock_error_handler, mock_client):
    mock_auth_manager.get_client.return_value = mock_client
    return BudgetTools(mock_auth_manager, mock_error_handler)


@pytest.fixture
def make_budget_row():
    """Factory fixture: returns a callable that builds a mock search result row."""

    def _make(
        budget_id=123,
        name="Test Budget",
        amount_micros=5_000_000,
        total_amount_micros=0,
        period_name="DAILY",
        delivery_method_name="STANDARD",
        status_name="ENABLED",
        explicitly_shared=True,
        reference_count=0,
        type_name="STANDARD",
        has_recommended_budget=False,
        recommended_budget_amount_micros=0,
    ):
        row = MagicMock()
        budget = row.campaign_budget
        budget.id = budget_id
        budget.name = name
        budget.amount_micros = amount_micros
        budget.total_amount_micros = total_amount_micros
        budget.period.name = period_name
        budget.delivery_method.name = delivery_method_name
        budget.status.name = status_name
        budget.explicitly_shared = explicitly_shared
        budget.reference_count = reference_count
        budget.type_.name = type_name
        budget.has_recommended_budget = has_recommended_budget
        budget.recommended_budget_amount_micros = recommended_budget_amount_micros
        return row

    return _make
