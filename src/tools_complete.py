"""Complete tools implementation combining all modules."""

import asyncio
from typing import Any, Dict, List, Optional
import base64
import structlog

from mcp.types import Tool
from google.ads.googleads.errors import GoogleAdsException

from .auth import GoogleAdsAuthManager
from .error_handler import ErrorHandler
from .tools_campaigns import CampaignTools
from .tools_reporting import ReportingTools
from .tools_ad_groups import AdGroupTools
from .tools_ads import AdTools
from .tools_keywords import KeywordTools
from .tools_budgets import BudgetTools
from .tools_assets import AssetTools
from .tools_extensions import ExtensionTools
from .tools_audiences import AudienceTools
from .tools_geography import GeographyTools
from .tools_bidding import BiddingTools
from .utils import currency_to_micros, micros_to_currency

logger = structlog.get_logger(__name__)


class GoogleAdsTools:
    """Complete implementation of all Google Ads API v20 tools."""
    
    def __init__(self, auth_manager: GoogleAdsAuthManager, error_handler: ErrorHandler):
        self.auth_manager = auth_manager
        self.error_handler = error_handler
        
        # Initialize tool modules
        self.campaign_tools = CampaignTools(auth_manager, error_handler)
        self.reporting_tools = ReportingTools(auth_manager, error_handler)
        self.ad_group_tools = AdGroupTools(auth_manager, error_handler)
        self.ad_tools = AdTools(auth_manager, error_handler)
        self.keyword_tools = KeywordTools(auth_manager, error_handler)
        self.budget_tools = BudgetTools(auth_manager, error_handler)
        self.asset_tools = AssetTools(auth_manager, error_handler)
        self.extension_tools = ExtensionTools(auth_manager, error_handler)
        self.audience_tools = AudienceTools(auth_manager, error_handler)
        self.geography_tools = GeographyTools(auth_manager, error_handler)
        self.bidding_tools = BiddingTools(auth_manager, error_handler)
        
        self._tools_registry = self._register_all_tools()
        
    def _register_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available tools from all modules."""
        tools = {}
        
        # Account Management
        tools.update(self._register_account_tools())
        
        # Campaign Management (from CampaignTools)
        tools.update(self._register_campaign_tools())
        
        # Reporting & Analytics (from ReportingTools)
        tools.update(self._register_reporting_tools())
        
        # Additional tool categories
        # Ad Group Management
        tools.update(self._register_ad_group_tools())
        
        # Ad Management
        tools.update(self._register_ad_tools())
        
        # Asset Management
        tools.update(self._register_asset_tools())
        
        # Budget Management
        tools.update(self._register_budget_tools())
        
        # Keyword Management
        tools.update(self._register_keyword_tools())
        
        # Extension Management
        tools.update(self._register_extension_tools())
        
        # Search Terms & Negative Keyword Intelligence
        tools.update(self._register_search_intelligence_tools())
        
        # Audience Management & Targeting
        tools.update(self._register_audience_tools())
        
        # Geographic Performance & Targeting
        tools.update(self._register_geography_tools())
        
        # Bidding Strategy & Bid Adjustments
        tools.update(self._register_bidding_tools())
        
        # # Advanced Features
        # tools.update(self._register_advanced_tools())
        
        return tools
        
    def _register_account_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register account management tools."""
        return {
            "list_accounts": {
                "description": "List all accessible Google Ads accounts, returning account IDs, names, currency codes, and time zones.",
                "handler": self.list_accounts,
                "parameters": {},
            },
            "get_account_info": {
                "description": "Get detailed information for a specific account including currency, time zone, manager status, test account flag, auto-tagging status, and optimization score.",
                "handler": self.get_account_info,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                },
            },
            "get_account_hierarchy": {
                "description": "Get the full manager→sub-account tree (up to 2 levels deep), returning each node's ID, name, manager flag, hierarchy level, time zone, and currency.",
                "handler": self.get_account_hierarchy,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                },
            },
        }
        
    def _register_campaign_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register campaign management tools."""
        return {
            "create_campaign": {
                "description": "Create a new campaign with a dedicated budget. Supported campaign_type values: SEARCH (default), DISPLAY, SHOPPING, VIDEO, PERFORMANCE_MAX, SMART, LOCAL. Currently uses Manual CPC bidding regardless of bidding_strategy parameter. SEARCH campaigns target Google Search + Search Network. EU political ad compliance field is set automatically to non-EU. Language targeting is applied when target_languages is provided; geo-targeting is not yet supported.",
                "handler": self.campaign_tools.create_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "budget_amount": {"type": "number", "required": True, "description": "Daily budget in USD (e.g., 50.0 = $50/day)"},
                    "campaign_type": {"type": "string", "default": "SEARCH"},
                    "bidding_strategy": {"type": "string", "default": "MAXIMIZE_CLICKS", "description": "Ignored — campaign always uses Manual CPC (bidding strategy upgrade is TODO)"},
                    "start_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "end_date": {"type": "string", "description": "Date in YYYY-MM-DD format; omit for no end date"},
                    "target_locations": {"type": "array", "description": "Array of location names e.g. ['US', 'CA'] — currently NOT applied (geo-targeting is disabled)"},
                    "target_languages": {"type": "array", "description": "Array of language names e.g. ['English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Dutch', 'Russian', 'Japanese', 'Chinese']"},
                },
            },
            "update_campaign": {
                "description": "Update campaign fields using field-mask based update. Updatable fields: name, status (ENABLED/PAUSED/REMOVED), start_date, end_date, bidding_strategy (pass a portfolio bidding strategy resource name to assign it).",
                "handler": self.campaign_tools.update_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "name": {"type": "string"},
                    "status": {"type": "string", "description": "New status: ENABLED, PAUSED, or REMOVED"},
                    "start_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "end_date": {"type": "string", "description": "Date in YYYY-MM-DD format; omit for no end date"},
                    "bidding_strategy": {"type": "string", "description": "Full resource name of a portfolio bidding strategy: customers/{id}/biddingStrategies/{id}"},
                },
            },
            "pause_campaign": {
                "description": "Pause a running campaign",
                "handler": self.campaign_tools.pause_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                },
            },
            "resume_campaign": {
                "description": "Resume a paused campaign",
                "handler": self.campaign_tools.resume_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                },
            },
            "list_campaigns": {
                "description": "List all campaigns with optional status and campaign_type filters. Returns campaign ID, name, status, and advertising channel type. Defaults to excluding REMOVED campaigns when no status filter is provided.",
                "handler": self.campaign_tools.list_campaigns,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "status": {"type": "string", "description": "Filter by status: ENABLED, PAUSED, or REMOVED"},
                    "campaign_type": {"type": "string", "description": "Filter by type: SEARCH, DISPLAY, SHOPPING, VIDEO, PERFORMANCE_MAX, SMART, or LOCAL"},
                },
            },
            "get_campaign": {
                "description": "Get detailed information for a single campaign including type, subtype, bidding strategy, budget (amount + delivery method), start/end dates, network settings, optimization score, and 30-day performance metrics (clicks, impressions, cost, conversions, CTR, average_cpc, conversion_rate).",
                "handler": self.campaign_tools.get_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                },
            },
            "delete_campaign": {
                "description": "Delete a campaign permanently",
                "handler": self.campaign_tools.delete_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                },
            },
            "copy_campaign": {
                "description": "Copy an existing campaign's settings (type, network, bidding, targeting) under a new name. Optionally override the budget amount; if omitted, defaults to $50.00. Returns the new campaign ID.",
                "handler": self.campaign_tools.copy_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "source_campaign_id": {"type": "string", "required": True},
                    "new_name": {"type": "string", "required": True},
                    "budget_amount": {"type": "number", "description": "Override daily budget in USD; if omitted, defaults to $50.00"},
                },
            },
            "create_ad_schedule": {
                "description": "Create dayparting schedules for a campaign. Each schedule in the schedules array specifies a day of week, start hour, end hour, and an optional bid modifier to increase or decrease bids during that time block.",
                "handler": self.campaign_tools.create_ad_schedule,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "schedules": {"type": "array", "required": True, "description": "Array of schedule objects: [{\"day_of_week\": \"MONDAY\", \"start_hour\": 9, \"end_hour\": 17, \"bid_modifier\": 1.2}]. day_of_week: MONDAY–SUNDAY; hours: 0–23; bid_modifier optional (e.g., 1.2 = +20%)"},
                },
            },
            "get_campaign_overview": {
                "description": "Get comprehensive high-level campaign overview showing keywords, extensions, scheduling, audiences, performance, and optimization score",
                "handler": self.campaign_tools.get_campaign_overview,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
        }

    def _register_ad_group_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register ad group management tools."""
        return {
            "create_ad_group": {
                "description": "Create a new ad group in a campaign. Default CPC bid is $2.00 (2,000,000 micros). Always creates SEARCH_STANDARD type (ad group type is not configurable via this tool). Status is ENABLED on creation.",
                "handler": self.ad_group_tools.create_ad_group,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "cpc_bid_micros": {"type": "number", "description": "CPC bid in micros ($1 = 1,000,000); default is 2,000,000 ($2.00)"},
                },
            },
            "update_ad_group": {
                "description": "Update an ad group's name, CPC bid (cpc_bid_micros), or status (ENABLED or PAUSED) using field-mask based update.",
                "handler": self.ad_group_tools.update_ad_group,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "name": {"type": "string"},
                    "status": {"type": "string", "description": "New status: ENABLED or PAUSED"},
                    "cpc_bid_micros": {"type": "number", "description": "New CPC bid in micros ($1 = 1,000,000)"},
                },
            },
            "list_ad_groups": {
                "description": "List ad groups across the account, optionally filtered by campaign_id. Returns each group's ID, name, status, type (SEARCH_STANDARD/DISPLAY_STANDARD), CPC bid, and parent campaign info.",
                "handler": self.ad_group_tools.list_ad_groups,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "description": "Optional — filter to a specific campaign; omit to list all"},
                },
            },
        }

    def _register_ad_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register ad management tools."""
        return {
            "create_responsive_search_ad": {
                "description": "Create a responsive search ad. Accepts 3–15 headlines and 2–4 descriptions; inputs are silently capped at the API maximums (15 headlines, 4 descriptions). Optional path1/path2 add display URL paths appended to the domain. Returns ad ID, counts, and status.",
                "handler": self.ad_tools.create_responsive_search_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "headlines": {"type": "array", "required": True, "description": "Array of headline strings; min 3, max 15 (extras are silently dropped)"},
                    "descriptions": {"type": "array", "required": True, "description": "Array of description strings; min 2, max 4 (extras are silently dropped)"},
                    "final_urls": {"type": "array", "required": True, "description": "Array of landing page URLs; at least one required"},
                    "path1": {"type": "string", "description": "Optional display URL path segment appended after the domain (max 15 chars)"},
                    "path2": {"type": "string", "description": "Optional second display URL path segment; requires path1 to be set (max 15 chars)"},
                },
            },
            "create_expanded_text_ad": {
                "description": "Create an expanded text ad (legacy/deprecated format; prefer create_responsive_search_ad). Accepts 2–3 headlines (headline1 and headline2 required, headline3 optional) and 1–2 descriptions.",
                "handler": self.ad_tools.create_expanded_text_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "headline1": {"type": "string", "required": True, "description": "Headline text; max 30 chars"},
                    "headline2": {"type": "string", "required": True, "description": "Headline text; max 30 chars"},
                    "headline3": {"type": "string", "description": "Optional third headline; max 30 chars"},
                    "description1": {"type": "string", "required": True, "description": "Description text; max 80 chars"},
                    "description2": {"type": "string", "description": "Optional second description; max 80 chars"},
                    "final_urls": {"type": "array", "required": True, "description": "Array of landing page URLs; at least one required"},
                },
            },
            "list_ads": {
                "description": "List ads with optional ad_group_id, campaign_id, and status filters. Returns ad type (RESPONSIVE_SEARCH_AD/EXPANDED_TEXT_AD), headlines, descriptions, final URLs, and review status per ad.",
                "handler": self.ad_tools.list_ads,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "description": "Optional filter; omit to list across all ad groups"},
                    "campaign_id": {"type": "string", "description": "Optional filter; omit to list across all campaigns"},
                    "status": {"type": "string", "description": "Optional filter: ENABLED or PAUSED"},
                },
            },
            "update_ad": {
                "description": "Update an existing ad",
                "handler": self.ad_tools.update_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "ad_id": {"type": "string", "required": True},
                    "headlines": {"type": "array", "description": "Replacement headlines (RSA only); max 15"},
                    "descriptions": {"type": "array", "description": "Replacement descriptions (RSA only); max 4"},
                    "final_urls": {"type": "array", "description": "Replacement landing page URLs"},
                    "status": {"type": "string", "description": "New status: ENABLED or PAUSED"},
                },
            },
            "pause_ad": {
                "description": "Pause a specific ad",
                "handler": self.ad_tools.pause_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "ad_id": {"type": "string", "required": True},
                },
            },
            "enable_ad": {
                "description": "Enable a specific ad",
                "handler": self.ad_tools.enable_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "ad_id": {"type": "string", "required": True},
                },
            },
            "delete_ad": {
                "description": "Delete a specific ad",
                "handler": self.ad_tools.delete_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "ad_id": {"type": "string", "required": True},
                },
            },
            "compare_ad_performance": {
                "description": "Compare multiple ads side-by-side within an ad group, computing a composite efficiency score (CTR×10 + conversion_rate×5 + ROAS×2 + cost_efficiency). Returns ads sorted by efficiency score with best/worst performers identified and actionable insights.",
                "handler": self.ad_tools.compare_ad_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_ids": {"type": "array", "required": True, "description": "Array of ad ID strings to compare (must all be in the same ad_group_id)"},
                    "ad_group_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
            "get_ad_group_performance_ranking": {
                "description": "Rank all ads in an ad group by performance. sort_by options: efficiency_score (default), ctr, conversions, roas, cost. Returns each ad's rank, CTR, ROAS, conversion rate, cost-per-conversion, and ad strength, identifying top and bottom performers.",
                "handler": self.ad_tools.get_ad_group_performance_ranking,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                    "sort_by": {"type": "string", "default": "efficiency_score", "description": "Sort metric: efficiency_score (default), ctr, conversions, roas, or cost_per_conversion"},
                },
            },
            "identify_optimization_opportunities": {
                "description": "Identify ads to pause, optimize, or scale based on performance. Only ads with ≥ min_clicks clicks qualify for analysis. Returns three action tiers: scale (top performers), optimize (mediocre efficiency), pause (poor/wasteful). Use campaign_id OR ad_group_id to scope; both are optional for account-wide analysis.",
                "handler": self.ad_tools.identify_optimization_opportunities,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "description": "Optional scope — use ad_group_id OR campaign_id (or neither for account-wide)"},
                    "campaign_id": {"type": "string", "description": "Optional scope — use campaign_id OR ad_group_id (or neither for account-wide)"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                    "min_clicks": {"type": "number", "default": 10, "description": "Minimum clicks an ad must have to be included in analysis (default 10)"},
                },
            },
            "calculate_roas_by_ad": {
                "description": "Calculate ROAS for each ad, filtered to ads with spend ≥ min_cost (default $5). Returns ROAS, conversion value, cost, and profitability classification per ad. Use campaign_id OR ad_group_id to scope; both are optional.",
                "handler": self.ad_tools.calculate_roas_by_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "description": "Optional scope — use ad_group_id OR campaign_id (or neither for account-wide)"},
                    "campaign_id": {"type": "string", "description": "Optional scope — use campaign_id OR ad_group_id (or neither for account-wide)"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                    "min_cost": {"type": "number", "default": 5.0, "description": "Minimum spend in USD to include an ad (default $5.00)"},
                },
            },
            "analyze_ad_strength_trends": {
                "description": "Analyze ad strength ratings (POOR/AVERAGE/GOOD/EXCELLENT) alongside performance metrics (clicks, impressions, CTR) for ads in an ad group. current_date_range is compared against comparison_date_range to surface trends. Returns strength summary by rating, review/approval status, and concrete improvement recommendations.",
                "handler": self.ad_tools.analyze_ad_strength_trends,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "current_date_range": {"type": "string", "default": "LAST_7_DAYS", "description": "Recent period to analyze; Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                    "comparison_date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Older comparison period; Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
        }
        
    def _register_asset_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register asset management tools."""
        return {
            "upload_image_asset": {
                "description": "Upload an image as a reusable account-level asset. image_data accepts base64-encoded data, a data URL (data:image/...;base64,<data>), or a local file path — format is auto-detected. Returns asset ID and size in bytes.",
                "handler": self.asset_tools.upload_image_asset,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "image_data": {"type": "string", "required": True, "description": "Image as base64-encoded string, data URL (data:image/png;base64,...), or local file path — format auto-detected"},
                    "name": {"type": "string", "required": True, "description": "Human-readable name for the asset (for identification in the asset library)"},
                },
            },
            "upload_text_asset": {
                "description": "Create a reusable text asset with a given name and text content. Returns asset ID and resource name.",
                "handler": self.asset_tools.upload_text_asset,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "text": {"type": "string", "required": True, "description": "Text content for the asset"},
                    "name": {"type": "string", "required": True, "description": "Human-readable name for the asset"},
                },
            },
            "list_assets": {
                "description": "List all assets in the account. Optional asset_type filter: IMAGE, TEXT, SITELINK, CALLOUT, STRUCTURED_SNIPPET, etc.",
                "handler": self.asset_tools.list_assets,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "asset_type": {"type": "string", "description": "Optional filter: IMAGE, TEXT, SITELINK, CALLOUT, STRUCTURED_SNIPPET"},
                },
            },
        }
        
    def _register_budget_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register budget management tools."""
        return {
            "create_budget": {
                "description": (
                    "Create a campaign budget. Two modes are supported:\n"
                    "• DAILY (default): average daily budget shared across campaigns. "
                    "Requires amount_micros (e.g. 10000000 = $10/day). "
                    "explicitly_shared defaults to True so it can be reused across campaigns.\n"
                    "• CUSTOM_PERIOD: lifetime (campaign total) budget for campaigns with fixed "
                    "start and end dates (Search, Shopping, and Performance Max only). "
                    "Requires total_amount_micros. explicitly_shared is always False and cannot "
                    "be overridden.\n"
                    "delivery_method: STANDARD (default, paces spend evenly) or ACCELERATED."
                ),
                "handler": self.budget_tools.create_budget,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "period": {
                        "type": "string",
                        "default": "DAILY",
                        "description": "DAILY (average daily budget) or CUSTOM_PERIOD (campaign total / lifetime budget).",
                    },
                    "amount_micros": {
                        "type": "number",
                        "description": "Daily budget in micros ($1 = 1,000,000). Required when period=DAILY.",
                    },
                    "total_amount_micros": {
                        "type": "number",
                        "description": "Total lifetime budget in micros. Required when period=CUSTOM_PERIOD.",
                    },
                    "delivery_method": {
                        "type": "string",
                        "default": "STANDARD",
                        "description": "STANDARD (pace evenly throughout day) or ACCELERATED (spend as fast as possible).",
                    },
                    "explicitly_shared": {
                        "type": "boolean",
                        "description": (
                            "Whether the budget can be shared across multiple campaigns. "
                            "Defaults to True for DAILY budgets. "
                            "Must be False (or omitted) for CUSTOM_PERIOD budgets."
                        ),
                    },
                },
            },
            "update_budget": {
                "description": (
                    "Update a campaign budget's amount and/or settings using field-mask based update. "
                    "At least one field must be provided. amount_micros (DAILY) and total_amount_micros "
                    "(CUSTOM_PERIOD) are mutually exclusive. explicitly_shared can only be set to True "
                    "(a shared budget can never become non-shared)."
                ),
                "handler": self.budget_tools.update_budget,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "budget_id": {"type": "string", "required": True},
                    "amount_micros": {"type": "number", "description": "New daily budget in micros ($1 = 1,000,000). For DAILY budgets only; mutually exclusive with total_amount_micros."},
                    "total_amount_micros": {"type": "number", "description": "New lifetime budget in micros. For CUSTOM_PERIOD budgets only; mutually exclusive with amount_micros."},
                    "name": {"type": "string", "description": "New budget name."},
                    "delivery_method": {"type": "string", "description": "STANDARD (pace evenly) or ACCELERATED (spend as fast as possible)."},
                    "explicitly_shared": {"type": "boolean", "description": "Set to True to make the budget explicitly shared across campaigns. Cannot be set to False (shared budgets can never become non-shared)."},
                },
            },
            "list_budgets": {
                "description": "List all campaign budgets in the account, including budget ID, name, amount, delivery method (STANDARD/ACCELERATED), and campaign association status.",
                "handler": self.budget_tools.list_budgets,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                },
            },
            "remove_budget": {
                "description": (
                    "Remove a campaign budget permanently. The budget must have no campaigns "
                    "referencing it (reference_count = 0); if any ENABLED or PAUSED campaigns "
                    "still use the budget the call returns a ValidationError with the reference "
                    "count. Non-shared budgets attached to a campaign are automatically removed "
                    "when that campaign is deleted — use this tool only for budgets that are "
                    "already unlinked."
                ),
                "handler": self.budget_tools.remove_budget,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "budget_id": {"type": "string", "required": True, "description": "Numeric budget ID to remove"},
                },
            },
        }

    def _register_keyword_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register keyword management tools."""
        return {
            "add_keywords": {
                "description": "Add positive keywords to an ad group. SYNTAX: keywords=[{'text': 'buy shoes', 'match_type': 'BROAD', 'cpc_bid_micros': 2000000}, ...]. match_type defaults to BROAD if omitted; supported values: BROAD, PHRASE, EXACT. cpc_bid_micros is optional per keyword.",
                "handler": self.keyword_tools.add_keywords,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keywords": {"type": "array", "required": True, "description": "Array of keyword objects: [{\"text\": \"buy shoes\", \"match_type\": \"BROAD\", \"cpc_bid_micros\": 2000000}]. match_type: BROAD (default), PHRASE, EXACT. cpc_bid_micros optional."},
                },
            },
            "add_negative_keywords": {
                "description": "Add negative keywords at campaign or ad group level. SYNTAX: keywords=['free','cheap','demo'] as array of strings. Use EITHER campaign_id (campaign-level) OR ad_group_id (ad group-level), not both — tool raises an error if neither is provided. All negatives are added as BROAD match. Tool automatically creates KeywordInfo protobuf objects.",
                "handler": self.keyword_tools.add_negative_keywords,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "keywords": {"type": "array", "required": True, "description": "Array of negative keyword strings, e.g. ['free', 'cheap', 'demo']"},
                    "campaign_id": {"type": "string", "description": "Campaign-level negatives — use campaign_id OR ad_group_id, not both"},
                    "ad_group_id": {"type": "string", "description": "Ad group-level negatives — use ad_group_id OR campaign_id, not both"},
                },
            },
            "list_keywords": {
                "description": "List keywords with 30-day performance data. Optional ad_group_id and/or campaign_id filters. Returns text, match type, status, negative flag, CPC bid, and click/impression/cost/conversion metrics per keyword.",
                "handler": self.keyword_tools.list_keywords,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "description": "Optional filter; omit to list across all groups"},
                    "campaign_id": {"type": "string", "description": "Optional filter; omit to list across all campaigns"},
                },
            },
            "update_keyword_bid": {
                "description": "Update the CPC bid for a specific keyword",
                "handler": self.keyword_tools.update_keyword_bid,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keyword_id": {"type": "string", "required": True},
                    "cpc_bid_micros": {"type": "number", "required": True, "description": "New CPC bid in micros ($1 = 1,000,000; e.g., 1500000 = $1.50)"},
                },
            },
            "delete_keyword": {
                "description": "Delete a specific keyword",
                "handler": self.keyword_tools.delete_keyword,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keyword_id": {"type": "string", "required": True},
                },
            },
            "pause_keyword": {
                "description": "Pause a specific keyword",
                "handler": self.keyword_tools.pause_keyword,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keyword_id": {"type": "string", "required": True},
                },
            },
            "enable_keyword": {
                "description": "Enable a paused keyword",
                "handler": self.keyword_tools.enable_keyword,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keyword_id": {"type": "string", "required": True},
                },
            },
            "get_keyword_performance": {
                "description": "Get keyword performance including quality score (1–10), CTR, avg CPC, conversions, and cost, sorted by clicks descending. Optional ad_group_id filter. Uses keyword_view which includes impression-share data.",
                "handler": self.keyword_tools.get_keyword_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "description": "Optional filter; omit for account-wide keyword performance"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
        }

    def _register_extension_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register extension management tools."""
        return {
            "create_sitelink_extensions": {
                "description": "Create sitelink extensions for a campaign using a two-step process: creates sitelink assets then associates them with the campaign. description1 defaults to the sitelink text if omitted; description2 defaults to 'Learn more'. SYNTAX: sitelinks=[{'text':'Features','url':'https://site.com/features','description1':'Optional desc','description2':'Optional desc2'}]",
                "handler": self.extension_tools.create_sitelink_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "sitelinks": {"type": "array", "required": True, "description": "Array of objects with 'text', 'url', optional 'description1', 'description2'. description1 defaults to link text; description2 defaults to 'Learn more'"},
                },
            },
            "create_callout_extensions": {
                "description": "Create callout text extensions for a campaign using a two-step process: creates callout assets then associates with the campaign. callouts is an array of short text strings (e.g., ['Free Shipping', '24/7 Support']).",
                "handler": self.extension_tools.create_callout_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "callouts": {"type": "array", "required": True, "description": "Array of callout text strings (e.g., ['Free Shipping', '24/7 Support', 'Money-Back Guarantee'])"},
                },
            },
            "create_structured_snippet_extensions": {
                "description": "Create structured snippet extensions for a campaign using a two-step process (asset creation + campaign association). SERVICES and FEATURES header values are mapped to SERVICE_CATALOG. Values list is padded to at least 3 items if fewer are provided. Each value is silently truncated to 25 characters. SYNTAX: structured_snippets=[{'header':'SERVICE_CATALOG','values':['Web Design','SEO','PPC']}]. Valid headers: AMENITIES, BRANDS, COURSES, DESTINATIONS, MODELS, SERVICE_CATALOG, SERVICES, FEATURES (→SERVICE_CATALOG), STYLES, TYPES.",
                "handler": self.extension_tools.create_structured_snippet_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "structured_snippets": {"type": "array", "required": True, "description": "Array of objects with 'header' (predefined Google value) and 'values' (array of strings)"},
                },
            },
            "create_call_extensions": {
                "description": "Create a call extension for a campaign using the legacy ExtensionFeedItem API. Call tracking is enabled by default. country_code defaults to 'US'. Note: call_only is accepted but currently has no effect.",
                "handler": self.extension_tools.create_call_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "phone_number": {"type": "string", "required": True, "description": "Phone number to display; use your country's standard format (e.g., '1-800-555-1234' for US)"},
                    "country_code": {"type": "string", "default": "US", "description": "ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'AU'); default 'US'"},
                    "call_only": {"type": "boolean", "default": False, "description": "If true, ad shows only the phone number with no website link; default false"},
                },
            },
            "list_extensions": {
                "description": "List extensions for a campaign or the entire account. Optional extension_type filter: SITELINK, CALLOUT, STRUCTURED_SNIPPET, CALL. Returns extension-type-specific data (link text, URLs, callout text, phone numbers, etc.).",
                "handler": self.extension_tools.list_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "description": "Optional — filter to a specific campaign; omit for all account extensions"},
                    "extension_type": {"type": "string", "description": "Optional filter: SITELINK, CALLOUT, STRUCTURED_SNIPPET, or CALL"},
                },
            },
            "delete_extension": {
                "description": "Delete a campaign-asset link (extension) by its full campaign-asset resource name. The resource name must use the campaignAssets/ format — a plain asset path or numeric ID will fail.",
                "handler": self.extension_tools.delete_extension,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "extension_id": {"type": "string", "required": True, "description": "Full campaign-asset resource name (e.g., customers/{cid}/campaignAssets/{campaign_id}~{asset_id}~{field_type})"},
                },
            },
        }
        
    def _register_reporting_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register reporting and analytics tools."""
        return {
            "get_campaign_performance": {
                "description": "Get campaign performance metrics (clicks, impressions, cost, conversions, CTR, avg CPC) for a date range. Optional campaign_id to scope to a single campaign; optional metrics array to select specific fields.",
                "handler": self.reporting_tools.get_campaign_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "description": "Optional — filter to one campaign; omit for all campaigns"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                    "metrics": {"type": "array", "description": "Optional array of metric field names to return; omit for all default metrics"},
                },
            },
            "get_ad_group_performance": {
                "description": "Get ad group performance metrics (clicks, impressions, cost, conversions, CTR) for a date range. Optional ad_group_id to scope to a single group.",
                "handler": self.reporting_tools.get_ad_group_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "description": "Optional — filter to one ad group; omit for all groups"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
            "get_keyword_performance": {
                "description": "Get keyword-level performance metrics (clicks, impressions, cost, conversions, CTR) from the reporting view for a date range. Optional ad_group_id filter. For quality scores and detailed keyword data, use the keyword_tools.get_keyword_performance instead.",
                "handler": self.reporting_tools.get_keyword_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "description": "Optional — filter to one ad group; omit for all groups"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
            # "run_gaql_query": {
            #     "description": "Run custom GAQL queries",
            #     "handler": self.reporting_tools.run_gaql_query,
            #     "parameters": {
            #         "customer_id": {"type": "string", "required": True},
            #         "query": {"type": "string", "required": True},
            #     },
            # },
            "get_search_terms_report": {
                "description": "Get the raw search terms report showing which queries triggered your ads, with clicks, impressions, cost, and conversions per term. Optional campaign_id and/or ad_group_id filters. Defaults to LAST_7_DAYS.",
                "handler": self.reporting_tools.get_search_terms_report,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "description": "Optional scope filter"},
                    "ad_group_id": {"type": "string", "description": "Optional scope filter"},
                    "date_range": {"type": "string", "default": "LAST_7_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
        }
        
    def _register_advanced_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register advanced feature tools."""
        return {
            "get_recommendations": {
                "description": "Get optimization recommendations",
                "handler": self.get_recommendations,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                },
            },
            "apply_recommendation": {
                "description": "Apply a specific recommendation",
                "handler": self.apply_recommendation,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "recommendation_id": {"type": "string", "required": True},
                },
            },
            "get_change_history": {
                "description": "Get account change history",
                "handler": self.get_change_history,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_7_DAYS"},
                },
            },
        }
        
    def get_all_tools(self) -> List[Tool]:
        """Get all tools in MCP format."""
        tools = []
        for name, config in self._tools_registry.items():
            # Extract required parameters
            required_params = []
            properties = {}
            
            for param_name, param_config in config["parameters"].items():
                # Create property schema without the 'required' field
                prop_schema = {k: v for k, v in param_config.items() if k != "required"}
                properties[param_name] = prop_schema
                
                # Add to required list if marked as required
                if param_config.get("required", False):
                    required_params.append(param_name)
            
            tool = Tool(
                name=name,
                description=config["description"],
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required_params,
                },
            )
            tools.append(tool)
        return tools
        
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name."""
        if name not in self._tools_registry:
            raise ValueError(f"Unknown tool: {name}")
            
        tool_config = self._tools_registry[name]
        handler = tool_config["handler"]
        
        # Validate required parameters
        for param, config in tool_config["parameters"].items():
            if config.get("required", False) and param not in arguments:
                raise ValueError(f"Missing required parameter: {param}")
                
        # Execute the handler
        return await handler(**arguments)
        
    # Account Management Methods
    
    async def list_accounts(self) -> Dict[str, Any]:
        """List all accessible Google Ads accounts."""
        try:
            customers = self.auth_manager.get_accessible_customers()
            return {
                "success": True,
                "accounts": customers,
                "count": len(customers),
            }
        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            raise
            
    async def get_account_info(self, customer_id: str) -> Dict[str, Any]:
        """Get detailed account information."""
        try:
            client = self.auth_manager.get_client(customer_id)
            googleads_service = client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone,
                    customer.auto_tagging_enabled,
                    customer.manager,
                    customer.test_account,
                    customer.optimization_score,
                    customer.optimization_score_weight
                FROM customer
                LIMIT 1
            """
            
            response = googleads_service.search(
                customer_id=customer_id,
                query=query,
            )
            
            for row in response:
                return {
                    "success": True,
                    "account": {
                        "id": str(row.customer.id),
                        "name": row.customer.descriptive_name,
                        "currency_code": row.customer.currency_code,
                        "time_zone": row.customer.time_zone,
                        "auto_tagging_enabled": row.customer.auto_tagging_enabled,
                        "is_manager": row.customer.manager,
                        "is_test_account": row.customer.test_account,
                        "optimization_score": row.customer.optimization_score,
                        "optimization_score_weight": row.customer.optimization_score_weight,
                    },
                }
                
            return {"success": False, "error": "Account not found"}
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
            
    async def get_account_hierarchy(self, customer_id: str) -> Dict[str, Any]:
        """Get the account hierarchy tree."""
        try:
            client = self.auth_manager.get_client(customer_id)
            googleads_service = client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    customer_client.id,
                    customer_client.descriptive_name,
                    customer_client.manager,
                    customer_client.level,
                    customer_client.time_zone,
                    customer_client.currency_code
                FROM customer_client
                WHERE customer_client.level <= 2
            """
            
            response = googleads_service.search(
                customer_id=customer_id,
                query=query,
            )
            
            hierarchy = []
            for row in response:
                hierarchy.append({
                    "id": str(row.customer_client.id),
                    "name": row.customer_client.descriptive_name,
                    "is_manager": row.customer_client.manager,
                    "level": row.customer_client.level,
                    "time_zone": row.customer_client.time_zone,
                    "currency_code": row.customer_client.currency_code,
                })
                
            return {
                "success": True,
                "hierarchy": hierarchy,
                "count": len(hierarchy),
            }
            
        except Exception as e:
            logger.error(f"Failed to get account hierarchy: {e}")
            raise
    
    def _register_search_intelligence_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register search terms analysis and negative keyword intelligence tools."""
        return {
            "auto_suggest_negative_keywords": {
                "description": "Analyze wasteful search terms (spend ≥ min_cost with zero conversions) and suggest negative keywords using pattern analysis: single words appearing in 3+ wasteful terms and phrases appearing in 2+ wasteful terms are flagged. Returns ranked suggestions with estimated waste savings. Optional campaign_id or ad_group_id to scope analysis.",
                "handler": self.keyword_tools.auto_suggest_negative_keywords,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "description": "Optional scope — omit for account-wide; can use with or independently of ad_group_id"},
                    "ad_group_id": {"type": "string", "description": "Optional scope — omit for account-wide; can use with or independently of campaign_id"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                    "min_cost": {"type": "number", "default": 5.0, "description": "Minimum USD spend a term must have (no conversions) to be flagged as wasteful (default $5.00)"},
                    "max_suggestions": {"type": "number", "default": 50, "description": "Maximum number of negative keyword suggestions to return (default 50)"},
                },
            },
            "get_search_terms_insights": {
                "description": "Categorize search terms (with ≥ min_impressions impressions) into three groups: high performers (ROAS ≥ 2 or 2+ conversions under $50), expansion opportunities (unmatched terms with conversions, status=NONE), and wasteful terms (zero conversions, cost ≥ $5). Returns counts, metrics per term, and actionable recommendations for each category.",
                "handler": self.keyword_tools.get_search_terms_insights,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "description": "Optional scope filter"},
                    "ad_group_id": {"type": "string", "description": "Optional scope filter"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                    "min_impressions": {"type": "number", "default": 5, "description": "Minimum impressions a search term must have to be included in analysis (default 5)"},
                },
            },
        }
    
    def _register_audience_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register audience management and targeting tools."""
        return {
            "create_custom_audience": {
                "description": "Create a custom audience (user list). WEBSITE_VISITORS: rule-based list matching URL patterns — rules dict accepts 'url_contains', 'url_equals', or 'domain'. CUSTOMER_MATCH: CRM-based list for email/phone upload (CONTACT_INFO key type). Default membership_life_span is 540 days. Status is OPEN on creation.",
                "handler": self.audience_tools.create_custom_audience,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "audience_type": {"type": "string", "required": True, "description": "WEBSITE_VISITORS (rule-based URL matching) or CUSTOMER_MATCH (CRM-based email/phone upload)"},
                    "rules": {"type": "object", "required": True, "description": "Rules config — for WEBSITE_VISITORS: {\"url_contains\": \"value\"} or {\"url_equals\": \"/path\"} or {\"domain\": \"example.com\"}; for CUSTOMER_MATCH: {} (data uploaded separately)"},
                    "description": {"type": "string", "description": "Optional human-readable description; defaults to 'Custom audience: {name}'"},
                },
            },
            "add_audience_targeting": {
                "description": "Add audience targeting to an ad group. SYNTAX: audience_id can be just ID ('375' for user interests, '9088079237' for user lists) or full resource name ('customers/123/userLists/456'). Tool auto-detects type: 8+ digits = user list, shorter = user interest. targeting_mode: TARGETING (restrict traffic to this audience) or OBSERVATION (collect data without restricting reach). bid_modifier: optional multiplier, e.g. 1.2 for +20%.",
                "handler": self.audience_tools.add_audience_targeting,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "audience_id": {"type": "string", "required": True, "description": "User interest ID ('375'), user list ID ('9088079237'), or full resource name ('customers/123/userLists/456')"},
                    "targeting_mode": {"type": "string", "default": "TARGETING", "description": "TARGETING or OBSERVATION"},
                    "bid_modifier": {"type": "number", "description": "Bid adjustment, e.g. 1.2 for +20%"},
                },
            },
            "list_audiences": {
                "description": "List user lists in the account. Optional audience_type filter. Returns list name, type (RULE_BASED, CRM_BASED, SIMILAR), membership life span, size estimates, and status (OPEN/CLOSED).",
                "handler": self.audience_tools.list_audiences,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "audience_type": {"type": "string", "description": "Optional filter: USER_LIST, USER_INTEREST, RULE_BASED, CRM_BASED, or SIMILAR"},
                },
            },
            "get_audience_performance": {
                "description": "Get ROAS, cost-per-conversion, CTR, clicks, and impressions for audience targeting criteria. Includes benchmark comparison across audiences. Optional audience_id and/or campaign_id filters to scope results.",
                "handler": self.audience_tools.get_audience_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "audience_id": {"type": "string", "description": "Optional — filter to a specific audience ID; omit to get all audiences"},
                    "campaign_id": {"type": "string", "description": "Optional — filter to a specific campaign; omit for account-wide data"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
        }

    def _register_geography_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register geographic performance and targeting tools."""
        return {
            "get_location_performance": {
                "description": "Get performance by geographic location sorted by spend, including ROAS, cost-per-conversion, conversion rate, CTR, and avg CPC per location. Optional campaign_id filter. location_type: COUNTRY_AND_REGION (default) or other geo types. Returns optimization recommendations comparing each location against account averages.",
                "handler": self.geography_tools.get_location_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "description": "Optional — filter to a specific campaign; omit for account-wide data"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                    "location_type": {"type": "string", "default": "COUNTRY_AND_REGION", "description": "Geographic granularity: COUNTRY_AND_REGION (default), CITY, or STATE"},
                },
            },
            "optimize_geographic_targeting": {
                "description": "Analyze geographic performance for a campaign and return three action tiers: bid increases for top-performing locations (above-average ROAS), exclusion candidates (ROAS < poor_roas_threshold and spend ≥ min_cost_threshold), and bid adjustment suggestions for mid-tier locations. Returns potential waste savings estimate.",
                "handler": self.geography_tools.optimize_geographic_targeting,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                    "min_cost_threshold": {"type": "number", "default": 20.0, "description": "Minimum USD spend a location must have to be analyzed (default $20.00)"},
                    "poor_roas_threshold": {"type": "number", "default": 1.0, "description": "Locations with ROAS below this value and sufficient spend are flagged for exclusion (default 1.0)"},
                },
            },
        }
    
    def _register_bidding_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register bidding strategy and bid adjustment tools."""
        return {
            "set_bid_adjustments": {
                "description": "Apply bid modifiers to a campaign by device or location. SYNTAX: adjustments={'device': {'mobile': 1.2, 'desktop': 0.9, 'tablet': 1.1}, 'location': {'2840': 1.3}}. Supported device keys: mobile, desktop, tablet. Location keys are geo_target_constant IDs (e.g., '2840' for USA). Modifiers are multiplicative: 1.2 = +20%, 0.8 = -20%.",
                "handler": self.bidding_tools.set_bid_adjustments,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "adjustments": {"type": "object", "required": True, "description": "Object with keys: 'device' ({'mobile': 1.2, 'desktop': 0.9, 'tablet': 1.1}), 'location' ({'geo_constant_id': 1.3}). Modifiers are multiplicative: 1.2 = +20%, 0.8 = -20%."},
                },
            },
            "get_bid_adjustment_performance": {
                "description": "Retrieve performance metrics for all active non-1.0 bid adjustments on a campaign (device, location criteria). Returns spend, conversions, and ROAS per adjustment segment, with recommendations for increasing, decreasing, or removing each modifier based on efficiency.",
                "handler": self.bidding_tools.get_bid_adjustment_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
            "create_portfolio_bidding_strategy": {
                "description": "Create a portfolio bidding strategy shared across campaigns. Supported strategy_type values: TARGET_CPA (target_cpa_micros optional, defaults to 10,000,000 = $10), TARGET_ROAS (target_roas optional, defaults to 3.0), MAXIMIZE_CONVERSIONS, TARGET_IMPRESSION_SHARE (requires strategy_config={'location': 'ANYWHERE_ON_PAGE'|'TOP_OF_PAGE'|'ABSOLUTE_TOP_OF_PAGE', 'impression_share_target': 0.9, 'max_cpc_bid_limit_micros': 5000000}). Returns strategy resource name for use in update_campaign.",
                "handler": self.bidding_tools.create_portfolio_bidding_strategy,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "strategy_type": {"type": "string", "required": True, "description": "TARGET_CPA, TARGET_ROAS, MAXIMIZE_CONVERSIONS, MAXIMIZE_CLICKS, TARGET_IMPRESSION_SHARE (needs strategy_config)"},
                    "target_cpa_micros": {"type": "number", "description": "Optional when strategy_type=TARGET_CPA. Target cost-per-acquisition in micros ($1 = 1,000,000); defaults to 10,000,000 ($10)"},
                    "target_roas": {"type": "number", "description": "Optional when strategy_type=TARGET_ROAS. Target return on ad spend as a multiplier (e.g., 3.0 = 300% ROAS); defaults to 3.0"},
                    "strategy_config": {"type": "object", "description": "Required when strategy_type=TARGET_IMPRESSION_SHARE: {\"location\": \"TOP_OF_PAGE\" (or ABSOLUTE_TOP_OF_PAGE or ANYWHERE_ON_PAGE), \"impression_share_target\": 0.65, \"max_cpc_bid_limit_micros\": 5000000}"},
                },
            },
            "list_bidding_strategies": {
                "description": "List all portfolio bidding strategies in the account with strategy-specific configuration values (target CPA, target ROAS, impression share target, location). Returns summary counts by strategy type.",
                "handler": self.bidding_tools.list_bidding_strategies,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                },
            },
            "get_device_performance": {
                "description": "Get performance breakdown across three device types (MOBILE, DESKTOP, TABLET): clicks, impressions, cost, conversions, ROAS, spend share, conversion rate, and current bid modifier. Optional campaign_id filter. Returns bid adjustment recommendations for each device based on relative ROAS.",
                "handler": self.bidding_tools.get_device_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "description": "Optional — filter to a specific campaign; omit for account-wide device breakdown"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS", "description": "Google Ads date range: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, TODAY, YESTERDAY"},
                },
            },
        }

    # (Account, Ad Group, Ad, Asset, Budget, Keyword, and Advanced tools)
    # These would follow the same pattern as the campaign and reporting tools