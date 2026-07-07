"""
calendar_utils.py — Deadline-to-Calendar linking utility.

Generates .ics (iCalendar) files from brand deal deadlines so creators can
import them directly into Google Calendar, Outlook, or Apple Calendar.

Also maintains a local JSON-based deadline tracker for at-a-glance viewing
of all upcoming brand deal deadlines.

iCalendar Format (RFC 5545):
    The .ics format is a universal calendar standard supported by all major
    calendar apps. Double-clicking a .ics file on any OS will prompt the
    user to add the event to their default calendar.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Project imports
import config


# ──────────────────────────────────────────────────────────────────────────────
# Console Styling
# ──────────────────────────────────────────────────────────────────────────────

_BLUE = "\033[94m"
_GREEN = "\033[92m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _log(msg: str) -> None:
    """Print a timestamped calendar log message."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Deadline Parsing
# ──────────────────────────────────────────────────────────────────────────────

def _parse_deadline(deadline_str: str | None) -> datetime | None:
    """
    Parse a human-readable deadline string into a datetime object.

    Handles formats like:
        "August 15th"     → 2026-08-15
        "August 15"       → 2026-08-15
        "Sept 1, 2026"    → 2026-09-01
        "July 30th, 2026" → 2026-07-30

    Args:
        deadline_str: Human-readable deadline string from triage extraction.

    Returns:
        datetime or None: Parsed deadline, or None if unparsable.
    """
    if not deadline_str:
        return None

    # Remove ordinal suffixes (1st, 2nd, 3rd, 4th, etc.)
    clean = re.sub(r"(\d+)(?:st|nd|rd|th)", r"\1", deadline_str.strip())

    # Common date formats to try
    formats = [
        "%B %d, %Y",    # August 15, 2026
        "%B %d %Y",     # August 15 2026
        "%B %d",         # August 15 (assume current year)
        "%b %d, %Y",    # Aug 15, 2026
        "%b %d %Y",     # Aug 15 2026
        "%b %d",         # Aug 15
    ]

    current_year = datetime.now().year

    for fmt in formats:
        try:
            parsed = datetime.strptime(clean, fmt)
            # If no year was in the string, default to current/next year
            if parsed.year == 1900:
                parsed = parsed.replace(year=current_year)
                # If the date has already passed this year, use next year
                if parsed < datetime.now():
                    parsed = parsed.replace(year=current_year + 1)
            return parsed
        except ValueError:
            continue

    _log(f"Could not parse deadline: '{deadline_str}'")
    return None


# ──────────────────────────────────────────────────────────────────────────────
# .ics (iCalendar) File Generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_ics_event(
    brand_name: str,
    deadline: datetime,
    deliverables: list[str],
    counter_offer: int | None = None,
    notes: str = "",
) -> str:
    """
    Generate a .ics (iCalendar) formatted event string.

    Creates an all-day event with:
      - A reminder 3 days before the deadline
      - A reminder 1 day before the deadline
      - Full brand deal details in the description

    Args:
        brand_name:    Name of the brand.
        deadline:      Parsed deadline datetime.
        deliverables:  List of deliverable descriptions.
        counter_offer: Agreed/counter-offered amount in dollars.
        notes:         Additional notes.

    Returns:
        str: Complete .ics file content (RFC 5545 compliant).
    """
    uid = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    event_date = deadline.strftime("%Y%m%d")

    # Build description
    deliverables_text = "\\n".join(f"  • {d}" for d in deliverables)
    description = (
        f"Brand Deal Deadline: {brand_name}\\n"
        f"\\n"
        f"Deliverables:\\n{deliverables_text}\\n"
    )
    if counter_offer:
        description += f"\\nAgreed Rate: ${counter_offer:,}\\n"
    if notes:
        description += f"\\nNotes: {notes}\\n"
    description += f"\\nManaged by: {config.APP_NAME}"

    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        f"PRODID:-//{config.APP_NAME}//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now}\r\n"
        f"DTSTART;VALUE=DATE:{event_date}\r\n"
        f"DTEND;VALUE=DATE:{event_date}\r\n"
        f"SUMMARY:📹 DEADLINE: {brand_name} Content Due\r\n"
        f"DESCRIPTION:{description}\r\n"
        "STATUS:CONFIRMED\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-P3D\r\n"
        "ACTION:DISPLAY\r\n"
        f"DESCRIPTION:3 days until {brand_name} content deadline!\r\n"
        "END:VALARM\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-P1D\r\n"
        "ACTION:DISPLAY\r\n"
        f"DESCRIPTION:TOMORROW: {brand_name} content must go live!\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

    return ics_content


