"""
config.py — Shared configurations and mock settings for the Creator Studio.

All creator metrics, directory paths, and style preferences are defined here
as plain Python constants. No .env files, no external dependencies.

These values simulate a mid-tier tech creator on YouTube/Instagram.
Agents and the MCP server read from this module to maintain consistency.

NOTE: This module also handles Windows terminal encoding setup.
      Since every other module imports config, this ensures UTF-8
      and ANSI color support are enabled exactly once at startup,
      before any module tries to print Unicode characters (emojis,
      box-drawing chars, etc.).
"""

import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Windows Terminal Compatibility
# ──────────────────────────────────────────────────────────────────────────────
# Problem: Windows default encoding is cp1252, which can't render emojis or
#          Unicode box-drawing characters (╔═║ etc.). This causes
#          UnicodeEncodeError crashes when agents try to print styled output.
#
# Solution: Force sys.stdout to use UTF-8 encoding at startup. This must
#           happen before ANY print() call in any module.
#
# Also enable ANSI escape codes (colors) on Windows 10+ terminals, which
# are disabled by default. Without this, you'd see raw escape sequences
# like "\033[91m" instead of colored text.
# ──────────────────────────────────────────────────────────────────────────────

if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass  # Best-effort — older Python versions may not support reconfigure

if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf-8-sig"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

# Enable ANSI escape codes on Windows 10+ (for colored terminal output)
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # SetConsoleMode flag 0x7 = ENABLE_PROCESSED_OUTPUT |
        #   ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass  # Silently skip if ctypes unavailable or not Windows

# ──────────────────────────────────────────────────────────────────────────────
# Creator Profile — Mock Metrics
# ──────────────────────────────────────────────────────────────────────────────

CREATOR_NAME = "Ashmita Dhawan"
CREATOR_HANDLE = "@ashmita_dhawan"

PLATFORMS = {
    "YouTube": {
        "subscribers": 500_000,
        "avg_views": 45_000,
        "engagement_rate_pct": 4.2,
        "avg_watch_time_secs": 142,
        "base_cpm": 20.00
    },
    "Instagram": {
        "followers": 120_000,
        "avg_views": 25_000,
        "engagement_rate_pct": 5.8,
        "base_cpm": 12.00
    },
    "TikTok": {
        "followers": 850_000,
        "avg_views": 150_000,
        "engagement_rate_pct": 8.5,
        "base_cpm": 6.00
    }
}

TOP_CATEGORY = "Tech & Lifestyle"  # Top-performing content category

# ──────────────────────────────────────────────────────────────────────────────
# Pricing Configuration
# ──────────────────────────────────────────────────────────────────────────────

ENGAGEMENT_MULTIPLIER = 1.15   # Applied when engagement_rate > 3%
PLATFORM_COMBO_PREMIUM = 1.20  # Premium for multi-platform bundles
COUNTER_OFFER_FLOOR = 1.35     # Minimum multiplier over brand's stated budget
ROUNDING_STEP = 50             # Round counter-offers up to nearest $N

# ──────────────────────────────────────────────────────────────────────────────
# Directory Paths
# ──────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent
MOCK_INBOX_DIR = PROJECT_ROOT / "mock_inbox"
DRAFTS_DIR = PROJECT_ROOT / "drafts"

# ──────────────────────────────────────────────────────────────────────────────
# Creator Style Preferences — Used by Creative Agent
# ──────────────────────────────────────────────────────────────────────────────

CREATOR_STYLE = {
    "tone": "energetic, witty, and conversational",
    "format": "fast-paced with jump cuts",
    "signature_intro": "Hey guys, Ashmita here!",
    "signature_outro": "Drop a comment if you learned something — bye! ✌️",
    "email_signoff": "Best,",
    "preferred_angles": [
        "myth-busting",
        "honest review",
        "day-in-my-life integration",
    ],
    "avoid": [
        "overly salesy language",
        "clickbait without payoff",
        "reading from a teleprompter",
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# System Settings
# ──────────────────────────────────────────────────────────────────────────────

APP_NAME = "Autonomous Creator Studio & Influencer Manager"
APP_VERSION = "1.0.0"
LOG_TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"
