"""Unit tests for src/tools_budgets.py."""

import pytest
from unittest.mock import MagicMock

from tests.unit.conftest import MockGoogleAdsException, make_mutate_response

CUSTOMER_ID = "1234567890"
BUDGET_ID = "456"


# ---------------------------------------------------------------------------
# create_budget
# ---------------------------------------------------------------------------


class TestCreateBudget:
    async def test_create_budget_daily_success(
        self, budget_tools, mock_budget_service, mock_client
    ):
        resource_name = f"customers/{CUSTOMER_ID}/campaignBudgets/{BUDGET_ID}"
        mock_budget_service.mutate_campaign_budgets.return_value = make_mutate_response(resource_name)

        result = await budget_tools.create_budget(
            customer_id=CUSTOMER_ID,
            name="Daily Budget",
            amount_micros=5_000_000,
            period="DAILY",
        )

        assert result["success"] is True
        assert result["budget_id"] == BUDGET_ID
        assert result["budget_resource_name"] == resource_name
        assert result["period"] == "DAILY"
        assert result["amount"] == 5.0
        mock_budget_service.mutate_campaign_budgets.assert_called_once()

    async def test_create_budget_custom_period_success(
        self, budget_tools, mock_budget_service
    ):
        resource_name = f"customers/{CUSTOMER_ID}/campaignBudgets/{BUDGET_ID}"
        mock_budget_service.mutate_campaign_budgets.return_value = make_mutate_response(resource_name)

        result = await budget_tools.create_budget(
            customer_id=CUSTOMER_ID,
            name="Campaign Total Budget",
            total_amount_micros=100_000_000,
            period="CUSTOM_PERIOD",
        )

        assert result["success"] is True
        assert result["period"] == "CUSTOM_PERIOD"
        assert result["total_amount"] == 100.0
        assert result["explicitly_shared"] is False

    async def test_create_budget_daily_missing_amount_micros(self, budget_tools):
        result = await budget_tools.create_budget(
            customer_id=CUSTOMER_ID,
            name="Bad Budget",
            period="DAILY",
            # amount_micros intentionally omitted
        )

        assert result["success"] is False
        assert result["error_type"] == "ValidationError"
        assert "amount_micros" in result["error"]

    async def test_create_budget_custom_period_missing_total_amount(self, budget_tools):
        result = await budget_tools.create_budget(
            customer_id=CUSTOMER_ID,
            name="Bad Budget",
            period="CUSTOM_PERIOD",
            # total_amount_micros intentionally omitted
        )

        assert result["success"] is False
        assert result["error_type"] == "ValidationError"
        assert "total_amount_micros" in result["error"]

    async def test_create_budget_custom_period_explicitly_shared_true(self, budget_tools):
        result = await budget_tools.create_budget(
            customer_id=CUSTOMER_ID,
            name="Bad Budget",
            period="CUSTOM_PERIOD",
            total_amount_micros=50_000_000,
            explicitly_shared=True,
        )

        assert result["success"] is False
        assert result["error_type"] == "ValidationError"
        assert "explicitly_shared" in result["error"]

    async def test_create_budget_google_ads_exception(
        self, budget_tools, mock_budget_service
    ):
        mock_budget_service.mutate_campaign_budgets.side_effect = MockGoogleAdsException()

        result = await budget_tools.create_budget(
            customer_id=CUSTOMER_ID,
            name="Budget",
            amount_micros=1_000_000,
        )

        assert result["success"] is False
        assert result["error_type"] == "GoogleAdsException"

    async def test_create_budget_unexpected_exception(
        self, budget_tools, mock_budget_service
    ):
        mock_budget_service.mutate_campaign_budgets.side_effect = RuntimeError("network down")

        result = await budget_tools.create_budget(
            customer_id=CUSTOMER_ID,
            name="Budget",
            amount_micros=1_000_000,
        )

        assert result["success"] is False
        assert result["error_type"] == "UnexpectedError"
        assert "network down" in result["error"]


