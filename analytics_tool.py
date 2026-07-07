"""
analytics_tool.py — Mock MCP tool that simulates pulling creator analytics.

In production, this would connect to the YouTube Analytics API, Instagram
Graph API, or a combined analytics dashboard. For this local demo, it reads
base metrics from config.py and adds slight random jitter (±5%) to simulate
the variability of real-time API responses.

MCP Tool Name: get_creator_metrics
Returns:       JSON-serializable dict of creator performance metrics
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone

# Project imports
# NOTE: config is imported first because it sets up UTF-8 encoding on
# Windows. Without this, Unicode characters in log messages would crash.
import config


# ──────────────────────────────────────────────────────────────────────────────
# MCP Tool Implementation
# ──────────────────────────────────────────────────────────────────────────────

def _jitter(value: float, pct: float = 0.05) -> float:
    """
    Apply random jitter of ±pct to a numeric value.

    This simulates the natural variance you'd see in real-time analytics
    (e.g., subscriber counts fluctuating between API calls).

    Args:
        value: Base numeric value.
        pct:   Maximum percentage deviation (default ±5%).

    Returns:
        Jittered value as a float.
    """
    factor = 1.0 + random.uniform(-pct, pct)
    return round(value * factor, 2)


def get_creator_metrics() -> dict:
    """
    Mock MCP Tool — Simulates pulling real-time creator analytics.

    This is the core tool exposed by the MCP server. The Negotiator Agent
    calls this to fetch up-to-date channel performance data before
    calculating a counter-offer.

    Returns:
        dict: JSON-serializable analytics snapshot, e.g.:
            {
                "creator_name": "TechVibes with Priya",
                "handle": "@techvibes_priya",
                "platform": "YouTube + Instagram",
                "subscribers": 497500,
                "avg_views_per_video": 44100,
                "engagement_rate_pct": 4.18,
                "avg_watch_time_seconds": 140,
                "top_performing_category": "Tech Reviews",
                "estimated_cpm_value": 24.50,
                "last_updated": "2026-06-25T14:00:00+00:00"
            }
    """
    # ── Build analytics snapshot with realistic jitter ────────────────────────
    metrics = {
        "creator_name": config.CREATOR_NAME,
        "handle": config.CREATOR_HANDLE,
        "top_performing_category": config.TOP_CATEGORY,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "platforms": {}
    }

    for platform, stats in config.PLATFORMS.items():
        metrics["platforms"][platform] = {
            "subscribers": int(_jitter(stats.get("subscribers", stats.get("followers", 0)))),
            "avg_views_per_video": int(_jitter(stats["avg_views"])),
            "engagement_rate_pct": round(_jitter(stats["engagement_rate_pct"]), 2),
            "estimated_cpm_value": round(_jitter(stats["base_cpm"] * 1.225), 2),
        }
        
        if "avg_watch_time_secs" in stats:
            metrics["platforms"][platform]["avg_watch_time_seconds"] = int(_jitter(stats["avg_watch_time_secs"]))

    return metrics


def get_tool_schema() -> dict:
    """
    Return the MCP-compliant tool schema for get_creator_metrics.

    This follows the MCP tool definition format so the MCP server can
    register it and agents can discover its capabilities.

    Returns:
        dict: Tool schema with name, description, and parameter spec.
    """
    return {
        "name": "get_creator_metrics",
        "description": (
            "Fetches real-time creator analytics including subscriber count, "
            "average views, engagement rate, watch time, and estimated CPM value. "
            "Simulates a pull from YouTube/Instagram Analytics APIs."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    }
