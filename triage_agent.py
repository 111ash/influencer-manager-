"""
triage_agent.py — Email Classification Agent.

Classifies incoming email text into one of three categories:
  - BRAND_DEAL  : A brand partnership or sponsorship inquiry
  - FAN_MAIL    : A fan message, question, or compliment
  - SPAM        : Unsolicited junk, scams, or lottery messages

Implementation Note:
    This uses deterministic keyword-based classification to simulate
    LLM reasoning. The architecture is designed so that swapping in a
    real LLM (e.g., google.genai, openai) requires changing only the
    classify() method — the input/output contract stays identical.

    Confidence scores are calculated based on keyword density — the more
    matching keywords found, the higher the confidence.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Console Styling
# ──────────────────────────────────────────────────────────────────────────────

_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _log(msg: str) -> None:
    """Print a timestamped triage log message."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Classification Keywords
# ──────────────────────────────────────────────────────────────────────────────

# Each category has a set of weighted keywords. Keywords earlier in the list
# carry slightly more weight (position-based scoring).

BRAND_KEYWORDS = [
    "partnership", "collaboration", "sponsor", "sponsored", "sponsorship",
    "budget", "campaign", "rate card", "paid", "brand deal", "deliverables",
    "flat fee", "integration", "product placement", "affiliate",
    "influencer", "content creator", "promote", "promotion",
]

FAN_KEYWORDS = [
    "love your", "fan", "inspired", "big fan", "how did you start",
    "amazing content", "keep it up", "your videos", "watching your",
    "supporter", "admire", "changed my", "learned from",
]

SPAM_KEYWORDS = [
    "congratulations", "won", "click here", "lottery", "free",
    "act now", "limited time", "claim your", "prize", "winner",
    "banking details", "urgent", "expire", "forfeit",
]

PERSONAL_KEYWORDS = [
    "dinner", "family", "mom", "dad", "friend", "catch up", "lunch", "miss you",
    "personal", "birthday", "party", "get together", "weekend"
]

PR_KEYWORDS = [
    "pr package", "gifting", "gifted", "send you our product", 
    "pr list", "no obligation", "free product", "care package"
]

BARTER_KEYWORDS = [
    "barter", "collab in exchange", "unpaid", "product in exchange", 
    "gifted collaboration", "in exchange for", "free in exchange"
]


# ──────────────────────────────────────────────────────────────────────────────
# Email Metadata Extraction
# ──────────────────────────────────────────────────────────────────────────────