# ---------------------------------------------------------------------------
# update_budget
# ---------------------------------------------------------------------------


class TestUpdateBudget:
    async def test_update_budget_amount_success(
        self, budget_tools, mock_budget_service
    ):
        mock_budget_service.mutate_campaign_budgets.return_value = MagicMock()

        result = await budget_tools.update_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
            amount_micros=10_000_000,
        )

        assert result["success"] is True
        assert "amount_micros" in result["updated_fields"]
        mock_budget_service.mutate_campaign_budgets.assert_called_once()

    async def test_update_budget_name_success(
        self, budget_tools, mock_budget_service
    ):
        mock_budget_service.mutate_campaign_budgets.return_value = MagicMock()

        result = await budget_tools.update_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
            name="Renamed Budget",
        )

        assert result["success"] is True
        assert "name" in result["updated_fields"]

    async def test_update_budget_multiple_fields(
        self, budget_tools, mock_budget_service
    ):
        mock_budget_service.mutate_campaign_budgets.return_value = MagicMock()

        result = await budget_tools.update_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
            amount_micros=8_000_000,
            name="Updated",
            delivery_method="ACCELERATED",
        )

        assert result["success"] is True
        assert set(result["updated_fields"]) == {"amount_micros", "name", "delivery_method"}

    async def test_update_budget_no_fields(self, budget_tools):
        result = await budget_tools.update_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
        )

        assert result["success"] is False
        assert result["error_type"] == "ValidationError"
        assert "At least one field" in result["error"]

    async def test_update_budget_mutually_exclusive(self, budget_tools):
        result = await budget_tools.update_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
            amount_micros=5_000_000,
            total_amount_micros=50_000_000,
        )

        assert result["success"] is False
        assert result["error_type"] == "ValidationError"
        assert "mutually exclusive" in result["error"]

    async def test_update_budget_explicitly_shared_false(self, budget_tools):
        result = await budget_tools.update_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
            explicitly_shared=False,
        )

        assert result["success"] is False
        assert result["error_type"] == "ValidationError"
        assert "explicitly_shared" in result["error"]

    async def test_update_budget_explicitly_shared_true(
        self, budget_tools, mock_budget_service
    ):
        mock_budget_service.mutate_campaign_budgets.return_value = MagicMock()

        result = await budget_tools.update_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
            explicitly_shared=True,
        )

        assert result["success"] is True
        assert "explicitly_shared" in result["updated_fields"]

    async def test_update_budget_google_ads_exception(
        self, budget_tools, mock_budget_service
    ):
        mock_budget_service.mutate_campaign_budgets.side_effect = MockGoogleAdsException()

        result = await budget_tools.update_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
            amount_micros=1_000_000,
        )

        assert result["success"] is False
        assert result["error_type"] == "GoogleAdsException"


# ---------------------------------------------------------------------------
# list_budgets
# ---------------------------------------------------------------------------


class TestListBudgets:
    async def test_list_budgets_success(
        self, budget_tools, mock_googleads_service, make_budget_row
    ):
        rows = [
            make_budget_row(budget_id=1, name="Budget A", amount_micros=2_000_000),
            make_budget_row(budget_id=2, name="Budget B", amount_micros=4_000_000),
        ]
        mock_googleads_service.search.return_value = iter(rows)

        result = await budget_tools.list_budgets(customer_id=CUSTOMER_ID)

        assert result["success"] is True
        assert result["count"] == 2
        budgets = result["budgets"]
        assert budgets[0]["id"] == "1"
        assert budgets[0]["name"] == "Budget A"
        assert budgets[0]["amount"] == 2.0
        assert budgets[0]["period"] == "DAILY"
        assert budgets[0]["status"] == "ENABLED"
        assert budgets[1]["id"] == "2"
        assert budgets[1]["amount"] == 4.0

    async def test_list_budgets_empty(
        self, budget_tools, mock_googleads_service
    ):
        mock_googleads_service.search.return_value = iter([])

        result = await budget_tools.list_budgets(customer_id=CUSTOMER_ID)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["budgets"] == []

    async def test_list_budgets_with_recommendation(
        self, budget_tools, mock_googleads_service, make_budget_row
    ):
        row = make_budget_row(
            budget_id=99,
            has_recommended_budget=True,
            recommended_budget_amount_micros=6_000_000,
        )
        mock_googleads_service.search.return_value = iter([row])

        result = await budget_tools.list_budgets(customer_id=CUSTOMER_ID)

        assert result["success"] is True
        budget = result["budgets"][0]
        assert budget["has_recommended_budget"] is True
        assert budget["recommended_budget_amount_micros"] == 6_000_000
        assert budget["recommended_budget_amount"] == 6.0

    async def test_list_budgets_google_ads_exception(
        self, budget_tools, mock_googleads_service
    ):
        mock_googleads_service.search.side_effect = MockGoogleAdsException()

        result = await budget_tools.list_budgets(customer_id=CUSTOMER_ID)

        assert result["success"] is False
        assert result["error_type"] == "GoogleAdsException"


