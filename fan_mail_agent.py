"""
fan_mail_agent.py — Fan Mail Reply Agent.

Takes the triage result for a FAN_MAIL email and generates a personalized,
appreciative reply to the fan.
"""

from __future__ import annotations

import textwrap
from datetime import datetime

import config


# ──────────────────────────────────────────────────────────────────────────────
# Console Styling
# ──────────────────────────────────────────────────────────────────────────────

_GREEN = "\033[92m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _log(msg: str) -> None:
    """Print a timestamped fan mail agent log message."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Email Draft Generator
# ──────────────────────────────────────────────────────────────────────────────

def _detect_intent(text: str) -> str:
    """Detect if the fan mail is asking a question, mentioning an event, or just a compliment."""
    text_lower = text.lower()
    
    if "?" in text or any(q in text_lower for q in ["how did you", "what is your", "advice", "help me", "tips"]):
        return "question"
        
    if any(e in text_lower for e in ["meet", "event", "coming to", "visit", "see you at", "conference"]):
        return "event"
        
    return "compliment"


def draft_reply(triage_result: dict, feedback: str = None) -> dict:
    """
    Draft a personalized reply to a fan email.

    Args:
        triage_result: Output dict from triage_agent.classify().

    Returns:
        dict: Result containing the drafted email:
            {
                "fan_email_draft": "Subject: Re: ...\n..."
            }
    """
    _log("Starting fan mail reply pipeline...")

    sender = triage_result.get("sender", "Supporter")
    subject = triage_result.get("subject", "Your Message")
    raw_text = triage_result.get("raw_text", "")

    # Extract sender's first name for greeting
    sender_name = sender.split()[0] if sender != "Unknown Sender" else "there"

    intent = _detect_intent(raw_text)
    _log(f"Detected fan intent: {_BOLD}{intent.upper()}{_RESET}")
    _log(f"Drafting personalized reply to {sender_name}...")

    tone = config.CREATOR_STYLE.get("tone", "authentic")
    
    if "sarcastic" in tone:
        if intent == "question":
            body = "Thanks for the question! Honestly, my best advice is to just start making stuff. Don't worry if it's terrible at first—we all start somewhere.\n\nKeep at it, eventually you'll be less terrible!"
        elif intent == "event":
            body = "Appreciate the message! I might leave my house for a meetup eventually, so keep an eye on the community tab.\n\nThanks for not being a weirdo and supporting the channel."
        else:
            body = "Thanks for reaching out! I usually ignore my inbox, but your message was actually nice. Glad you're enjoying the chaos.\n\nStay awesome."
            
    elif "cozy" in tone or "calm" in tone:
        if intent == "question":
            body = "Thank you so much for your thoughtful question. My biggest piece of advice is to be gentle with yourself and just begin. Consistency is key, and the rest will naturally fall into place.\n\nSending good energy your way!"
        elif intent == "event":
            body = "Thank you for the sweet message! I'd love to organize a cozy little meetup soon. I'll post updates on the community tab when the time is right.\n\nTake care and stay warm."
        else:
            body = "Thank you so much for your kind words. It brings me so much peace knowing the content resonates with you.\n\nRemember to take time for yourself today."
            
    elif "high-energy" in tone or "hype" in tone:
        if intent == "question":
            body = "YO! Thanks for the question! The secret is to JUST START! Grind it out, stay consistent, and don't let anyone stop you!\n\nYou got this!!"
        elif intent == "event":
            body = "LET'S GOOO! Thanks for the hype! We are definitely doing a massive meetup soon, stay tuned to the community tab because it's going to be insane!\n\nAppreciate the support!"
        else:
            body = "THANK YOU! You guys are the absolute best! Hearing this fires me up to make even better videos for you all!\n\nKeep crushing it!"
            
    elif "professional" in tone:
        if intent == "question":
            body = "Thank you for reaching out with your question. I highly recommend focusing on consistent, high-quality output. The learning curve is steep, but persistence pays off.\n\nBest of luck with your endeavors."
        elif intent == "event":
            body = "Thank you for your message. I am currently reviewing my schedule for upcoming conferences and events. Any public appearances will be announced on my channel.\n\nI appreciate your continued interest."
        else:
            body = "Thank you for the message. I greatly appreciate the positive feedback from my audience, and it helps me tailor future educational content.\n\nRegards."
            
    else: # Default authentic
        if intent == "question":
            body = "Thank you so much for reaching out and for your thoughtful question! My best advice is to just start creating. Don't worry about being perfect right away—focus on consistency.\n\nI hope that helps, and I'm rooting for you!"
        elif intent == "event":
            body = "Thank you so much for the message! It's always amazing to hear from people who watch the channel. I'm hoping to do more meetups soon, so keep an eye on my community tab!\n\nThanks again for your incredible support."
        else:
            body = "Thank you so much for reaching out! It really means a lot to hear from people who enjoy the content. Your support is what keeps this channel going.\n\nKeep pursuing your own passions!"

    # Use the creator's dynamic email signoff (not the video outro)
    outro = config.CREATOR_STYLE.get("email_signoff", "Best,")

    email_draft = textwrap.dedent(f"""\
        Subject: Re: {subject}

        Hi {sender_name},

        {body}

        {outro}
        {config.CREATOR_NAME}
    """)
    
    if feedback:
        email_draft += f"\n\n        [Note: Revised based on feedback: '{feedback}']\n"

    _log("Email draft: READY ✓")

    return {
        "fan_email_draft": email_draft.strip(),
    }
