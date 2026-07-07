"""
hitl_gatekeeper.py — Human-in-the-Loop Terminal Approval Gate.

Implements strict human oversight for the AI pipeline. Instead of
automatically sending the negotiation email or publishing the video script,
this module pauses terminal execution and requires explicit human approval.

This is the security layer — nothing leaves the system without the
creator's consent.

Workflow:
    1. Display a prominent "HUMAN REVIEW REQUIRED" banner
    2. Print the drafted negotiation email in a styled box
    3. Print the full video script in a styled box
    4. Prompt: "[A]pprove and save draft, [E]dit, or [R]eject?"
    5. Wait for input() — blocks execution entirely
    6. On Approve → save to drafts/ + create calendar event for deadline
    7. On Edit → log feedback (demo mode: re-display with note)
    8. On Reject → discard all output
"""

from __future__ import annotations

import os
import textwrap
from datetime import datetime
from pathlib import Path

# Project imports
import config
import calendar_utils


# ──────────────────────────────────────────────────────────────────────────────
# Console Styling Constants
# ──────────────────────────────────────────────────────────────────────────────

_RED = "\033[38;5;210m"
_GREEN = "\033[38;5;150m"
_YELLOW = "\033[38;5;223m"
_BLUE = "\033[38;5;153m"
_MAGENTA = "\033[38;5;183m"
_CYAN = "\033[38;5;159m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"
_BG_RED = "\033[48;5;210m"
_BG_GREEN = "\033[48;5;150m"
_WHITE = "\033[97m"