def generate_generic_event(
    title: str,
    date: datetime,
    notes: str = "",
) -> str:
    """Generate a generic .ics event for a meeting or call."""
    uid = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    event_date = date.strftime("%Y%m%d")

    description = f"Notes: {notes}\\n\\nManaged by: {config.APP_NAME}"

    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        f"PRODID:-//{config.APP_NAME}//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now}\r\n"
        f"DTSTART;VALUE=DATE:{event_date}\r\n"
        f"DTEND;VALUE=DATE:{event_date}\r\n"
        f"SUMMARY:🗓️ {title}\r\n"
        f"DESCRIPTION:{description}\r\n"
        "STATUS:CONFIRMED\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-P1D\r\n"
        "ACTION:DISPLAY\r\n"
        f"DESCRIPTION:TOMORROW: {title}\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

    return ics_content


# ──────────────────────────────────────────────────────────────────────────────
# Local Deadline Tracker (JSON)
# ──────────────────────────────────────────────────────────────────────────────

CALENDAR_FILE = config.PROJECT_ROOT / "calendar" / "deadlines.json"


def _load_deadlines() -> list[dict]:
    """Load existing deadlines from the JSON tracker."""
    if CALENDAR_FILE.exists():
        try:
            with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_deadlines(deadlines: list[dict]) -> None:
    """Save deadlines to the JSON tracker."""
    CALENDAR_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(deadlines, f, indent=2, default=str)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def add_deadline(
    brand_name: str,
    deadline_str: str | None,
    deliverables: list[str],
    counter_offer: int | None = None,
) -> dict:
    """
    Process a brand deal deadline — parse, save to tracker, generate .ics file.

    This is the main entry point called by the HITL Gatekeeper when a deal
    is approved. It:
      1. Parses the deadline string into a datetime
      2. Generates a .ics calendar event file
      3. Saves the deadline to the local JSON tracker
      4. Returns a summary dict

    Args:
        brand_name:    Name of the brand.
        deadline_str:  Human-readable deadline (e.g., "August 15th").
        deliverables:  List of deliverable descriptions.
        counter_offer: Counter-offer amount in dollars.

    Returns:
        dict: Deadline processing result:
            {
                "parsed_deadline": "2026-08-15",
                "days_until": 51,
                "ics_file_path": "calendar/glowskin_2026-08-15.ics",
                "added_to_tracker": True
            }
    """
    _log("Processing brand deal deadline...")

    # ── Parse the deadline ───────────────────────────────────────────────
    parsed = _parse_deadline(deadline_str)

    if not parsed:
        _log("⚠ No parseable deadline found — skipping calendar entry")
        return {
            "parsed_deadline": None,
            "days_until": None,
            "ics_file_path": None,
            "added_to_tracker": False,
        }

    days_until = (parsed - datetime.now()).days
    _log(f"Deadline: {parsed.strftime('%B %d, %Y')} ({days_until} days from now)")

    # ── Generate .ics file ───────────────────────────────────────────────
    ics_content = generate_ics_event(
        brand_name=brand_name,
        deadline=parsed,
        deliverables=deliverables,
        counter_offer=counter_offer,
    )

    # Save .ics file
    safe_brand = re.sub(r"[^a-zA-Z0-9]", "_", brand_name).lower().strip("_")
    ics_filename = f"{safe_brand}_{parsed.strftime('%Y-%m-%d')}.ics"
    ics_dir = config.PROJECT_ROOT / "calendar"
    ics_dir.mkdir(parents=True, exist_ok=True)
    ics_path = ics_dir / ics_filename

    with open(ics_path, "w", encoding="utf-8") as f:
        f.write(ics_content)

    _log(f"📁 .ics file saved: {ics_path.name}")
    _log("   ↳ Double-click to add to Google Calendar / Outlook / Apple Calendar")

    # ── Update JSON deadline tracker ─────────────────────────────────────
    deadlines = _load_deadlines()
    deadline_entry = {
        "brand_name": brand_name,
        "deadline_date": parsed.strftime("%Y-%m-%d"),
        "days_until": days_until,
        "deliverables": deliverables,
        "counter_offer": counter_offer,
        "ics_file": str(ics_path.name),
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }
    deadlines.append(deadline_entry)
    _save_deadlines(deadlines)

    _log(f"Deadline tracker updated ({len(deadlines)} active deadline(s))")

    return {
        "parsed_deadline": parsed.strftime("%Y-%m-%d"),
        "days_until": days_until,
        "ics_file_path": str(ics_path),
        "added_to_tracker": True,
    }


