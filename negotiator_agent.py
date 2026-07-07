"""
negotiator_agent.py — Deal Negotiation Agent.

When the Triage Agent classifies an email as BRAND_DEAL, this agent:
  1. Calls the MCP server to fetch real-time creator analytics
  2. Calculates the creator's true market value using CPM-based pricing
  3. Compares brand's offered budget against the calculated value
  4. Generates a professional counter-offer email draft
  5. Passes the brand brief downstream to the Creative Agent

Pricing Algorithm:
    true_value = (avg_views / 1000) × estimated_cpm × num_deliverables
    Apply engagement multiplier if engagement > 3%
    Apply platform combo premium for multi-platform deals
    counter_offer = _calculate_true_value(brand_budget, deliverables, metrics, feedback)
    Round up to nearest $50
"""

from __future__ import annotations

import math
import textwrap
from datetime import datetime

# Project imports
import config
from mcp_server.main import mcp_server


# ──────────────────────────────────────────────────────────────────────────────
# Console Styling
# ──────────────────────────────────────────────────────────────────────────────

_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _log(msg: str) -> None:
    """Print a timestamped negotiator log message."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Pricing Engine
# ──────────────────────────────────────────────────────────────────────────────

def _calculate_counter_offer(
    metrics: dict,
    brand_budget: int | None,
    num_deliverables: int,
    platforms: list[str],
    feedback: str = None
) -> dict:
    """
    Calculate an optimized counter-offer based on analytics and pricing config.

    The algorithm values the creator's reach fairly by computing what their
    analytics are actually worth, then ensures the counter-offer is always
    above a floor relative to the brand's stated budget.

    Args:
        metrics:          Creator analytics from MCP server.
        brand_budget:     Budget offered by the brand (dollars), or None.
        num_deliverables: Number of content deliverables requested.
        platforms:        List of platforms requested by the brand.
        feedback:         Optional override/feedback text.

    Returns:
        dict: Pricing breakdown:
            {
                "base_cpm_value": 1102.50,
                "engagement_bonus": True,
                "platform_premium": True,
                "calculated_value": 1521.45,
                "brand_floor": 1080.00,
                "counter_offer": 1550,
                "reasoning": "..."
            }
    """
    platform_metrics = metrics.get("platforms", {})
    
    base_value = 0.0
    engagement_bonus = False
    platform_premium = False
    
    reasoning_parts = []

    # ── Step 1 & 2: Base CPM value and Engagement per platform ───────────
    for plat in platforms:
        p_stats = platform_metrics.get(plat)
        if not p_stats:
            continue
            
        avg_views = p_stats.get("avg_views_per_video", 10000)
        cpm = p_stats.get("estimated_cpm_value", 10.0)
        engagement = p_stats.get("engagement_rate_pct", 2.0)
        
        # CPM = cost per 1,000 views
        p_val = (avg_views / 1000) * cpm * max(num_deliverables, 1)
        
        if engagement > 3.0:
            p_val *= config.ENGAGEMENT_MULTIPLIER
            engagement_bonus = True
            
        base_value += p_val
        reasoning_parts.append(f"{plat}: {avg_views:,} views @ ${cpm:.2f} CPM")

    # ── Step 3: Platform combo premium ───────────────────────────────────
    if len(platforms) > 1:
        platform_premium = True
        base_value *= config.PLATFORM_COMBO_PREMIUM
        reasoning_parts.append(f"Multi-platform premium")

    # ── Step 4: Floor against brand budget ───────────────────────────────
    brand_floor = 0
    if brand_budget:
        brand_floor = brand_budget * config.COUNTER_OFFER_FLOOR

    # ── Step 5: Final counter-offer ──────────────────────────────────────
    raw_offer = max(base_value, brand_floor)
    # Apply manual feedback overrides (Heuristic simulation of LLM instruction following)
    counter_offer = int(
        math.ceil(raw_offer / config.ROUNDING_STEP) * config.ROUNDING_STEP
    )
    if feedback:
        import re
        # Look for numbers in feedback (e.g., "$3500", "5000") to adjust pricing
        price_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*|\d+)', feedback)
        if price_match:
            new_price = int(price_match.group(1).replace(',', ''))
            if new_price > 100:
                counter_offer = new_price
                _log(f"Feedback heuristic: Adjusted counter-offer to ${counter_offer}")

    if brand_budget and brand_floor > base_value:
        reasoning_parts.append(f"floored at {config.COUNTER_OFFER_FLOOR}× brand budget")

    return {
        "base_cpm_value": round(base_value, 2),
        "engagement_bonus": engagement_bonus,
        "platform_premium": platform_premium,
        "calculated_value": round(base_value, 2),
        "brand_floor": round(brand_floor, 2),
        "counter_offer": counter_offer,
        "reasoning": ", ".join(reasoning_parts),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Email Draft Generator
# ──────────────────────────────────────────────────────────────────────────────

def _draft_counter_email(
    triage_result: dict,
    pricing: dict,
    metrics: dict,
    platforms: list[str],
    feedback: str = None,
) -> str:
    """
    Draft a professional counter-offer email reply.

    The tone is firm but friendly — positions the creator's value clearly
    while keeping the door open for negotiation.

    Args:
        triage_result: Output from the Triage Agent.
        pricing:       Output from _calculate_counter_offer().
        metrics:       Creator analytics from MCP server.
        platforms:     List of requested platforms.
        feedback:      Optional feedback note to include.

    Returns:
        str: Formatted email draft ready for HITL review.
    """
    sender = triage_result.get("sender", "Partner")
    subject = triage_result.get("subject", "Partnership Inquiry")
    reqs = triage_result.get("extracted_requirements", {})

    # Extract sender's first name for greeting
    sender_name = sender.split()[0] if sender != "Unknown Sender" else "there"

    # Build deliverables summary
    deliverables = reqs.get("deliverables", ["Content package"])
    deliverables_summary = ", ".join(deliverables[:3])
    deliverables_list = "\n".join(f"  • {d}" for d in deliverables)

    counter_offer = pricing["counter_offer"]
    platform_metrics = metrics.get("platforms", {})
    
    stats_lines = []
    for plat in platforms:
        if plat in platform_metrics:
            p_stats = platform_metrics[plat]
            subs = p_stats.get("subscribers", p_stats.get("followers", 0))
            views = p_stats.get("avg_views_per_video", 0)
            eng = p_stats.get("engagement_rate_pct", 0)
            stats_lines.append(f"          [{plat}] 📊 {subs:,} subs/followers | 👁️ {views:,} avg views | 💬 {eng}% engagement")

    stats_block = "\n".join(stats_lines) if stats_lines else "          📊 High engagement across multiple platforms"

    tone = config.CREATOR_STYLE.get("tone", "authentic")
    
    if "sarcastic" in tone:
        intro_line = "Thanks for reaching out. Usually I ignore these, but this campaign actually looks fun."
        pitch_line = f"My audience can smell a script from a mile away, so I keep my {', '.join(platforms)} integrations painfully honest. That's why they actually buy things."
        closing = "Let me know if this works for you, otherwise no hard feelings!"
    elif "cozy" in tone or "calm" in tone:
        intro_line = "Thank you so much for reaching out — I would love to explore a cozy integration for this campaign."
        pitch_line = f"I always ensure sponsor integrations feel incredibly organic and gentle for my audience across {', '.join(platforms)}. This helps maintain a high trust factor."
        closing = "I'd love to discuss any customizations that feel right for both of us."
    elif "high-energy" in tone or "hype" in tone:
        intro_line = "LET'S GO! Thanks for reaching out, I am massively hyped about this campaign!"
        pitch_line = f"I go all out on my {', '.join(platforms)} integrations to make sure they are high-energy and actually keep people watching, which is why my stats crush the industry average."
        closing = "Let's make this happen and crush this campaign!"
    elif "professional" in tone:
        intro_line = "Thank you for the inquiry. I have reviewed the brief and am interested in moving forward."
        pitch_line = f"I pride myself on delivering clear, educational integrations on {', '.join(platforms)} that provide genuine value to my audience and drive measurable results."
        closing = "I look forward to discussing how we can tailor this package to meet your KPIs."
    else:
        intro_line = "Thank you so much for reaching out — I'm genuinely excited about this campaign!"
        pitch_line = f"I always ensure sponsor integrations feel authentic to my audience and follow the latest {', '.join(platforms)} trends, which is why my engagement rates consistently outperform industry averages."
        closing = "Looking forward to making this collaboration happen!"

    outro = config.CREATOR_STYLE.get("email_signoff", "Best,")

    email = textwrap.dedent(f"""\
        Subject: Re: {subject}

        Hi {sender_name},

        {intro_line}

        Based on my current channel performance:
{stats_block}

        My standard rate for this package ({deliverables_summary}) is ${counter_offer:,}.

        This includes:
{deliverables_list}

        {pitch_line}
        
        {closing}

        {outro}
        {config.CREATOR_NAME}
    """)
    
    if feedback:
        email += f"\n\n    [Note: Revised based on feedback: '{feedback}']"

    return email.strip()


# ──────────────────────────────────────────────────────────────────────────────
# Main Agent Entry Point
# ──────────────────────────────────────────────────────────────────────────────

def negotiate(triage_result: dict, feedback: str = None) -> dict:
    """
    Execute the full negotiation pipeline for a brand deal.

    This is the main entry point called by the orchestrator. It:
      1. Fetches real-time metrics via MCP
      2. Calculates optimized pricing
      3. Drafts a counter-offer email
      4. Packages everything for the Creative Agent

    Args:
        triage_result: Output dict from triage_agent.classify().
        feedback:      Optional guidance on the negotiation.

    Returns:
        dict: Negotiation result:
            {
                "counter_offer_amount": 1650,
                "pricing_breakdown": { ... },
                "negotiation_email_draft": "Subject: Re: ...\n...",
                "brand_brief": {
                    "brand_name": "GlowSkin Co.",
                    "deliverables": [...],
                    "budget_offered": 800,
                    "deadline": "August 15th",
                    "key_requirements": [...],
                    "subject": "..."
                },
                "metrics_snapshot": { ... }
            }
    """
    _log("Starting negotiation pipeline...")

    # ── Step 1: Fetch analytics from MCP ─────────────────────────────────
    _log("Calling MCP server: get_creator_metrics()")
    mcp_response = mcp_server.call_tool("get_creator_metrics")

    if mcp_response["status"] != "success":
        _log(f"⚠ MCP call failed — using fallback config values")
        # Ensure we still have the new platform structure if fallback
        metrics = {
            "creator_name": config.CREATOR_NAME,
            "handle": config.CREATOR_HANDLE,
            "platforms": {
                "YouTube": {
                    "subscribers": config.PLATFORMS["YouTube"]["subscribers"],
                    "avg_views_per_video": config.PLATFORMS["YouTube"]["avg_views"],
                    "engagement_rate_pct": config.PLATFORMS["YouTube"]["engagement_rate_pct"],
                    "estimated_cpm_value": config.PLATFORMS["YouTube"]["base_cpm"]
                }
            }
        }
    else:
        metrics = mcp_response["data"]
        _log("MCP metrics received ✓")

    # ── Step 2: Extract deal parameters from triage result ───────────────
    reqs = triage_result.get("extracted_requirements", {})
    brand_budget = reqs.get("budget_offered")
    deliverables = reqs.get("deliverables", [])
    
    # If the brand didn't specify deliverables, propose a standard package
    if not deliverables or deliverables == ["Deliverables not specified"]:
        _log("Deliverables not specified — proposing standard package")
        deliverables = [
            "1x Dedicated YouTube Integration (60-90s)",
            "1x Instagram Story with Link"
        ]
        if "extracted_requirements" in triage_result:
            triage_result["extracted_requirements"]["deliverables"] = deliverables
            
    num_deliverables = len(deliverables)

    if brand_budget:
        _log(f"Brand offered: ${brand_budget:,} for {num_deliverables} deliverable(s)")
    else:
        _log("No budget specified by brand — calculating from analytics only")

    # ── Step 3: Detect Platforms ─────────────────────────────────────────
    deliv_text = " ".join(deliverables).lower()
    platforms = []
    if "youtube" in deliv_text or "yt" in deliv_text or "short" in deliv_text:
        platforms.append("YouTube")
    if "instagram" in deliv_text or "ig" in deliv_text or "reel" in deliv_text or "story" in deliv_text:
        platforms.append("Instagram")
    if "tiktok" in deliv_text or "tt" in deliv_text:
        platforms.append("TikTok")
        
    if not platforms:
        platforms = ["YouTube"] # Default

    # ── Step 4: Calculate pricing ────────────────────────────────────────
    pricing = _calculate_counter_offer(metrics, brand_budget, num_deliverables, platforms, feedback)

    # ── Step 5: Draft counter-offer email ────────────────────────────────
    _log("Drafting counter-offer email...")
    email_draft = _draft_counter_email(triage_result, pricing, metrics, platforms, feedback)
    _log("Email draft: READY ✓")

    # ── Step 5: Package brand brief for Creative Agent ───────────────────
    # Extract brand name from sender (take the company part after dash/comma)
    sender = triage_result.get("sender", "Unknown Brand")
    brand_name = sender
    for sep in ["—", "-", ",", "@"]:
        if sep in sender:
            parts = sender.split(sep)
            brand_name = parts[-1].strip()
            break

    brand_brief = {
        "brand_name": brand_name,
        "subject": triage_result.get("subject", ""),
        "deliverables": deliverables,
        "platforms": platforms,
        "budget_offered": brand_budget,
        "counter_offer": pricing["counter_offer"],
        "deadline": reqs.get("deadline"),
        "key_requirements": reqs.get("key_requirements", []),
        "raw_text": triage_result.get("raw_text", ""),
    }

    _log("Brand brief packaged for Creative Agent ✓")

    return {
        "counter_offer_amount": pricing["counter_offer"],
        "pricing_breakdown": pricing,
        "negotiation_email_draft": email_draft,
        "brand_brief": brand_brief,
        "metrics_snapshot": metrics,
    }