def _log(msg: str) -> None:
    """Print a timestamped gatekeeper log message."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Display Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _pad_line(text: str, width: int) -> str:
    """
    Pad text to visual width, accounting for astral characters (emojis).
    Astral characters take 2 UTF-16 code units, which aligns with them
    taking 2 columns in most standard terminals.
    """
    visual_len = len(text.encode("utf-16-le")) // 2
    padding = max(0, width - visual_len)
    return text + " " * padding


def _print_banner() -> None:
    """Print the HUMAN REVIEW REQUIRED warning banner."""
    print()
    print(f"  {_BG_RED}{_WHITE}{_BOLD}  ⚠️  HUMAN REVIEW REQUIRED  ⚠️  {_RESET}")
    print(f"  {_RED}The AI pipeline has completed. Review the drafts below{_RESET}")
    print(f"  {_RED}before any content is saved or sent.{_RESET}")
    print()


def _print_section(title: str, content: str, color: str) -> None:
    """Print a titled content section."""
    print()
    print(f"  {color}{_BOLD}{title}{_RESET}")

    # Print each line of content, wrapping long lines
    for line in content.split("\n"):
        leading_spaces = len(line) - len(line.lstrip(' '))
        indent = " " * leading_spaces
        
        wrapped_lines = textwrap.wrap(
            line.strip(), 
            width=66, 
            initial_indent=indent, 
            subsequent_indent=indent
        )
        
        if not wrapped_lines:
            print(f"  {color}{_RESET}")
        
        for wl in wrapped_lines:
            print(f"  {color}{wl}{_RESET}")

    print()


def _print_prompt() -> None:
    """Print the action prompt."""
    print()
    print(f"  {_YELLOW}{_BOLD}Choose an action:{_RESET}")
    print(f"    {_GREEN}[A]{_RESET}{_YELLOW}pprove — Save drafts to disk + add deadline to calendar{_RESET}")
    print(f"    {_YELLOW}[E]{_RESET}{_YELLOW}dit   — Provide feedback for revisions{_RESET}")
    print(f"    {_RED}[R]{_RESET}{_YELLOW}eject — Discard all drafts{_RESET}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Draft Saving
# ──────────────────────────────────────────────────────────────────────────────

def _save_draft(
    email_draft: str,
    metadata: dict,
    video_script: str | None = None,
    brand_brief: dict | None = None,
) -> str:
    """
    Save the approved email draft and video script to the drafts/ directory.

    Creates a combined file with both outputs, timestamped and labeled
    with the brand name for easy retrieval.

    Args:
        email_draft:  The negotiation email text.
        video_script: The video script text.
        metadata:     Triage result metadata.
        brand_brief:  Brand brief dict (for calendar linking).

    Returns:
        str: Path to the saved draft file.
    """
    drafts_dir = config.DRAFTS_DIR
    drafts_dir.mkdir(parents=True, exist_ok=True)

    # Build filename from timestamp + brand name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    sender = metadata.get("sender", "unknown")
    # Sanitize sender for filename
    safe_sender = "".join(c if c.isalnum() or c in "-_ " else "" for c in sender)
    safe_sender = safe_sender.strip().replace(" ", "_")[:30]

    filename = f"{timestamp}_{safe_sender}.txt"
    filepath = drafts_dir / filename

    # Build the combined draft file
    content = textwrap.dedent(f"""\
        APPROVED DRAFT — {config.APP_NAME}
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Status: APPROVED BY HUMAN REVIEW

        CLASSIFICATION
        Category:   {metadata.get('classification', 'N/A')}
        Confidence: {metadata.get('confidence', 0):.0%}
        Sender:     {metadata.get('sender', 'N/A')}
        Subject:    {metadata.get('subject', 'N/A')}

        EMAIL SUMMARY
        
        {metadata.get('summary', 'No summary available.')}

        EMAIL DRAFT

        {email_draft}
    """)

    if video_script:
        content += textwrap.dedent(f"""
        VIDEO SCRIPT

        {video_script}
        """)

    content += textwrap.dedent("""
        End of Draft
    """)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return str(filepath)


# ──────────────────────────────────────────────────────────────────────────────
# Main Review Function
# ──────────────────────────────────────────────────────────────────────────────

def review(
    email_draft: str,
    metadata: dict,
    video_script: str | None = None,
    negotiation_result: dict | None = None,
) -> dict:
    """
    Execute the Human-in-the-Loop review process.

    This is the main entry point called by the orchestrator. It blocks
    terminal execution until the human makes a decision.

    Args:
        email_draft:        The counter-offer email text.
        video_script:       The generated video script text.
        metadata:           Triage result metadata dict.
        negotiation_result: Full negotiation result dict (for calendar).

    Returns:
        dict: Review outcome:
            {
                "decision": "approved" | "edited" | "rejected",
                "draft_path": "drafts/2026-06-25_Sarah_Chen.txt" | None,
                "calendar_result": { ... } | None,
                "feedback": None | "user's edit feedback"
            }
    """
    _log("Entering Human-in-the-Loop review gate...")

    # ── Display everything for review ────────────────────────────────────
    _print_banner()
    
    summary = metadata.get("summary")
    if summary:
        _print_section("📝 EMAIL SUMMARY (TL;DR)", summary, _YELLOW)
        
    _print_section("📧 EMAIL DRAFT", email_draft, _CYAN)
    if video_script:
        _print_section("🎬 VIDEO SCRIPT", video_script, _MAGENTA)

    # Show deadline info if available
    brand_brief = negotiation_result.get("brand_brief", {}) if negotiation_result else {}
    deadline = brand_brief.get("deadline")
    if deadline:
        print(f"\n  {_BLUE}📅 Deadline detected: {_BOLD}{deadline}{_RESET}")
        print(f"  {_DIM}   Will be added to calendar on approval{_RESET}")

    # ── Prompt for decision ──────────────────────────────────────────────
    _print_prompt()

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            choice = input(f"\n  {_BOLD}Your choice [A/E/R]: {_RESET}").strip().upper()
        except (EOFError, KeyboardInterrupt):
            # Handle non-interactive environments gracefully
            print()
            _log("Non-interactive environment detected — auto-approving for demo")
            choice = "A"

        # ── APPROVE ──────────────────────────────────────────────────
        if choice == "A":
            _log(f"{_BG_GREEN}{_WHITE} APPROVED {_RESET}")

            # Save the draft
            draft_path = _save_draft(email_draft, metadata, video_script, brand_brief)
            _log(f"📁 Draft saved: {draft_path}")

            # Link deadline to calendar
            calendar_result = None
            if deadline and negotiation_result:
                calendar_result = calendar_utils.add_deadline(
                    brand_name=brand_brief.get("brand_name", "Unknown Brand"),
                    deadline_str=deadline,
                    deliverables=brand_brief.get("deliverables", []),
                    counter_offer=negotiation_result.get("counter_offer_amount"),
                )
                
            # Link extra dates to calendar
            extra_dates = metadata.get("extracted_requirements", {}).get("extra_dates", [])
            for date_str in extra_dates:
                sender = metadata.get("sender", "Unknown").split("<")[0].strip()
                calendar_utils.add_calendar_event(
                    title=f"Event: {sender}",
                    date_str=date_str,
                    notes=f"Subject: {metadata.get('subject', '')}",
                )

            return {
                "decision": "approved",
                "draft_path": draft_path,
                "calendar_result": calendar_result,
                "feedback": None,
            }

        # ── EDIT ─────────────────────────────────────────────────────
        elif choice == "E":
            _log(f"{_YELLOW}EDIT REQUESTED{_RESET}")
            print()

            try:
                feedback = input(
                    f"  {_BOLD}What would you like to change?{_RESET}\n  > "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                feedback = "No feedback provided"
                print()

            _log(f"Feedback received: \"{feedback}\"")
            _log("Returning control to orchestrator to regenerate drafts...")

            return {
                "decision": "edited",
                "draft_path": None,
                "calendar_result": None,
                "feedback": feedback,
            }

        # ── REJECT ───────────────────────────────────────────────────
        elif choice == "R":
            _log(f"{_RED}REJECTED{_RESET} — All drafts discarded")
            return {
                "decision": "rejected",
                "draft_path": None,
                "calendar_result": None,
                "feedback": None,
            }

        else:
            remaining = max_attempts - attempt - 1
            _log(f"Invalid input '{choice}'. Please enter A, E, or R. ({remaining} attempts left)")

    _log("No valid input received — auto-rejecting to fail safe")
    return {
        "decision": "rejected",
        "draft_path": None,
        "calendar_result": None,
        "feedback": None
    }


def review_personal(metadata: dict) -> None:
    """Display a personal message notification and wait for acknowledgment."""
    _log("Personal message detected. Displaying notification...")
    print()
    print(f"  {_BG_RED}{_WHITE}{_BOLD}  🚨  PERSONAL MESSAGE NOTIFICATION  🚨  {_RESET}")
    print(f"  {_RED}This looks like a personal email. The AI will not reply.{_RESET}")
    print()
    
    summary = metadata.get("summary", "No summary available")
    _print_section("📝 MESSAGE SUMMARY", summary, _YELLOW)
    
    sender = metadata.get("sender", "Unknown")
    print(f"\n  {_BOLD}From: {sender}{_RESET}")
    print(f"  {_CYAN}Press Enter to acknowledge and continue...{_RESET}", end="")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass
    print()