def add_calendar_event(
    title: str,
    date_str: str,
    notes: str = "",
) -> dict:
    """Process a generic calendar event — parse, save, and generate .ics."""
    parsed = _parse_deadline(date_str)
    if not parsed:
        return {"parsed_date": None, "added": False}

    days_until = (parsed - datetime.now()).days
    _log(f"Event: {title} on {parsed.strftime('%B %d, %Y')}")

    ics_content = generate_generic_event(title, parsed, notes)

    safe_title = re.sub(r"[^a-zA-Z0-9]", "_", title).lower().strip("_")[:20]
    ics_filename = f"event_{safe_title}_{parsed.strftime('%Y-%m-%d')}.ics"
    ics_dir = config.PROJECT_ROOT / "calendar"
    ics_dir.mkdir(parents=True, exist_ok=True)
    ics_path = ics_dir / ics_filename

    with open(ics_path, "w", encoding="utf-8") as f:
        f.write(ics_content)

    _log(f"📁 Event .ics saved: {ics_path.name}")

    # Add to JSON tracker
    deadlines = _load_deadlines()
    deadlines.append({
        "brand_name": title,
        "deadline_date": parsed.strftime("%Y-%m-%d"),
        "days_until": days_until,
        "ics_file": str(ics_path.name),
        "status": "active",
        "type": "event",
        "created_at": datetime.now().isoformat(),
    })
    _save_deadlines(deadlines)

    return {"parsed_date": parsed.strftime("%Y-%m-%d"), "ics_file_path": str(ics_path), "added": True}


def print_upcoming_deadlines() -> None:
    """
    Print a styled summary of all upcoming deadlines to the console.

    Called by main.py at the end of pipeline execution.
    """
    deadlines = _load_deadlines()

    if not deadlines:
        return

    active = [d for d in deadlines if d.get("status") == "active"]
    if not active:
        return

    # Sort by deadline date
    active.sort(key=lambda d: d.get("deadline_date", "9999-12-31"))

    print()
    print(f"  {_BLUE}{_BOLD}📅  UPCOMING DEADLINES{_RESET}")

    for d in active:
        brand = d.get("brand_name", "Unknown")[:25]
        date = d.get("deadline_date", "N/A")
        days = d.get("days_until", "?")
        offer = d.get("counter_offer")
        offer_str = f"${offer:,}" if offer else "TBD"

        # Color code by urgency
        if isinstance(days, int):
            if days <= 7:
                urgency = f"\033[91m{days}d ⚠️{_RESET}"   # Red — urgent
            elif days <= 14:
                urgency = f"\033[93m{days}d{_RESET}"       # Yellow — soon
            else:
                urgency = f"{_GREEN}{days}d{_RESET}"       # Green — comfortable
        else:
            urgency = "?"

        print(f"  {_BLUE}{brand:<25s}{_RESET}  {date}  {urgency:<20s}  {offer_str:>8s}")

    print()
    print(f"  {_BLUE}📁 .ics files saved in: calendar/{_RESET}")
    print(f"  {_BLUE}↳ Double-click any .ics to add to your calendar app{_RESET}")
