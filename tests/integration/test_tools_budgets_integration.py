"""Integration tests for BudgetTools against a real Google Ads account.

These tests perform live CRUD operations and are skipped automatically when
TEST_CUSTOMER_ID is not set in the environment.

Run with:
    uv run pytest tests/integration -v -m integration
"""

import pytest


@pytest.mark.integration
async def test_create_list_remove_daily_budget(budget_tools, customer_id):
    """Full lifecycle for a DAILY budget: create → list (assert present) → remove."""
    # --- Create ---
    create_result = await budget_tools.create_budget(
        customer_id=customer_id,
        name="[TEST] Daily Budget - auto cleanup",
        amount_micros=1_000_000,  # $1.00
        period="DAILY",
        delivery_method="STANDARD",
    )
    assert create_result["success"] is True, create_result.get("error")
    budget_id = create_result["budget_id"]

    try:
        # --- List (assert present) ---
        list_result = await budget_tools.list_budgets(customer_id=customer_id)
        assert list_result["success"] is True
        ids = [b["id"] for b in list_result["budgets"]]
        assert budget_id in ids, f"Budget {budget_id} not found in list: {ids}"

    finally:
        # --- Remove (always attempt cleanup) ---
        remove_result = await budget_tools.remove_budget(
            customer_id=customer_id,
            budget_id=budget_id,
        )
        assert remove_result["success"] is True, remove_result.get("error")


@pytest.mark.integration
async def test_create_list_remove_custom_period_budget(budget_tools, customer_id):
    """Full lifecycle for a CUSTOM_PERIOD budget: create → list → remove."""
    # --- Create ---
    create_result = await budget_tools.create_budget(
        customer_id=customer_id,
        name="[TEST] Custom Period Budget - auto cleanup",
        total_amount_micros=10_000_000,  # $10.00
        period="CUSTOM_PERIOD",
        explicitly_shared=False,
    )
    assert create_result["success"] is True, create_result.get("error")
    budget_id = create_result["budget_id"]

    try:
        # --- List (assert present) ---
        list_result = await budget_tools.list_budgets(customer_id=customer_id)
        assert list_result["success"] is True
        ids = [b["id"] for b in list_result["budgets"]]
        assert budget_id in ids, f"Budget {budget_id} not found in list: {ids}"

    finally:
        # --- Remove (always attempt cleanup) ---
        remove_result = await budget_tools.remove_budget(
            customer_id=customer_id,
            budget_id=budget_id,
        )
        assert remove_result["success"] is True, remove_result.get("error")
