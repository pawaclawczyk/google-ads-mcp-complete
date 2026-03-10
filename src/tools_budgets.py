"""Budget management tools for Google Ads API v21."""

from typing import Any, Dict, List, Optional
import structlog

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from .utils import currency_to_micros, micros_to_currency

logger = structlog.get_logger(__name__)


class BudgetTools:
    """Budget management tools."""
    
    def __init__(self, auth_manager, error_handler):
        self.auth_manager = auth_manager
        self.error_handler = error_handler
        
    async def create_budget(
        self,
        customer_id: str,
        name: str,
        amount_micros: Optional[int] = None,
        delivery_method: str = "STANDARD",
        period: str = "DAILY",
        total_amount_micros: Optional[int] = None,
        explicitly_shared: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Create a campaign budget (daily or campaign total)."""
        period_upper = period.upper()

        # Validate parameters per period type
        if period_upper == "CUSTOM_PERIOD":
            if total_amount_micros is None:
                return {
                    "success": False,
                    "error": "total_amount_micros is required when period=CUSTOM_PERIOD",
                    "error_type": "ValidationError",
                }
            if explicitly_shared is True:
                return {
                    "success": False,
                    "error": "explicitly_shared must be False (or omitted) for CUSTOM_PERIOD budgets",
                    "error_type": "ValidationError",
                }
            explicitly_shared = False
        else:  # DAILY
            if amount_micros is None:
                return {
                    "success": False,
                    "error": "amount_micros is required when period=DAILY",
                    "error_type": "ValidationError",
                }
            if explicitly_shared is None:
                explicitly_shared = True

        try:
            client = self.auth_manager.get_client(customer_id)
            budget_service = client.get_service("CampaignBudgetService")

            # Create budget operation
            budget_operation = client.get_type("CampaignBudgetOperation")
            budget = budget_operation.create

            # Set budget properties
            budget.name = name
            budget.explicitly_shared = explicitly_shared

            # Set period
            if period_upper == "CUSTOM_PERIOD":
                budget.period = client.enums.BudgetPeriodEnum.CUSTOM_PERIOD
                budget.total_amount_micros = total_amount_micros
            else:
                budget.period = client.enums.BudgetPeriodEnum.DAILY
                budget.amount_micros = amount_micros

            # Set delivery method
            if delivery_method.upper() == "ACCELERATED":
                budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.ACCELERATED
            else:
                budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD

            # Create the budget
            response = budget_service.mutate_campaign_budgets(
                customer_id=customer_id,
                operations=[budget_operation],
            )

            # Extract budget ID from response
            budget_resource_name = response.results[0].resource_name
            budget_id = budget_resource_name.split("/")[-1]

            logger.info(
                "Created campaign budget",
                customer_id=customer_id,
                budget_id=budget_id,
                name=name,
                period=period_upper,
            )

            result = {
                "success": True,
                "budget_id": budget_id,
                "budget_resource_name": budget_resource_name,
                "name": name,
                "period": period_upper,
                "delivery_method": delivery_method.upper(),
                "explicitly_shared": explicitly_shared,
            }
            if period_upper == "CUSTOM_PERIOD":
                result["total_amount"] = micros_to_currency(total_amount_micros)
            else:
                result["amount"] = micros_to_currency(amount_micros)
            return result

        except GoogleAdsException as e:
            logger.error(f"Failed to create budget: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "GoogleAdsException"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating budget: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "UnexpectedError"
            }
    
    async def update_budget(
        self,
        customer_id: str,
        budget_id: str,
        amount_micros: Optional[int] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update budget amount or settings."""
        try:
            client = self.auth_manager.get_client(customer_id)
            budget_service = client.get_service("CampaignBudgetService")
            
            # Create budget operation
            budget_operation = client.get_type("CampaignBudgetOperation")
            budget = budget_operation.update
            
            # Set resource name
            budget.resource_name = budget_service.campaign_budget_path(
                customer_id, budget_id
            )
            
            # Set update mask fields (API v21 compatible)
            from google.protobuf.field_mask_pb2 import FieldMask
            update_mask = FieldMask()
            paths = []
            
            if amount_micros is not None:
                budget.amount_micros = amount_micros
                paths.append("amount_micros")
                
            if name is not None:
                budget.name = name
                paths.append("name")
                
            update_mask.paths.extend(paths)
            budget_operation.update_mask = update_mask
            
            # Update the budget
            response = budget_service.mutate_campaign_budgets(
                customer_id=customer_id,
                operations=[budget_operation],
            )
            
            logger.info(
                f"Updated campaign budget",
                customer_id=customer_id,
                budget_id=budget_id,
                updated_fields=paths
            )
            
            return {
                "success": True,
                "budget_id": budget_id,
                "updated_fields": paths,
                "message": f"Successfully updated budget {budget_id}"
            }
            
        except GoogleAdsException as e:
            logger.error(f"Failed to update budget: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "GoogleAdsException"
            }
        except Exception as e:
            logger.error(f"Unexpected error updating budget: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "UnexpectedError"
            }
    
    async def list_budgets(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """List all budgets."""
        try:
            client = self.auth_manager.get_client(customer_id)
            googleads_service = client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    campaign_budget.id,
                    campaign_budget.name,
                    campaign_budget.amount_micros,
                    campaign_budget.delivery_method,
                    campaign_budget.status
                FROM campaign_budget
            """
            
            response = googleads_service.search(
                customer_id=customer_id, query=query
            )
            
            budgets = []
            for row in response:
                budgets.append({
                    "id": str(row.campaign_budget.id),
                    "name": str(row.campaign_budget.name),
                    "amount": micros_to_currency(row.campaign_budget.amount_micros),
                    "amount_micros": row.campaign_budget.amount_micros,
                    "delivery_method": str(row.campaign_budget.delivery_method.name),
                    "status": str(row.campaign_budget.status.name)
                })
            
            return {
                "success": True,
                "budgets": budgets,
                "count": len(budgets)
            }
            
        except GoogleAdsException as e:
            logger.error(f"Failed to list budgets: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "GoogleAdsException"
            }
        except Exception as e:
            logger.error(f"Unexpected error listing budgets: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "UnexpectedError"
            }

    async def remove_budget(
        self,
        customer_id: str,
        budget_id: str,
    ) -> Dict[str, Any]:
        """Remove a campaign budget. Fails if the budget is still referenced by any campaign."""
        try:
            client = self.auth_manager.get_client(customer_id)
            googleads_service = client.get_service("GoogleAdsService")

            # Pre-flight: check reference_count
            query = f"""
                SELECT campaign_budget.reference_count
                FROM campaign_budget
                WHERE campaign_budget.id = {budget_id}
            """
            response = googleads_service.search(customer_id=customer_id, query=query)
            rows = list(response)
            if not rows:
                return {
                    "success": False,
                    "error": f"Budget {budget_id} not found",
                    "error_type": "NotFound",
                }
            reference_count = rows[0].campaign_budget.reference_count
            if reference_count > 0:
                return {
                    "success": False,
                    "error": (
                        f"Budget {budget_id} is still referenced by {reference_count} "
                        "campaign(s). Unlink or remove those campaigns first."
                    ),
                    "error_type": "ValidationError",
                    "reference_count": reference_count,
                }

            # Remove the budget
            budget_service = client.get_service("CampaignBudgetService")
            budget_operation = client.get_type("CampaignBudgetOperation")
            budget_operation.remove = budget_service.campaign_budget_path(customer_id, budget_id)

            remove_response = budget_service.mutate_campaign_budgets(
                customer_id=customer_id,
                operations=[budget_operation],
            )

            resource_name = remove_response.results[0].resource_name
            logger.info(
                "Removed campaign budget",
                customer_id=customer_id,
                budget_id=budget_id,
            )
            return {
                "success": True,
                "budget_id": budget_id,
                "resource_name": resource_name,
                "message": f"Budget {budget_id} removed successfully",
            }

        except GoogleAdsException as e:
            for err in e.failure.errors:
                if "OPERATION_NOT_PERMITTED_FOR_REMOVED_RESOURCE" in str(err.error_code):
                    return {
                        "success": True,
                        "already_removed": True,
                        "message": f"Budget {budget_id} was already removed",
                    }
            logger.error(f"Failed to remove budget: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "GoogleAdsException",
            }
        except Exception as e:
            logger.error(f"Unexpected error removing budget: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "UnexpectedError",
            }
