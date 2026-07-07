"""
creative_agent.py — Creative Director Agent.

Takes the brand brief from the Negotiator Agent and generates an engaging
short-form video script customized to the creator's style.

Script Structure:
    📌 HOOK      (0:00 – 0:05)  — Attention-grabbing opener
    📝 BODY      (0:05 – 0:30)  — Value-first content
    🎯 SPONSOR   (0:30 – 0:45)  — Natural product integration
    🔚 OUTRO     (0:45 – 0:60)  — CTA + engagement prompt

Improvisation Engine:
    If the brand's brief is basic (< 3 requirements), the agent
    automatically improvises creative angles and plot hooks to make
    the content more engaging. It selects from a pool of proven
    content formats matched to the brand category.
"""

from __future__ import annotations

import random
import textwrap
from datetime import datetime

# Project imports
import config


# ──────────────────────────────────────────────────────────────────────────────
# Console Styling
# ──────────────────────────────────────────────────────────────────────────────

_MAGENTA = "\033[95m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _log(msg: str) -> None:
    """Print a timestamped creative agent log message."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Creative Angle Database
# ──────────────────────────────────────────────────────────────────────────────

# Pool of proven content angles/formats. Each has a name, description,
# hook template, and a list of matching brand categories.

CREATIVE_ANGLES = [
    {
        "name": "Myth-Busting Review",
        "description": "Debunk common myths about the product category, then reveal the truth",
        "hook_template": "Everyone thinks {category} is {myth}... but here's what they don't tell you 👀",
        "matching_categories": ["skincare", "beauty", "health", "tech", "fitness"],
        "visual_cues": ["dramatic reveal transition", "split-screen comparison", "text overlay with ❌/✅"],
    },
    {
        "name": "Day-in-My-Life Integration",
        "description": "Seamlessly weave the product into a morning/evening routine vlog",
        "hook_template": "My {time_of_day} routine just got a MAJOR upgrade ✨",
        "matching_categories": ["skincare", "beauty", "lifestyle", "food", "wellness"],
        "visual_cues": ["soft morning lighting", "cozy aesthetic", "ASMR-style product shots"],
    },
    {
        "name": "Before/After Transformation",
        "description": "Show a dramatic before/after using the product over time",
        "hook_template": "I used {product} for 2 weeks straight. The results? 🤯",
        "matching_categories": ["skincare", "beauty", "fitness", "home", "tech"],
        "visual_cues": ["timelapse", "side-by-side comparison", "close-up detail shots"],
    },
    {
        "name": "Unpopular Opinion Take",
        "description": "Start with a controversial take that hooks viewers into watching",
        "hook_template": "Hot take: most {category} products are a SCAM. But this one? Different. 🔥",
        "matching_categories": ["tech", "skincare", "beauty", "gadgets", "finance"],
        "visual_cues": ["direct-to-camera, no cuts", "dramatic pause", "opinion text overlay"],
    },
    {
        "name": "Challenge Format",
        "description": "Turn the product review into a fun challenge or experiment",
        "hook_template": "I challenged myself to only use {product} for a WEEK. Here's what happened...",
        "matching_categories": ["food", "tech", "fitness", "lifestyle", "beauty"],
        "visual_cues": ["day counter overlay", "reaction shots", "progress montage"],
    },
    {
        "name": "Honest First Impressions",
        "description": "Unbox and react to the product live — raw, unscripted first impressions",
        "hook_template": "They sent me {product} and I've NEVER seen anything like this before...",
        "matching_categories": ["tech", "gadgets", "beauty", "fashion", "gaming"],
        "visual_cues": ["unboxing close-ups", "genuine reaction shots", "handheld camera feel"],
    },
    {
        "name": "Story Time + Product Tie-In",
        "description": "Tell a personal story that naturally leads into why the product matters",
        "hook_template": "Story time: last month something happened that completely changed how I think about {category}...",
        "matching_categories": ["skincare", "health", "wellness", "finance", "education"],
        "visual_cues": ["talking head with b-roll cutaways", "emotional music bed", "text captions"],
    },
    {
        "name": "Top 3 Reasons Format",
        "description": "Rapid-fire listicle format — 3 reasons why this product stands out",
        "hook_template": "3 reasons why {product} is the ONLY {category} product worth buying right now ⬇️",
        "matching_categories": ["tech", "gadgets", "skincare", "beauty", "fitness", "food"],
        "visual_cues": ["number graphics (1, 2, 3)", "quick cuts between demos", "product B-roll"],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Angle Selection Logic
# ──────────────────────────────────────────────────────────────────────────────

def _detect_brand_category(brand_brief: dict) -> str:
    """
    Infer the brand's product category from the brief text.

    Uses keyword matching against the raw email text and brand name
    to determine the most likely category.

    Args:
        brand_brief: Brand brief dict from the Negotiator Agent.

    Returns:
        str: Detected category (e.g., "skincare", "tech").
    """
    text = (
        brand_brief.get("raw_text", "")
        + " "
        + brand_brief.get("brand_name", "")
        + " "
        + brand_brief.get("subject", "")
    ).lower()

    category_keywords = {
        "skincare": ["skin", "serum", "moistur", "spf", "derma", "glow", "vitamin c", "retinol"],
        "beauty": ["makeup", "cosmetic", "lipstick", "foundation", "mascara", "beauty"],
        "tech": ["tech", "gadget", "software", "app", "device", "phone", "laptop"],
        "fitness": ["fitness", "gym", "workout", "protein", "supplement", "exercise"],
        "food": ["food", "recipe", "cook", "meal", "snack", "restaurant", "drink"],
        "fashion": ["fashion", "clothing", "wear", "style", "outfit", "apparel"],
        "gaming": ["gaming", "game", "console", "pc", "esport"],
        "lifestyle": ["lifestyle", "home", "decor", "wellness", "travel"],
    }

    scores = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score

    if scores:
        best = max(scores, key=scores.get)
        _log(f"Detected brand category: {_BOLD}{best}{_RESET}")
        return best

    _log("Could not detect category — using 'lifestyle' as default")
    return "lifestyle"


def _select_angle(category: str, brand_brief: dict) -> dict:
    """
    Select the best creative angle for this brand + category combo.

    Prioritizes angles from the creator's preferred list (config.CREATOR_STYLE),
    then falls back to category-matched angles from the pool.

    Args:
        category:    Detected brand category.
        brand_brief: Brand brief dict.

    Returns:
        dict: Selected angle from CREATIVE_ANGLES.
    """
    # Filter angles that match the category
    matching = [
        a for a in CREATIVE_ANGLES
        if category in a["matching_categories"]
    ]

    if not matching:
        matching = CREATIVE_ANGLES  # Fallback to full pool

    # Prefer creator's preferred angles (from config)
    preferred = config.CREATOR_STYLE.get("preferred_angles", [])
    for angle in matching:
        for pref in preferred:
            if pref.lower() in angle["name"].lower():
                _log(f"Selected angle: {_BOLD}{angle['name']}{_RESET} (creator preference match)")
                return angle

    # Random selection from matching pool
    selected = random.choice(matching)
    _log(f"Selected angle: {_BOLD}{selected['name']}{_RESET} (best category match)")
    return selected


# ──────────────────────────────────────────────────────────────────────────────
# Script Generation
# ──────────────────────────────────────────────────────────────────────────────

def _generate_hook(angle: dict, brand_brief: dict, category: str) -> str:
    """Generate the attention-grabbing hook section (0:00–0:05)."""
    product = brand_brief.get("brand_name", "this product")
    template = angle["hook_template"]

    # Fill in template variables
    hook = template.format(
        product=product,
        category=category,
        myth="just marketing hype",
        time_of_day="morning",
    )

    return hook


def _generate_body(angle: dict, brand_brief: dict, category: str) -> str:
    """Generate the value-first body section (0:05–0:30)."""
    brand_name = brand_brief.get("brand_name", "this brand")

    bodies = {
        "Myth-Busting Review": (
            f"So I've been testing {brand_name}'s product for the past week, and\n"
            f"     I need to set the record straight on some things. First — the\n"
            f"     ingredients. Most people don't realize that {category} products\n"
            f"     need to be formulated a specific way to actually work. Let me\n"
            f"     break down what I found..."
        ),
        "Day-in-My-Life Integration": (
            f"It's 7 AM, alarm just went off — and honestly? The first thing I\n"
            f"     reach for now is {brand_name}. Let me walk you through why it's\n"
            f"     become a non-negotiable part of my routine and how it fits into\n"
            f"     everything I do throughout the day..."
        ),
        "Before/After Transformation": (
            f"Okay so here's where I started — and look, I'm not going to sugarcoat\n"
            f"     it. But after consistently using {brand_name}, the difference is\n"
            f"     actually wild. Let me show you the progression day by day..."
        ),
    }

    # Get specific body or generate a generic one
    body = bodies.get(
        angle["name"],
        f"Here's the thing about {brand_name} that nobody's talking about — \n"
        f"     I've spent the last week putting it through real-world tests, and\n"
        f"     the results genuinely surprised me. Let me show you exactly what\n"
        f"     I mean with some side-by-side comparisons..."
    )

    return body


def _generate_sponsor_segment(brand_brief: dict) -> str:
    """Generate the sponsor integration section (0:30–0:45)."""
    brand_name = brand_brief.get("brand_name", "our sponsor")
    requirements = brand_brief.get("key_requirements", [])

    # Build requirement integrations
    req_lines = []
    for req in requirements:
        # Clean up the requirement and make it conversational
        clean = req.strip().rstrip(".")
        req_lines.append(f"     [Naturally mention: \"{clean}\"]")

    req_block = "\n".join(req_lines) if req_lines else "     [Integrate key product benefits naturally]"

    segment = (
        f"Now, huge shoutout to {brand_name} for making this video possible.\n"
        f"     And honestly? I wouldn't partner with them if I didn't genuinely\n"
        f"     rate the product. Here's what makes it stand out —\n"
        f"{req_block}\n"
        f"     [Show product on screen — hold for 10 seconds with B-roll]\n"
        f"     Link's in the description if you want to check it out!"
    )

    return segment


def _generate_outro(platforms: list[str]) -> str:
    """Generate the outro section (0:45–0:60)."""
    style = config.CREATOR_STYLE
    
    # Customize CTA based on platforms
    ctas = []
    if "YouTube" in platforms:
        ctas.append("Hit that subscribe button and like this video")
    if "Instagram" in platforms:
        ctas.append("Save this reel and share it with a friend")
    if "TikTok" in platforms:
        ctas.append("Follow for more and drop a comment below")
        
    if not ctas:
        ctas.append("Hit that subscribe button if you're new")
        
    cta = " — and ".join(ctas) + "!"
    
    outro = (
        f"{style['signature_outro']}\n"
        f"     {cta}\n"
        f"     See you in the next one! ✌️"
    )
    return outro


def _improvise_if_sparse(brand_brief: dict, angle: dict) -> list[str]:
    """
    Auto-improvise creative additions if the brand brief is too sparse.

    If the brand provides fewer than 3 requirements, this adds improvised
    creative suggestions to make the content more engaging.

    Args:
        brand_brief: Brand brief dict.
        angle:       Selected creative angle.

    Returns:
        list[str]: Additional creative suggestions.
    """
    requirements = brand_brief.get("key_requirements", [])
    suggestions = []

    if len(requirements) < 3:
        _log("Brief is sparse — improvising additional creative hooks...")

        improvisations = [
            "Add a personal anecdote about why this product category matters to you",
            "Include a quick 'expectation vs reality' comparison moment",
            "Film a genuine reaction shot when first using the product",
            "Add a poll/question sticker for Instagram Stories to boost engagement",
            "Include a 'the one thing I wish I knew earlier' revelation moment",
            "Show a quick comparison with a competitor (without naming them)",
            "End with a cliffhanger for a potential follow-up video",
        ]

        # Pick 2-3 improvised additions
        num_additions = min(3, len(improvisations))
        suggestions = random.sample(improvisations, num_additions)

        for s in suggestions:
            _log(f"  + Improvised: {s}")

    return suggestions


# ──────────────────────────────────────────────────────────────────────────────
# Trend Engine
# ──────────────────────────────────────────────────────────────────────────────

def _get_current_trends(platforms: list[str]) -> str:
    """Simulate fetching live trends for specific platforms."""
    now = datetime.now()
    
    platform_trends = {
        "YouTube": [
            "Long-form documentary style intro",
            "Fast-paced MrBeast style editing",
            "Cozy aesthetic vlog with text overlay",
            "Direct-to-camera with jump cuts"
        ],
        "Instagram": [
            "Trending Audio: 'I'm just a girl' style meme",
            "Aesthetic POV with lo-fi beats",
            "Quick transition 'Get Ready With Me'",
            "Carousel-style info dump hook"
        ],
        "TikTok": [
            "Storytime while doing makeup/skincare",
            "Unpopular opinion stitch format",
            "3 reasons why you NEED this",
            "Aggressive hook with fast cuts"
        ]
    }
    
    trends = []
    for plat in platforms:
        if plat in platform_trends:
            # Pick a deterministic trend based on the month to simulate "current"
            idx = now.month % len(platform_trends[plat])
            trends.append(f"[{plat}] {platform_trends[plat][idx]}")
            
    trend_str = " | ".join(trends) if trends else "Fast-paced ASMR with text overlay"
    _log(f"Live Trends detected: {_BOLD}{trend_str}{_RESET}")
    return trend_str


# ──────────────────────────────────────────────────────────────────────────────
# Main Agent Entry Point
# ──────────────────────────────────────────────────────────────────────────────

def generate_script(brand_brief: dict, feedback: str = None) -> str:
    """
    Generate a complete short-form video script from a brand brief.

    This is the main entry point called by the orchestrator. It:
      1. Detects the brand's product category
      2. Selects the optimal creative angle
      3. Generates all four script sections
      4. Improvises additional hooks if the brief is sparse
      5. Formats everything into a presentation-ready script

    Args:
        brand_brief: Brand brief dict from the Negotiator Agent:
            {
                "brand_name": "GlowSkin Co.",
                "deliverables": [...],
                "key_requirements": [...],
                "deadline": "August 15th",
                ...
            }

    Returns:
        str: Fully formatted video script string.
    """
    _log("Starting creative pipeline...")

    brand_name = brand_brief.get("brand_name", "Brand Partner")
    creator = config.CREATOR_NAME

    platforms = brand_brief.get("platforms", ["YouTube"])

    # ── Step 1: Detect category ──────────────────────────────────────────
    category = _detect_brand_category(brand_brief)

    # ── Step 2: Select the creative angle ────────────────────────────────
    # For PR packages, we force the Unboxing format. Otherwise, use heuristics.
    deal_type = brand_brief.get("deal_type", "BRAND_DEAL")
    if deal_type == "PR_PACKAGE":
        # Fallback to Honest First Impressions if Authentic Unboxing/Haul is not present
        angle = next((a for a in CREATIVE_ANGLES if a["name"] == "Authentic Unboxing/Haul"), next(a for a in CREATIVE_ANGLES if a["name"] == "Honest First Impressions"))
        _log("PR Package detected — forcing Unboxing format")
    else:
        angle = _select_angle(category, brand_brief)
        
    # Apply heuristic feedback override for angle
    if feedback:
        if "angle" in feedback.lower() or "format" in feedback.lower():
            available = [a for a in CREATIVE_ANGLES if a["name"] != angle["name"]]
            if available:
                import random
                angle = random.choice(available)
                _log(f"Feedback heuristic: Switched angle to {angle['name']}")
    
    # ── Step 2b: Get Live Trend ──────────────────────────────────────────
    current_trends = _get_current_trends(platforms)

    # ── Step 3: Generate or Extract script sections ──────────────────────
    _log("Generating script sections...")
    
    provided_script = brand_brief.get("provided_script")
    
    if provided_script:
        _log("Found brand-provided script — refining to match creator style...")
        hook = _generate_hook(angle, brand_brief, category)
        
        # Integrate their script into the body but apply our style
        body = (
            f"     [Using brand-provided talking points]\n"
            f"{textwrap.indent(provided_script, '     ')}"
        )
        
        sponsor = _generate_sponsor_segment(brand_brief)
        outro = _generate_outro(platforms)
        extra_suggestions = []
        angle["name"] = "Refined Brand Script"
        angle["description"] = "Using the script provided by the brand, polished for your audience"
    else:
        hook = _generate_hook(angle, brand_brief, category)
        body = _generate_body(angle, brand_brief, category)
        sponsor = _generate_sponsor_segment(brand_brief)
        outro = _generate_outro(platforms)

        # ── Step 4: Improvise if brief is sparse ─────────────────────────────
        extra_suggestions = _improvise_if_sparse(brand_brief, angle)

    if feedback:
        extra_suggestions.append(f"INCORPORATED FEEDBACK: {feedback}")

    # ── Step 5: Format the complete script ───────────────────────────────
    _log("Assembling final script...")

    visual_cues = "\n".join(f"     • {v}" for v in angle["visual_cues"])
    extras = ""
    if extra_suggestions:
        extras_list = "\n".join(f"     • {s}" for s in extra_suggestions)
        extras = f"\n\n  💡 IMPROVISED ADDITIONS:\n{extras_list}"

    deliverables = brand_brief.get("deliverables", ["1 Video"])
    deliverables_str = ", ".join(deliverables[:3])

    title_line = f'🎬  VIDEO SCRIPT — "{brand_name} x {creator}"'
    format_line = f'Format: {deliverables_str} ({", ".join(platforms)})'
    angle_line = f'Angle:  {angle["name"]}'
    tone_line = f'Tone:   {config.CREATOR_STYLE["tone"]}'

    script = f"""\
  {title_line}
  {format_line}
  {angle_line}
  {tone_line}
  
  📈 SOCIAL TRENDS TO HIT: {current_trends}

  📌 HOOK (0:00 – 0:05)
     [{config.CREATOR_STYLE['signature_intro']}]
     {hook}

  📝 BODY (0:05 – 0:30)
     {body}

  🎯 SPONSOR SEGMENT (0:30 – 0:45)
     {sponsor}

  🔚 OUTRO (0:45 – 0:60)
     {outro}

  📊 CREATIVE NOTES:
     • Angle: {angle['name']} — {angle['description']}

  🎥 VISUAL CUES:
{visual_cues}{extras}
"""

    _log(f"Script: READY ✓ ({angle['name']} format)")
    return script