# ---------------------------------------------------------------------------
# remove_budget
# ---------------------------------------------------------------------------


class TestRemoveBudget:
    async def test_remove_budget_success(
        self, budget_tools, mock_googleads_service, mock_budget_service, make_budget_row
    ):
        row = make_budget_row(budget_id=int(BUDGET_ID), reference_count=0)
        mock_googleads_service.search.return_value = iter([row])

        resource_name = f"customers/{CUSTOMER_ID}/campaignBudgets/{BUDGET_ID}~removed"
        mock_budget_service.mutate_campaign_budgets.return_value = make_mutate_response(resource_name)

        result = await budget_tools.remove_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
        )

        assert result["success"] is True
        assert result["budget_id"] == BUDGET_ID
        assert "removed successfully" in result["message"]
        mock_budget_service.mutate_campaign_budgets.assert_called_once()

    async def test_remove_budget_not_found(
        self, budget_tools, mock_googleads_service
    ):
        mock_googleads_service.search.return_value = iter([])

        result = await budget_tools.remove_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
        )

        assert result["success"] is False
        assert result["error_type"] == "NotFound"
        assert BUDGET_ID in result["error"]

    async def test_remove_budget_still_referenced(
        self, budget_tools, mock_googleads_service, make_budget_row
    ):
        row = make_budget_row(budget_id=int(BUDGET_ID), reference_count=3)
        mock_googleads_service.search.return_value = iter([row])

        result = await budget_tools.remove_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
        )

        assert result["success"] is False
        assert result["error_type"] == "ValidationError"
        assert result["reference_count"] == 3
        assert "3" in result["error"]

    async def test_remove_budget_already_removed(
        self, budget_tools, mock_googleads_service, mock_budget_service, make_budget_row
    ):
        row = make_budget_row(budget_id=int(BUDGET_ID), reference_count=0)
        mock_googleads_service.search.return_value = iter([row])

        exc = MockGoogleAdsException(
            error_codes=["OPERATION_NOT_PERMITTED_FOR_REMOVED_RESOURCE"]
        )
        mock_budget_service.mutate_campaign_budgets.side_effect = exc

        result = await budget_tools.remove_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
        )

        assert result["success"] is True
        assert result.get("already_removed") is True
        assert BUDGET_ID in result["message"]

    async def test_remove_budget_google_ads_exception(
        self, budget_tools, mock_googleads_service, mock_budget_service, make_budget_row
    ):
        row = make_budget_row(budget_id=int(BUDGET_ID), reference_count=0)
        mock_googleads_service.search.return_value = iter([row])

        exc = MockGoogleAdsException(error_codes=["SOME_OTHER_ERROR"])
        mock_budget_service.mutate_campaign_budgets.side_effect = exc

        result = await budget_tools.remove_budget(
            customer_id=CUSTOMER_ID,
            budget_id=BUDGET_ID,
        )

        assert result["success"] is False
        assert result["error_type"] == "GoogleAdsException"