def _extract_sender(text: str) -> str:
    """
    Extract the sender's name/email from the email text.

    Looks for 'From:' header first, then falls back to signature patterns.

    Args:
        text: Raw email text.

    Returns:
        str: Extracted sender or "Unknown Sender".
    """
    # Try From: header
    match = re.search(r"^From:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try signature block (last lines often have the name)
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    if len(lines) >= 2:
        # Check if second-to-last line looks like a name
        candidate = lines[-2]
        if len(candidate) < 60 and not candidate.startswith("http"):
            return candidate

    return "Unknown Sender"


def _extract_subject(text: str) -> str:
    """
    Extract the email subject line.

    Args:
        text: Raw email text.

    Returns:
        str: Extracted subject or "No Subject".
    """
    match = re.search(r"^Subject:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "No Subject"


def _extract_budget(text: str) -> Optional[int]:
    """
    Extract a dollar budget amount from the email text.

    Handles formats like: $800, $1,200, $10000, $800 flat fee

    Args:
        text: Raw email text.

    Returns:
        int or None: Extracted budget in dollars, or None if not found.
    """
    # Match dollar amounts like $800, $1,200, $10,000
    matches = re.findall(r"\$\s*([\d,]+)", text)
    if matches:
        # Take the first reasonable amount (skip obvious scam numbers > $10k)
        for raw in matches:
            amount = int(raw.replace(",", ""))
            if 50 <= amount <= 50_000:
                return amount
    return None


def _extract_deliverables(text: str) -> list[str]:
    """
    Extract campaign deliverables from the email text.

    Looks for bullet points, numbered lists, and common deliverable patterns.

    Args:
        text: Raw email text.

    Returns:
        list[str]: Extracted deliverable descriptions.
    """
    deliverables = []

    # Pattern: lines starting with -, *, •, or numbers
    bullet_lines = re.findall(
        r"^[\s]*[-*•]\s*(.+)$", text, re.MULTILINE
    )
    for line in bullet_lines:
        clean = line.strip()
        # Skip if the line is just a horizontal separator (e.g., --------)
        if re.match(r"^[-*•=_\s]+$", clean):
            continue
        if len(clean) > 10:  # Skip very short bullets
            deliverables.append(clean)

    # Pattern: "N x [deliverable]" or "N [deliverable]"
    count_patterns = re.findall(
        r"\b(\d+)\s+(?:dedicated\s+)?(?:x\s+)?"
        r"((?:youtube|instagram|tiktok|blog|video|reel|story|short|post)\w*"
        r"(?:\s+\w+){0,3})",
        text, re.IGNORECASE,
    )
    for count, desc in count_patterns:
        deliverables.append(f"{count} {desc.strip()}")

    # Pattern: "45-second integrated sponsorship slot", "60s integration"
    duration_patterns = re.findall(
        r"\b(\d+[\s-]*(?:second|minute|sec|min)s?\s+(?:integrated|dedicated)?\s*(?:sponsorship\s+)?(?:slot|integration|video|placement|mention))",
        text, re.IGNORECASE,
    )
    for desc in duration_patterns:
        deliverables.append(f"1x {desc.strip()}")
        
    # Pattern: "a dedicated youtube video", "one instagram reel"
    text_count_patterns = re.findall(
        r"\b(?:a|an|one)\s+((?:dedicated\s+)?(?:youtube\s+|instagram\s+|tiktok\s+)?(?:video|reel|story|post|integration|slot))",
        text, re.IGNORECASE,
    )
    for desc in text_count_patterns:
        # Don't add if it's too generic or already covered
        if len(desc) > 4 and not any(desc.lower() in d.lower() for d in deliverables):
            deliverables.append(f"1x {desc.strip().title()}")

    return deliverables if deliverables else ["Deliverables not specified"]


def _extract_deadline(text: str) -> Optional[str]:
    """
    Extract a deadline or timeline from the email text.

    Args:
        text: Raw email text.

    Returns:
        str or None: Extracted deadline string.
    """
    # Common patterns: "by August 15th", "deadline: July 1", "before Sept 2026"
    patterns = [
        r"(?:by|before|deadline[:\s]*|timeline[:\s]*|due[:\s]*)\s*"
        r"([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:[,\s]+\d{4})?)",
        r"(?:live by|content.+?by)\s*([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_requirements(text: str) -> list[str]:
    """
    Extract specific brand requirements (must-mention, show product, etc.).

    Args:
        text: Raw email text.

    Returns:
        list[str]: Extracted requirement strings.
    """
    requirements = []

    # "Must mention X", "must include X", "required: X"
    must_patterns = re.findall(
        r"(?:must|required?|need to|should)\s+(\w[\w\s]{5,60})",
        text, re.IGNORECASE,
    )
    for req in must_patterns:
        clean = req.strip().rstrip(".")
        if clean:
            requirements.append(clean)

    return requirements if requirements else ["No specific requirements stated"]


def _extract_summary(text: str) -> str:
    """
    Extract a meaningful TL;DR summary from the email by prioritizing key sentences.
    """
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    
    # Filter out common headers, greetings, and short meaningless lines
    content_lines = []
    for line in lines:
        if re.match(r"^(From:|Subject:|Hi |Hello |Dear |Best,|Thanks,|Cheers,|Hope you|Hope this)", line, re.IGNORECASE):
            continue
        if len(line) > 20 and not line.startswith(">"):
            content_lines.append(line)
            
    if not content_lines:
        return "No clear summary available."
        
    # Join into a single block
    full_text = " ".join(content_lines)
    
    # Split into sentences using a simple regex keeping punctuation
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_text) if s.strip()]
    
    if not sentences:
        sentences = [full_text]
        
    # Keywords that indicate the main point of the email
    key_terms = [
        "sponsor", "partner", "collab", "budget", "rate", "deliverables",
        "offer", "campaign", "interested in", "reach out", "would love", "gift",
        "barter", "pr package", "fan", "inspire", "love your"
    ]
    
    summary_sentences = []
    for s in sentences:
        if any(term in s.lower() for term in key_terms):
            summary_sentences.append(s)
            if len(summary_sentences) == 2:
                break
                
    # Fallback to the first 1-2 sentences if no key terms found
    if not summary_sentences:
        summary_sentences = sentences[:2]
        
    summary_text = " ".join(summary_sentences)
    
    if len(summary_text) > 250:
        summary_text = summary_text[:247] + "..."
        
    return summary_text


def _extract_provided_script(text: str) -> Optional[str]:
    """
    Extract any provided script or talking points from the brand.
    """
    patterns = [
        r"(?:Script|Talking points|What to say|Draft script)[:\s\-]+(.+?)(?:\n\n|\Z)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            script_content = match.group(1).strip()
            if len(script_content) > 30:
                return script_content
    return None


def _extract_all_dates(text: str) -> list[str]:
    """
    Extract all dates mentioned in the email for calendar linking.
    """
    dates = []
    # Match dates like August 15th, Aug 12, Sept 1, 2026
    matches = re.findall(r"([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:[,\s]+\d{4})?)", text)
    for m in matches:
        if m not in dates:
            dates.append(m)
    return dates


# ──────────────────────────────────────────────────────────────────────────────
# Core Classification Logic
# ──────────────────────────────────────────────────────────────────────────────

def _score_category(text: str, keywords: list[str]) -> float:
    """
    Calculate a confidence score for a category based on keyword matches.

    Uses position-weighted scoring — keywords listed earlier in the
    keyword list contribute slightly more to the score.

    Args:
        text:     Lowercase email text.
        keywords: List of keywords for one category.

    Returns:
        float: Score between 0.0 and 1.0.
    """
    text_lower = text.lower()
    total_weight = 0.0
    matched_weight = 0.0

    for i, keyword in enumerate(keywords):
        # Earlier keywords get higher weight (1.0 down to 0.5)
        weight = 1.0 - (i / (2 * len(keywords)))
        total_weight += weight

        if keyword.lower() in text_lower:
            matched_weight += weight

    return matched_weight / total_weight if total_weight > 0 else 0.0


def classify(email_text: str) -> dict:
    """
    Classify an email into BRAND_DEAL, FAN_MAIL, or SPAM.

    This is the main entry point for the Triage Agent. It reads the raw
    email text, scores it against all three category keyword sets, and
    returns a structured result with metadata extraction.

    Args:
        email_text: Raw text content of the email.

    Returns:
        dict: Classification result:
            {
                "classification": "BRAND_DEAL" | "FAN_MAIL" | "SPAM",
                "confidence": 0.0–1.0,
                "sender": "Sarah Chen <partnerships@glowskin.co>",
                "subject": "Paid Collaboration – ...",
                "extracted_requirements": {
                    "deliverables": [...],
                    "budget_offered": 800,
                    "deadline": "August 15th",
                    "key_requirements": [...]
                },
                "raw_text": "..."
            }
    """
    _log("Analyzing email content...")

    # ── Score each category ──────────────────────────────────────────────
    brand_score = _score_category(email_text, BRAND_KEYWORDS)
    fan_score = _score_category(email_text, FAN_KEYWORDS)
    spam_score = _score_category(email_text, SPAM_KEYWORDS)
    personal_score = _score_category(email_text, PERSONAL_KEYWORDS)
    pr_score = _score_category(email_text, PR_KEYWORDS)
    barter_score = _score_category(email_text, BARTER_KEYWORDS)

    _log(
        f"Scores → Brand: {brand_score:.2f}  "
        f"Fan: {fan_score:.2f}  "
        f"Spam: {spam_score:.2f}  "
        f"Personal: {personal_score:.2f}  "
        f"PR: {pr_score:.2f}  "
        f"Barter: {barter_score:.2f}"
    )

    # ── Determine winner ─────────────────────────────────────────────────
    scores = {
        "BRAND_DEAL": brand_score,
        "FAN_MAIL": fan_score,
        "SPAM": spam_score,
        "PERSONAL": personal_score,
        "PR_PACKAGE": pr_score,
        "BARTER_DEAL": barter_score,
    }
    classification = max(scores, key=scores.get)
    confidence = scores[classification]

    # Minimum confidence threshold — if nothing matches well, default to SPAM
    if confidence < 0.1:
        classification = "SPAM"
        confidence = 0.5
        _log("Low confidence across all categories — defaulting to SPAM")

    # ── Extract metadata ─────────────────────────────────────────────────
    sender = _extract_sender(email_text)
    subject = _extract_subject(email_text)

    _log(f"Classification: {_BOLD}{classification}{_RESET} ({confidence:.0%} confidence)")
    _log(f"Sender: {sender}")
    _log(f"Subject: {subject}")

    # ── Build result ─────────────────────────────────────────────────────
    summary = _extract_summary(email_text)
    
    result = {
        "classification": classification,
        "confidence": round(confidence, 2),
        "sender": sender,
        "subject": subject,
        "summary": summary,
        "raw_text": email_text,
    }

    # Add detailed extraction only for brand deals
    # Add detailed extraction for relevant deal types
    if classification in ("BRAND_DEAL", "PR_PACKAGE", "BARTER_DEAL"):
        budget = _extract_budget(email_text)
        deliverables = _extract_deliverables(email_text)
        deadline = _extract_deadline(email_text)
        requirements = _extract_requirements(email_text)
        provided_script = _extract_provided_script(email_text)
        extra_dates = _extract_all_dates(email_text)
        
        # Remove the main deadline from extra dates if present
        if deadline and deadline in extra_dates:
            extra_dates.remove(deadline)

        result["extracted_requirements"] = {
            "deliverables": deliverables,
            "budget_offered": budget,
            "deadline": deadline,
            "key_requirements": requirements,
            "provided_script": provided_script,
            "extra_dates": extra_dates,
        }

        _log(f"Budget offered: ${budget}" if budget else "Budget: not specified")
        _log(f"Deliverables: {len(deliverables)} item(s)")
        _log(f"Deadline: {deadline or 'not specified'}")
        if provided_script:
            _log("Found brand-provided script/talking points")
        if extra_dates:
            _log(f"Found {len(extra_dates)} additional date(s) for calendar")

    return result
