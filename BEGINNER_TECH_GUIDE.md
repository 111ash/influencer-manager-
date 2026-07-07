# 🧠 Beginner's Tech Guide — Autonomous Creator Studio

**Creator: Ashmita Dhawan**

> **Who is this for?** This guide is for *you* — a beginner who wants to understand
> every piece of technology used in this project. No jargon dumps, no walls of docs.
> Just simple explanations with real-world analogies and exact references to the code
> you can open right now.

---

## Table of Contents

1. [Technology Map: What Is Used Where](#1-technology-map-what-is-used-where)
2. [What is an AI Agent?](#2-what-is-an-ai-agent)
3. [What is the Agent Development Kit (ADK)?](#3-what-is-the-agent-development-kit-adk)
4. [What is the Model Context Protocol (MCP)?](#4-what-is-the-model-context-protocol-mcp)
5. [What is Human-in-the-Loop (HITL)?](#5-what-is-human-in-the-loop-hitl)
6. [How Do the Agents Communicate?](#6-how-do-the-agents-communicate)
7. [Deep Dive: The Triage Agent](#7-deep-dive-the-triage-agent)
8. [Deep Dive: The Negotiator Agent](#8-deep-dive-the-negotiator-agent)
9. [Deep Dive: The MCP Server & Analytics Tool](#9-deep-dive-the-mcp-server--analytics-tool)
10. [Deep Dive: The HITL Gatekeeper](#10-deep-dive-the-hitl-gatekeeper)
11. [Deep Dive: config.py — The Single Source of Truth](#11-deep-dive-configpy--the-single-source-of-truth)
12. [Putting It All Together](#12-putting-it-all-together)
13. [Common Beginner Questions](#13-common-beginner-questions)
14. [Glossary](#14-glossary)

---

## 1. Technology Map: What Is Used Where

This section is your **quick-reference cheat sheet**. Before diving into explanations,
use this map to immediately answer: *"Where is X used?"* or *"What does file Y actually do?"*

---

### 📁 File-by-File Breakdown

| File | Role | Key Python concepts used |
|---|---|---|
| `main.py` | Orchestrator — runs the whole pipeline | `pathlib`, `re`, `sys`, f-strings, `while` loops, `input()` |
| `config.py` | Single source of truth for all settings | `sys`, `pathlib.Path`, `ctypes`, constants, dicts |
| `agents/triage_agent.py` | Classifies emails into categories | `re`, weighted scoring, regex extraction |
| `agents/negotiator_agent.py` | Calculates pricing + drafts counter-offer email | `math`, `re`, `textwrap`, CPM formula, f-strings |
| `agents/creative_agent.py` | Generates branded video scripts | String manipulation, conditional logic, brand detection |
| `agents/fan_mail_agent.py` | Drafts thank-you replies to fan mail | `textwrap`, tone adaptation, string templates |
| `agents/brand_analyst_agent.py` | Onboarding agent that profiles your brand | `input()`, interactive Q&A, config writing |
| `mcp_server/analytics_tool.py` | Simulates YouTube/Instagram analytics API | `random`, `datetime`, `json`, jitter simulation |
| `mcp_server/main.py` | MCP server that registers and exposes tools | Class pattern, tool registry dict, logging |
| `security/hitl_gatekeeper.py` | Human approval gate — blocks pipeline until decision | `input()`, ANSI codes, `textwrap`, `pathlib`, `os` |
| `calendar_utils.py` | Creates `.ics` calendar files + deadline tracker | `datetime`, `json`, `pathlib`, iCalendar format |

---

### 🐍 Python Standard Library — What's Used Where

This project uses **zero third-party pip packages**. Everything below comes with Python.

| Library / Built-in | What it does | Used in |
|---|---|---|
| `re` | Regular expressions — pattern matching in text | `triage_agent.py`, `negotiator_agent.py`, `main.py` |
| `math` | Mathematical functions (`math.ceil` for rounding) | `negotiator_agent.py` |
| `textwrap` | Clean multi-line string indentation + wrapping | `negotiator_agent.py`, `hitl_gatekeeper.py`, `fan_mail_agent.py` |
| `pathlib.Path` | Cross-platform file paths (works on Windows + Mac) | `config.py`, `main.py`, `hitl_gatekeeper.py`, `calendar_utils.py` |
| `datetime` | Date/time objects — timestamps, deadline parsing | `triage_agent.py`, `negotiator_agent.py`, `analytics_tool.py`, `calendar_utils.py` |
| `random` | Random number generation (jitter simulation) | `analytics_tool.py` |
| `json` | Read/write JSON files (deadline tracker storage) | `calendar_utils.py`, `analytics_tool.py` |
| `sys` | System settings — stdout encoding, platform check | `config.py` |
| `os` | OS-level file operations | `hitl_gatekeeper.py` |
| `ctypes` | Low-level Windows API calls (enable ANSI colors) | `config.py` |
| `time` | Pauses/delays between processing steps | `main.py` |
| `typing.Optional` | Type hint for "this might be None" | `triage_agent.py` |
| `from __future__ import annotations` | Enables modern type hints in older Python | Every agent file |
| `input()` | Read text typed by the user in the terminal | `main.py`, `hitl_gatekeeper.py`, `brand_analyst_agent.py` |
| `open()` | Read/write files | `main.py`, `hitl_gatekeeper.py`, `calendar_utils.py` |

---

### 🧠 Concepts & Patterns — What's Used Where

| Concept / Pattern | What it means (one line) | Where it appears |
|---|---|---|
| **ANSI escape codes** | Special strings that color terminal text | `main.py`, all agents, `hitl_gatekeeper.py` |
| **Position-weighted scoring** | Earlier keywords score higher than later ones | `triage_agent.py` → `_score_category()` |
| **CPM pricing formula** | `(views/1000) × CPM × deliverables` | `negotiator_agent.py` → `_calculate_counter_offer()` |
| **Engagement multiplier** | +15% bonus when engagement > 3% | `negotiator_agent.py`, configured in `config.py` |
| **Platform combo premium** | +20% when brand wants 2+ platforms | `negotiator_agent.py`, configured in `config.py` |
| **Counter-offer floor** | Always reply at ≥135% of brand's offer | `negotiator_agent.py`, configured in `config.py` |
| **Jitter simulation** | ±5% random variation on analytics numbers | `mcp_server/analytics_tool.py` → `_jitter()` |
| **MCP tool envelope** | Standard `{tool, status, data}` wrapper | `mcp_server/main.py` → `call_tool()` |
| **Graceful degradation** | Fall back to static config if MCP fails | `negotiator_agent.py` → `negotiate()` |
| **HITL review loop** | Blocks on `input()` until human decides | `security/hitl_gatekeeper.py` → `review()` |
| **Edit feedback loop** | `[E]dit` re-runs pipeline with user's note | `main.py` `while True` loop + `negotiator_agent.py` |
| **Tone switching** | Email style changes based on creator's tone setting | `negotiator_agent.py` → `_draft_counter_email()` |
| **Fail-safe auto-reject** | 3 bad inputs → auto-reject (not auto-approve) | `security/hitl_gatekeeper.py` → `review()` |
| **iCalendar (.ics) format** | Universal calendar file format | `calendar_utils.py` |
| **Underscore prefix `_`** | Marks a function/variable as private to its file | Every file — all helper functions |
| **Single-entry-point pattern** | Each agent has one public function others call | `classify()`, `negotiate()`, `generate_script()` |
| **UTF-16 emoji width trick** | Measures true visual width of emoji in terminal | `hitl_gatekeeper.py` → `_pad_line()` |
| **Regex groups** | Capturing `()` in patterns to extract substrings | `triage_agent.py` — all `_extract_*` functions |
| **f-string format spec `:,`** | Adds comma separators to numbers (`1650` → `1,650`) | `negotiator_agent.py`, `hitl_gatekeeper.py` |
| **`EOFError` catch** | Detects non-interactive environments (no keyboard) | `hitl_gatekeeper.py`, `main.py` |
| **`if __name__ == "__main__"`** | Only runs `main()` when the file is run directly | `main.py` |

---

### 🗂️ Directory Structure at a Glance

```
influencer manager/
│
├── main.py                   ← START HERE — runs the whole pipeline
├── config.py                 ← All settings in one place
├── calendar_utils.py         ← Deadline tracking + .ics generation
├── BEGINNER_TECH_GUIDE.md    ← This file
├── README.md                 ← Setup instructions
│
├── agents/                   ← Each AI agent lives here
│   ├── triage_agent.py       ← Classifies email type
│   ├── negotiator_agent.py   ← Calculates price + drafts reply email
│   ├── creative_agent.py     ← Writes the video script
│   ├── fan_mail_agent.py     ← Replies to fan mail
│   └── brand_analyst_agent.py← Onboarding: profiles your brand
│
├── mcp_server/               ← Simulated analytics API
│   ├── main.py               ← MCP server (registers tools)
│   └── analytics_tool.py     ← The actual tool logic (mock API)
│
├── security/
│   └── hitl_gatekeeper.py    ← Human approval gate
│
├── mock_inbox/               ← Drop .txt email files here to process
│   ├── sample_brand_email.txt
│   └── sample_spam_email.txt
│
├── drafts/                   ← Approved emails + scripts saved here
└── calendar/                 ← .ics calendar files + deadlines.json
```

---

### 🔗 Import Dependency Map

This shows which files import which, so you understand the dependency chain:

```
main.py
  └── imports: config, triage_agent, negotiator_agent,
               creative_agent, fan_mail_agent,
               brand_analyst_agent, hitl_gatekeeper, calendar_utils

negotiator_agent.py
  └── imports: config, mcp_server.main

mcp_server/main.py
  └── imports: config, mcp_server/analytics_tool

mcp_server/analytics_tool.py
  └── imports: config, random, datetime, json

security/hitl_gatekeeper.py
  └── imports: config, calendar_utils

calendar_utils.py
  └── imports: config, datetime, json, pathlib

config.py
  └── imports: sys, pathlib, ctypes  ← No project imports (it's the root)
```

> **Why does everything import `config` first?** Because `config.py` sets up
> Windows UTF-8 encoding and ANSI color support the moment it loads. Every other
> module needs that to be ready before it prints anything.

---

## 1. What is an AI Agent?

### The Simple Analogy: Assistants vs. Calculators

Think of a **regular Python script** like a **calculator**:

- You press buttons → it does *exactly* what you told it → spits out a number.
- It can't decide on its own what to calculate next.
- If something unexpected happens, it just crashes.

Now think of an **AI Agent** like a **personal assistant**:

- You say "Handle my brand emails" → it *figures out the steps* on its own.
- It can **observe** (read your inbox), **think** (classify the email), **decide**
  (is this a brand deal or spam?), and **act** (draft a reply or discard it).
- If something unexpected happens (weird email format), it adapts.

### The Key Differences

| Feature | Regular Script | AI Agent |
|---|---|---|
| **Decision-making** | Hardcoded `if/else` | Reasons about the *best* action |
| **Autonomy** | Follows rigid steps | Can chain actions dynamically |
| **Adaptability** | Breaks on edge cases | Handles uncertainty gracefully |
| **Memory** | None between runs | Can carry context across steps |
| **Goal-oriented** | Executes instructions | Works *towards a goal* |

### In This Project

We have **three agents**, each with a specialized role:

1. **🔀 Triage Agent** — The receptionist. Reads every email and decides: "Is this
   a brand deal, fan mail, or spam?" Lives in `agents/triage_agent.py`.
2. **💰 Negotiator Agent** — The business manager. If it's a brand deal, this agent
   looks up your channel stats and calculates a fair counter-offer price. Lives in
   `agents/negotiator_agent.py`.
3. **🎬 Creative Agent** — The creative director. Takes the brand's requirements and
   writes an engaging video script tailored to your content style.

Each agent **focuses on one job** and does it well — just like employees in a real
talent management company.

### The "Observe → Think → Act" Loop

Every agent in this project follows the same basic pattern:

```
OBSERVE  →  The agent receives an input (email text, triage result, brand brief)
THINK    →  The agent processes it (keyword scoring, pricing math, script generation)
ACT      →  The agent produces an output (dict, email draft, video script)
```

In a production system with a real LLM, the "THINK" step would involve sending a
prompt to GPT-4 / Gemini and parsing the response. In this project, the "THINK"
step is **deterministic code** — keyword matching and math — but the *architecture*
is identical. Swapping in a real LLM only requires changing the `classify()` or
`negotiate()` method internals.

---

## 2. What is the Agent Development Kit (ADK)?

### The Simple Analogy: LEGO Bricks for Agents

Imagine you want to build a house out of LEGO:

- You *could* mold every brick from scratch... but that's insane.
- Instead, you use **pre-made LEGO pieces** that snap together.

The **Agent Development Kit (ADK)** is Google's set of "LEGO pieces" for building
AI agents. It gives you:

- 🧱 **Pre-built agent patterns** — Templates for common agent behaviors
  (classify, generate, negotiate)
- 🔗 **Communication protocols** — How agents pass data to each other
- 🛡️ **Safety guardrails** — Built-in support for human review gates
- 🧪 **Testing tools** — Ways to run your agents locally without real APIs

### In This Project

Our codebase follows the **ADK architecture pattern**, even though we implement
it with pure Python (no external ADK library needed for the local demo):

```
main.py (Orchestrator)
   │
   ├── Routes email → Triage Agent
   │                     │
   │                     ├── BRAND_DEAL → Negotiator Agent
   │                     │                    │
   │                     │                    └── Creative Agent
   │                     │                           │
   │                     │                           └── HITL Gatekeeper
   │                     │
   │                     ├── FAN_MAIL → Log and skip
   │                     └── SPAM → Discard
```

The **ADK philosophy** we follow:

- **Modularity** — Each agent is a separate Python file with one job
- **Composability** — Agents chain together like building blocks
- **Observability** — Every step prints timestamped logs so you can *watch*
  the pipeline think in real time

### What Does "ADK-Compatible" Mean in Practice?

Each agent in this project is written so that you could drop it into a real Google
ADK deployment with minimal changes. The key design decisions that make this work:

1. **Single entry-point function** — Each agent exposes exactly one public function:
   - `triage_agent.classify(email_text)` → returns a dict
   - `negotiator_agent.negotiate(triage_result)` → returns a dict
   - The orchestrator (`main.py`) only calls these public functions, never internal helpers.

2. **No shared global state** — Agents don't write to shared variables. All data
   flows through the return values (dicts). This means agents can run in parallel
   or be swapped out without side effects.

3. **Consistent logging format** — Every agent uses a `_log()` helper that timestamps
   output. In a real ADK deployment, you'd replace this with ADK's built-in tracing.

---

## 3. What is the Model Context Protocol (MCP)?

### The Simple Analogy: USB-C for AI

Remember when every phone had a different charger? Nightmare, right?

Then **USB-C** came along — *one universal connector* that works with everything.

**MCP (Model Context Protocol)** is like **USB-C, but for AI data access**:

- **Before MCP:** Every AI app needs custom code to talk to YouTube Analytics,
  Instagram API, Google Analytics, etc. Each integration is different, fragile,
  and needs separate API keys.

- **After MCP:** There's *one standard protocol*. You build an MCP Server that
  exposes "tools" (like `get_creator_metrics`), and *any* AI agent can use them
  through the same interface.

### Why MCP is Better Than Direct API Calls

| Direct API Calls | MCP Protocol |
|---|---|
| Every agent needs its own API code | Agents call a *universal tool interface* |
| API keys scattered across files | Credentials managed in one place |
| Change the API → rewrite every agent | Change the tool → agents don't notice |
| No logging of data access | Every tool call is automatically logged |
| Tightly coupled | Loosely coupled (swap tools freely) |

### What is FastMCP?

**FastMCP** is a Python framework that makes building MCP servers easy. Think of
it as "Flask/FastAPI, but for MCP tool servers."

In a production system, you'd write:

```python
from fastmcp import FastMCP

mcp = FastMCP("Creator Analytics")

@mcp.tool()
def get_creator_metrics() -> dict:
    """Fetch real-time creator channel metrics."""
    return {"subscribers": 500000, "avg_views": 45000}
```

### In This Project

We simulate the FastMCP pattern with our own lightweight `MCPServer` class:

```
mcp_server/
├── analytics_tool.py    ← The actual tool logic (mock YouTube API)
└── main.py              ← The MCP server that registers + exposes tools
```

**How it works step-by-step:**

1. `analytics_tool.py` defines a function `get_creator_metrics()` that returns
   mock channel analytics (subscribers, views, CPM, etc.)
2. `main.py` creates an `MCPServer` that **registers** this function as a tool
3. When the Negotiator Agent needs analytics, it calls:
   ```python
   mcp_server.call_tool("get_creator_metrics")
   ```
4. The MCP server logs the call, runs the tool, wraps the result in a standard
   envelope, and returns it

**The magic:** If tomorrow you replace the mock with a *real* YouTube API call,
you only change `analytics_tool.py`. The Negotiator Agent doesn't change at all.

---

## 4. What is Human-in-the-Loop (HITL)?

### The Simple Analogy: The "Are You Sure?" Popup

You know that dialog box that says "Are you sure you want to delete this file?"
before permanently erasing something?

**HITL is that concept applied to AI systems.**

AI is powerful, but it makes mistakes. HITL means:

> "The AI does the heavy lifting, but a **human gets the final say** before
> anything important happens."

### Why HITL is a Security Guardrail

Without HITL:
```
Brand email → AI classifies → AI drafts reply → AI SENDS EMAIL 😱
```
*(What if it misclassified? What if the counter-offer is wrong? What if the
script is off-brand? Too late — it's already sent!)*

With HITL:
```
Brand email → AI classifies → AI drafts reply → ⏸️ HUMAN REVIEWS → ✅ Approved → Saved
```
*(You see everything before anything leaves the system. Full control.)*

### HITL in the Real World

| System | Without HITL (Scary) | With HITL (Safe) |
|---|---|---|
| Email AI | Auto-sends replies to brands | Shows draft, asks you to approve |
| Self-driving car | Makes all decisions alone | Alerts driver in tricky spots |
| Medical AI | Auto-prescribes medication | Suggests diagnosis, doctor confirms |
| Trading AI | Auto-executes large trades | Proposes trade, trader approves |

### In This Project

Our HITL gate (`security/hitl_gatekeeper.py`) works like this:

1. 🚫 **STOPS** the entire pipeline
2. 📧 **Shows** you the drafted negotiation email
3. 🎬 **Shows** you the generated video script
4. ❓ **Asks** you: `[A]pprove and save draft, [E]dit, or [R]eject?`
5. ⏳ **Waits** — literally `input()` — the program freezes until you type

**Only after you type `A`** does it save anything to disk. If you type `R`, everything
is thrown away. No emails sent, no scripts published, nothing happens without your
explicit approval.

---

## 5. How Do the Agents Communicate?

### The Simple Analogy: An Assembly Line

Think of a car factory assembly line:

1. **Station 1** (Welding) → takes raw metal, welds the frame, passes it to →
2. **Station 2** (Painting) → paints the frame, passes it to →
3. **Station 3** (Assembly) → adds wheels and engine, passes it to →
4. **Station 4** (Quality Check) → a human inspector approves or rejects the car

Each station **doesn't care** what the other stations do internally. They just:

- **Receive** a standardized input (the car-in-progress)
- **Do their job** on it
- **Pass** a standardized output to the next station

### In This Project — The Agent "Handshake"

Our agents communicate through **Python dictionaries** passed along the chain:

```
📬 Email Text (string)
      │
      ▼
🔀 Triage Agent
      │ Returns: { classification, confidence, sender, extracted_requirements }
      │
      ▼
💰 Negotiator Agent
      │ Receives: triage_result dict
      │ Calls: MCP Server → get_creator_metrics()
      │ Returns: { counter_offer, email_draft, brand_brief }
      │
      ▼
🎬 Creative Agent
      │ Receives: brand_brief dict (from Negotiator)
      │ Returns: video_script (string)
      │
      ▼
🛡️ HITL Gatekeeper
      │ Receives: email_draft + video_script + metadata
      │ Returns: { decision: approved/rejected, draft_path }
```

### The Data Flow in Code

```python
# Step 1: Triage
triage_result = triage_agent.classify(email_text)
# → {"classification": "BRAND_DEAL", "confidence": 0.85, "sender": "...", ...}

# Step 2: Negotiate (only if BRAND_DEAL)
negotiation_result = negotiator_agent.negotiate(triage_result)
# → {"counter_offer_amount": 1650, "negotiation_email_draft": "...", "brand_brief": {...}}

# Step 3: Creative
video_script = creative_agent.generate_script(negotiation_result["brand_brief"])
# → "📌 HOOK (0:00–0:05)\n  Everyone thinks skincare is just marketing hype..."

# Step 4: Human Review
review = hitl_gatekeeper.review(
    email_draft=negotiation_result["negotiation_email_draft"],
    video_script=video_script,
    metadata=triage_result,
)
# → {"decision": "approved", "draft_path": "drafts/2026-06-25_Sarah_Chen.txt"}
```

### Why Dicts? (Not Classes or Databases)

For a beginner project, Python dicts are the simplest way to pass structured data:

- ✅ No imports needed
- ✅ Easy to print and debug (`print(result)`)
- ✅ JSON-compatible (for future API integration)
- ✅ Every agent's input/output is just a dictionary

In a production system, you'd use **Pydantic models** or **dataclasses** for type
safety. But dicts work perfectly for learning and demonstration.

---

## 6. Deep Dive: The Triage Agent

> **File:** `agents/triage_agent.py`  
> **Job:** Read an email → classify it → extract structured metadata

### Step 1: Keyword Lists

The first thing in the file is a set of **keyword lists**, one per category:

```python
BRAND_KEYWORDS = [
    "partnership", "collaboration", "sponsor", "budget", "campaign",
    "rate card", "paid", "deliverables", "flat fee", "integration", ...
]

FAN_KEYWORDS = [
    "love your", "fan", "inspired", "big fan", "amazing content", ...
]

SPAM_KEYWORDS = [
    "congratulations", "won", "click here", "lottery", "free",
    "act now", "prize", "winner", "banking details", "urgent", ...
]
```

The agent also has two *extra* categories beyond the basic three:

- **`PERSONAL_KEYWORDS`** — Detects personal emails ("dinner", "birthday", "family")
  so the AI doesn't accidentally try to negotiate a brand deal with your mom.
- **`PR_KEYWORDS`** — Detects PR gifting emails ("pr package", "gifted",
  "no obligation") which are different from paid brand deals.
- **`BARTER_KEYWORDS`** — Detects unpaid collabs ("barter", "in exchange for",
  "product in exchange").

> **Why order matters:** Keywords earlier in the list get *slightly higher weight*
> in the scoring algorithm. The most important/definitive keywords go first.

### Step 2: Position-Weighted Scoring

This is the heart of the Triage Agent. Instead of just counting keyword matches,
it uses **position-weighted scoring**:

```python
def _score_category(text: str, keywords: list[str]) -> float:
    for i, keyword in enumerate(keywords):
        # Earlier keywords get higher weight (1.0 down to 0.5)
        weight = 1.0 - (i / (2 * len(keywords)))
        total_weight += weight
        if keyword.lower() in text_lower:
            matched_weight += weight
    return matched_weight / total_weight
```

**How the math works (example with 4 keywords):**

| Position | Keyword | Weight |
|---|---|---|
| 0 (first) | "partnership" | 1.00 |
| 1 | "sponsor" | 0.875 |
| 2 | "budget" | 0.75 |
| 3 (last) | "paid" | 0.625 |

If an email contains "sponsor" and "budget" but not "partnership" or "paid":
- `matched_weight` = 0.875 + 0.75 = 1.625
- `total_weight` = 1.00 + 0.875 + 0.75 + 0.625 = 3.25
- Score = 1.625 / 3.25 = **0.50** (50% confidence)

The category with the **highest score wins**, and if no category scores above
`0.1`, it defaults to SPAM as a fail-safe.

### Step 3: Metadata Extraction

For `BRAND_DEAL`, `PR_PACKAGE`, and `BARTER_DEAL` emails, the agent runs a
second pass of **regex-based extraction** to pull out structured data:

#### Budget Extraction
```python
def _extract_budget(text: str) -> Optional[int]:
    matches = re.findall(r"\$\s*([\d,]+)", text)
    for raw in matches:
        amount = int(raw.replace(",", ""))
        if 50 <= amount <= 50_000:  # Sanity check
            return amount
```
Finds `$800`, `$1,200`, `$10,000` etc. Ignores scam-sized numbers > $50k.

#### Deliverables Extraction
The agent uses **4 different regex patterns** to catch deliverables written in
any style an actual brand manager might use:

1. **Bullet points:** Lines starting with `•`, `-`, or `*`
   → `"• 1x Dedicated YouTube Video"`
2. **Count patterns:** `"2 Instagram Reels"`, `"3x TikTok posts"`
3. **Duration patterns:** `"45-second integrated sponsorship slot"`
4. **Written-out counts:** `"a dedicated YouTube video"`, `"one Instagram Reel"`

#### Deadline Extraction
```python
patterns = [
    r"(?:by|before|deadline[:\s]*|timeline[:\s]*)([A-Z][a-z]+ \d{1,2}...)",
    r"(?:live by|content.+?by)\s*([A-Z][a-z]+ \d{1,2}...)",
]
```
Catches phrases like "by August 15th", "deadline: July 1", "content live before Sept 2026".

#### The Final Output Dict

```python
{
    "classification": "BRAND_DEAL",
    "confidence": 0.72,
    "sender": "Sarah Chen <partnerships@glowskin.co>",
    "subject": "Paid Collaboration Opportunity",
    "summary": "GlowSkin is interested in a paid skincare integration...",
    "extracted_requirements": {
        "deliverables": ["1x Dedicated YouTube Video (60s)", "2x Instagram Stories"],
        "budget_offered": 800,
        "deadline": "August 15th",
        "key_requirements": ["must mention our 30-day guarantee", "show the unboxing"],
        "provided_script": None,
        "extra_dates": ["August 1st"]
    },
    "raw_text": "From: Sarah Chen..."
}
```

---

## 7. Deep Dive: The Negotiator Agent

> **File:** `agents/negotiator_agent.py`  
> **Job:** Take a brand deal → fetch analytics → calculate fair price → draft email

### The Pricing Algorithm (Step by Step)

The pricing formula lives in `_calculate_counter_offer()`. Here's exactly how
it works with real numbers from `config.py`:

**Creator stats (from `config.py`):**

| Platform | Subscribers | Avg Views | Engagement | Base CPM |
|---|---|---|---|---|
| YouTube | 500,000 | 45,000 | 4.2% | $20.00 |
| Instagram | 120,000 | 25,000 | 5.8% | $12.00 |
| TikTok | 850,000 | 150,000 | 8.5% | $6.00 |

> **What is CPM?** CPM = Cost Per Mille = cost per 1,000 views. It's the standard
> unit of advertising value. A $20 CPM means a brand pays $20 for every 1,000
> people who watch their sponsored segment.

#### Step 1: Base Value Per Platform

```
base_value = (avg_views / 1000) × estimated_cpm × num_deliverables
```

**Example:** Brand wants 1 YouTube video + 2 Instagram Stories

YouTube:  (45,000 / 1000) × $24.50 (CPM with 22.5% markup) × 3 = $3,307.50
Instagram: (25,000 / 1000) × $14.70 × 3 = $1,102.50

> **Why the 22.5% markup?** The analytics tool applies `base_cpm * 1.225`
> because base CPM in `config.py` is conservative. The actual ad value delivered
> to a brand is higher than the raw rate.

#### Step 2: Engagement Multiplier

```python
if engagement > 3.0:
    p_val *= config.ENGAGEMENT_MULTIPLIER  # 1.15 (15% bonus)
```

Both YouTube (4.2%) and Instagram (5.8%) are above 3%, so both get the 15% bonus:

```
YouTube:   $3,307.50 × 1.15 = $3,803.63
Instagram: $1,102.50 × 1.15 = $1,267.88
base_value total: $5,071.51
```

> **Why 3%?** Industry average engagement is ~2-3%. Above 3% means your audience
> genuinely cares — that's worth more to a brand.

#### Step 3: Multi-Platform Premium

```python
if len(platforms) > 1:
    base_value *= config.PLATFORM_COMBO_PREMIUM  # 1.20 (20% premium)
```

```
$5,071.51 × 1.20 = $6,085.81
```

A brand gets *more reach* by being on two platforms. That's worth a premium.

#### Step 4: Brand Budget Floor

```python
brand_floor = brand_budget * config.COUNTER_OFFER_FLOOR  # 1.35
```

If the brand offered $800: `$800 × 1.35 = $1,080`

The counter-offer is **always** at least 35% above what the brand offered.
This prevents the agent from ever "accepting" the brand's first number.

#### Step 5: Final Rounding

```python
raw_offer = max(base_value, brand_floor)  # Take the higher of the two
counter_offer = math.ceil(raw_offer / 50) * 50  # Round up to nearest $50
```

`max($6,085.81, $1,080) = $6,085.81` → rounded up → **$6,100**

> **Why round to $50?** Odd numbers like $6,085.81 look computer-generated.
> Rounded numbers look like confident human negotiating stances.

### The Email Drafting Engine

The email isn't just a template — it **adapts to the creator's tone** defined in
`config.py`:

```python
CREATOR_STYLE = {
    "tone": "energetic, witty, and conversational",
    "signature_outro": "Drop a comment if you learned something — bye! ✌️"
}
```

The drafting function checks for different tones and generates different intros:

| Tone in config | Email opens with |
|---|---|
| `"sarcastic"` | "Thanks for reaching out. Usually I ignore these, but..." |
| `"cozy"` or `"calm"` | "Thank you so much for reaching out — I would love to explore a cozy integration..." |
| `"high-energy"` or `"hype"` | "LET'S GO! Thanks for reaching out, I am massively hyped..." |
| `"professional"` | "Thank you for the inquiry. I have reviewed the brief and am interested..." |
| *(default)* | "Thank you so much for reaching out — I'm genuinely excited..." |

### The Edit/Feedback Loop

One of the most powerful features: if you type `[E]` during HITL review, the agent
accepts **free-text feedback** and re-runs with it. The feedback handler uses a
simple heuristic — if your feedback contains a dollar amount, it overrides the
calculated price:

```python
if feedback:
    price_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*|\d+)', feedback)
    if price_match:
        new_price = int(price_match.group(1).replace(',', ''))
        if new_price > 100:
            counter_offer = new_price
```

So if you type: *"I think $3500 is more realistic for this brand"*, the agent will
use $3,500 and regenerate the email. This mimics how a real LLM would follow
natural-language instructions.

---

## 8. Deep Dive: The MCP Server & Analytics Tool

> **Files:** `mcp_server/analytics_tool.py`, `mcp_server/main.py`  
> **Job:** Simulate a real-time analytics API and expose it as an MCP tool

### Why the Analytics Tool Adds "Jitter"

The analytics tool doesn't just return the same numbers every time. It adds
**±5% random noise** to simulate real API variability:

```python
def _jitter(value: float, pct: float = 0.05) -> float:
    factor = 1.0 + random.uniform(-pct, pct)
    return round(value * factor, 2)
```

**Real-world reason:** YouTube Analytics doesn't return the same subscriber count
twice in a row. It fluctuates second-to-second as people subscribe/unsubscribe.
Simulating this means our Negotiator Agent will get *slightly different* numbers
each run — which is realistic and good for testing.

**Example output from `get_creator_metrics()`:**

```json
{
    "creator_name": "Ashmita Dhawan",
    "handle": "@ashmita_dhawan",
    "top_performing_category": "Tech & Lifestyle",
    "last_updated": "2026-07-02T07:00:00+00:00",
    "platforms": {
        "YouTube": {
            "subscribers": 497843,
            "avg_views_per_video": 44231,
            "engagement_rate_pct": 4.18,
            "estimated_cpm_value": 24.38,
            "avg_watch_time_seconds": 139
        },
        "Instagram": {
            "followers": 121450,
            "avg_views_per_video": 25840,
            "engagement_rate_pct": 5.92,
            "estimated_cpm_value": 14.55
        },
        "TikTok": {
            "followers": 847200,
            "avg_views_per_video": 153000,
            "engagement_rate_pct": 8.71,
            "estimated_cpm_value": 7.32
        }
    }
}
```

### What the MCP Envelope Looks Like

When the Negotiator Agent calls `mcp_server.call_tool("get_creator_metrics")`,
it doesn't get the raw dict. It gets a **standardized MCP envelope**:

```json
{
    "tool": "get_creator_metrics",
    "status": "success",
    "timestamp": "2026-07-02T07:00:00+00:00",
    "data": { ... the actual metrics ... }
}
```

The agent then checks `mcp_response["status"] != "success"` before reading the data.
This is standard defensive programming — always check if a service call succeeded
before trusting its output.

### The Fallback Path

If the MCP call fails for any reason, the Negotiator Agent has a fallback:

```python
if mcp_response["status"] != "success":
    metrics = {
        "platforms": {
            "YouTube": {
                "subscribers": config.PLATFORMS["YouTube"]["subscribers"],
                "avg_views_per_video": config.PLATFORMS["YouTube"]["avg_views"],
                ...
            }
        }
    }
```

It falls back to the static values in `config.py`. This is called **graceful
degradation** — the system keeps working even when a dependency fails, just with
less precision. This is a critical pattern in production AI systems.

### Tool Schema — How Agents "Discover" Tools

Every MCP tool also exposes a **schema** — a description of what it does and
what parameters it accepts:

```python
def get_tool_schema() -> dict:
    return {
        "name": "get_creator_metrics",
        "description": "Fetches real-time creator analytics including subscriber "
                       "count, average views, engagement rate, watch time, and "
                       "estimated CPM value.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    }
```

In a real LLM-based agent, the LLM reads these schemas to know *which tools
are available and how to call them*. This is how tools like OpenAI's function
calling work — the LLM sees the schemas and decides which tool to call.

---

## 9. Deep Dive: The HITL Gatekeeper

> **File:** `security/hitl_gatekeeper.py`  
> **Job:** Show everything to the human, block execution until a decision is made

### How the Terminal UI Works

The gatekeeper uses **ANSI escape codes** to create the colored terminal output.
Here's what those mysterious `\033[...m` strings actually mean:

```python
_RED     = "\033[38;5;210m"   # Soft red (warnings)
_GREEN   = "\033[38;5;150m"   # Soft green (success)
_YELLOW  = "\033[38;5;223m"   # Warm yellow (information)
_BG_RED  = "\033[48;5;210m"   # Red background (for the REVIEW REQUIRED banner)
_BOLD    = "\033[1m"          # Bold text
_RESET   = "\033[0m"          # Reset ALL formatting
```

The `\033` is the **ESC character** (escape). The sequence `\033[1;31m` tells
the terminal: "make following text bold and red." `\033[0m` says "go back to normal."

> **Windows note:** ANSI codes are disabled by default on Windows. That's why
> `config.py` runs this at startup:
> ```python
> kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
> ```
> This enables "Virtual Terminal Processing" — Windows' term for ANSI support.

### The Emoji Width Problem (And How We Solve It)

Lining up boxes in the terminal with emoji is tricky. Emojis like 📧 or ⚠️ take
up **two character columns** in most terminals, but Python's `len()` counts them
as one character. This throws off padding calculations.

The gatekeeper uses a clever workaround:

```python
def _pad_line(text: str, width: int) -> str:
    visual_len = len(text.encode("utf-16-le")) // 2
    padding = max(0, width - visual_len)
    return text + " " * padding
```

By encoding to UTF-16-LE (2 bytes per character, 4 bytes for emoji), dividing
by 2 gives the *visual* width. This is how you get properly aligned boxes even
with emojis in them.

### The Decision Loop & Fail-Safe

The gatekeeper gives you **3 attempts** to enter a valid choice:

```python
max_attempts = 3
for attempt in range(max_attempts):
    choice = input("  Your choice [A/E/R]: ").strip().upper()

    if choice == "A":   # APPROVE
        ...
    elif choice == "E": # EDIT
        ...
    elif choice == "R": # REJECT
        ...
    else:
        remaining = max_attempts - attempt - 1
        print(f"Invalid input. ({remaining} attempts left)")

# If you type garbage 3 times:
return {"decision": "rejected", ...}  # Auto-reject (SAFE default)
```

Notice the fail-safe: invalid input eventually triggers an **auto-reject**, not
an auto-approve. In security systems, the default is always the *safer* option.

### What Happens on Approve

When you press `A`:

1. **Draft is saved** to `drafts/TIMESTAMP_SENDER.txt` — a text file containing
   the email, script, classification, and confidence score all together.

2. **Calendar event is created** if a deadline was detected:
   ```python
   calendar_utils.add_deadline(
       brand_name="GlowSkin Co.",
       deadline_str="August 15th",
       deliverables=["1x YouTube Video", "2x Instagram Stories"],
       counter_offer=6100,
   )
   ```
   This creates an `.ics` file in `calendar/` that you can import into Google
   Calendar, Apple Calendar, or Outlook.

3. **Extra dates** (other dates mentioned in the email beyond the main deadline)
   are also added as separate calendar events.

### The Non-Interactive Fallback

If you're running the pipeline in an automated/testing context (no keyboard), the
`input()` call would hang forever. The gatekeeper handles this gracefully:

```python
try:
    choice = input("  Your choice [A/E/R]: ").strip().upper()
except (EOFError, KeyboardInterrupt):
    print()
    _log("Non-interactive environment — auto-approving for demo")
    choice = "A"
```

`EOFError` is raised when there's no keyboard to read from (e.g., running in a
CI/CD pipeline). The agent catches it and auto-approves, which is useful for
demos and testing.

---

## 10. Deep Dive: `config.py` — The Single Source of Truth

> **File:** `config.py`  
> **Job:** Every number, name, path, and preference in ONE place

### Why One Config File Matters

Imagine you want to change your YouTube subscriber count from 500,000 to 750,000
because you just hit a new milestone. Without a central config, you'd need to find
and update that number in *every* agent file. With `config.py`, you change it once:

```python
"YouTube": {
    "subscribers": 750_000,  # Changed here → updates everywhere
    ...
}
```

Every agent that needs this number imports it directly:
```python
import config
subscribers = config.PLATFORMS["YouTube"]["subscribers"]
```

### The Windows Encoding Fix (Why It's in config.py)

The very first thing `config.py` does is fix Windows terminal encoding:

```python
if sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout.reconfigure(encoding="utf-8")
```

**Why is this in config.py instead of main.py?**

Because *every single module* in this project `import config` at the top. By
putting the encoding fix in `config.py`, it runs the moment *any* module loads.
This guarantees that by the time anyone tries to `print("🎬")`, the terminal
is already set up to handle it.

### The Pricing Constants

```python
ENGAGEMENT_MULTIPLIER  = 1.15   # +15% if engagement > 3%
PLATFORM_COMBO_PREMIUM = 1.20   # +20% for multi-platform deals
COUNTER_OFFER_FLOOR    = 1.35   # Always counter at ≥135% of their offer
ROUNDING_STEP          = 50     # Round up to nearest $50
```

These are all in one place so you can **tune the negotiation strategy** without
touching the negotiator logic. Want to be more aggressive? Change `COUNTER_OFFER_FLOOR`
to `1.50`. Want to reward engagement more? Raise `ENGAGEMENT_MULTIPLIER` to `1.25`.

### Creator Style Preferences

```python
CREATOR_STYLE = {
    "tone": "energetic, witty, and conversational",
    "format": "fast-paced with jump cuts",
    "signature_intro": "Hey guys, Ashmita here!",
    "preferred_angles": ["myth-busting", "honest review", "day-in-my-life integration"],
    "avoid": ["overly salesy language", "clickbait without payoff"],
}
```

The Creative Agent reads `preferred_angles` to pick a content angle, and
`avoid` to ensure the script doesn't use banned phrases. The Negotiator
reads `tone` to match the email's voice. One config, multiple consumers.

---

## 11. Putting It All Together

Here's the complete picture of what happens when you run `python main.py`:

```
┌─────────────────────────────────────────────────────────────┐
│                    python main.py                           │
│                                                             │
│  1. Print banner                                            │
│  2. Scan mock_inbox/ for .txt files                         │
│                                                             │
│  FOR EACH EMAIL:                                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ STEP 1: 🔀 Triage Agent                                │ │
│  │   • Reads email text                                    │ │
│  │   • Scores keywords against 6 categories                │ │
│  │   • Returns classification + confidence                 │ │
│  │   • Extracts: sender, budget, deliverables, deadline    │ │
│  │                                                         │ │
│  │ if BRAND_DEAL (or PR_PACKAGE / BARTER_DEAL):            │ │
│  │ ┌─────────────────────────────────────────────────────┐ │ │
│  │ │ STEP 2: 💰 Negotiator Agent                        │ │ │
│  │ │   • Calls MCP: get_creator_metrics() (±5% jitter)  │ │ │
│  │ │   • Detects platforms from deliverables text        │ │ │
│  │ │   • Calculates CPM-based pricing per platform       │ │ │
│  │ │   • Applies engagement + multi-platform multipliers │ │ │
│  │ │   • Floors counter-offer at 135% of brand's budget  │ │ │
│  │ │   • Rounds up to nearest $50                        │ │ │
│  │ │   • Drafts counter-offer email in creator's tone    │ │ │
│  │ │   • Packages brand brief for Creative               │ │ │
│  │ ├─────────────────────────────────────────────────────┤ │ │
│  │ │ STEP 3: 🎬 Creative Agent                          │ │ │
│  │ │   • Detects brand category (skincare, tech, etc.)  │ │ │
│  │ │   • Selects creative angle (myth-bust, storytime)  │ │ │
│  │ │   • Generates 4-part script (Hook→Body→Ad→Outro)   │ │ │
│  │ │   • Auto-improvises if brief is sparse             │ │ │
│  │ ├─────────────────────────────────────────────────────┤ │ │
│  │ │ STEP 4: 🛡️ HITL Gatekeeper                         │ │ │
│  │ │   • ⏸️ PAUSES execution (literally freezes)         │ │ │
│  │ │   • Displays TL;DR summary + email + script        │ │ │
│  │ │   • Shows detected deadline + calendar preview      │ │ │
│  │ │   • Waits for: [A]pprove / [E]dit / [R]eject       │ │ │
│  │ │   • If [E]: collects feedback, returns to Step 2   │ │ │
│  │ │   • If [A] → saves draft + adds deadline to .ics   │ │ │
│  │ │   • If [R] or 3× invalid → discards everything     │ │ │
│  │ └─────────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │ if FAN_MAIL:     💌 Log and skip                        │ │
│  │ if SPAM:         🗑️ Discard                             │ │
│  │ if PERSONAL:     🔔 Show notification, wait for Enter   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  3. Print pipeline summary (emails processed, decisions)    │
│  4. Show upcoming deadlines from calendar/                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why Each Piece Matters

| Component | Real-World Equivalent | Why It's Important |
|---|---|---|
| Triage Agent | Email filter / receptionist | Prevents spam from wasting pipeline resources |
| MCP Server | Analytics dashboard API | Standardized data access for all agents |
| Negotiator Agent | Business manager | Ensures creators aren't underpaid |
| Creative Agent | Creative director | Turns boring briefs into engaging content |
| HITL Gatekeeper | Quality control inspector | Nothing goes out without human approval |
| Calendar Utils | Personal assistant's calendar | Never miss a content deadline |
| `config.py` | Company handbook | One source of truth for every setting |

---

## 12. Common Beginner Questions

**Q: Why does the code use `from __future__ import annotations`?**

This is a Python 3.7+ compatibility trick. It lets you write type hints like
`list[str]` and `dict | None` in older Python versions without errors. In Python 3.10+
you don't need it, but it doesn't hurt to include it.

---

**Q: What are `_CYAN`, `_RESET` etc. at the top of every agent?**

These are ANSI color codes for terminal output. The underscore `_` prefix is a
Python convention meaning "this is a module-private constant — don't import it."
The actual strings like `"\033[96m"` are escape sequences that tell the terminal
to change text color.

---

**Q: Why do all the helper functions start with an underscore (`_extract_budget`, `_log`)?**

The underscore prefix means "this is private to this module." It's a signal to
other developers: "Don't call this directly from outside this file. Use the public
function (`classify`, `negotiate`) instead." Python doesn't technically *enforce*
this, but it's a strong convention that every Python developer respects.

---

**Q: What does `textwrap.dedent()` do in the email drafts?**

When you write a multi-line string inside a function, Python includes the
indentation whitespace. `textwrap.dedent()` strips it:

```python
# Without dedent:
email = """
        Hi there,
        Your budget is $1000.
"""
# ↑ Has 8 spaces of indentation at the start of each line

# With dedent:
email = textwrap.dedent("""
    Hi there,
    Your budget is $1000.
""")
# ↑ Clean, no extra indentation
```

---

**Q: Why are the dollar amounts formatted as `${counter_offer:,}`?**

The `:,` in an f-string format spec adds **comma separators** to numbers:
- `f"{1650}"` → `"1650"`
- `f"{1650:,}"` → `"1,650"`

Cleaner to read in emails.

---

**Q: If confidence is below 0.1, why default to SPAM instead of "UNKNOWN"?**

Because an "UNKNOWN" category would need special handling throughout the whole
pipeline. SPAM already means "discard and don't process further" — which is the
*correct* behavior for something we're uncertain about. In AI safety, **the default
action should always be the least harmful one**. Discarding an uncertain email is
safer than accidentally treating it as a brand deal.

---

## 13. Glossary

Quick reference for terms you'll encounter in the code:

| Term | What It Means |
|---|---|
| **Agent** | A program that can observe, think, decide, and act autonomously |
| **ADK** | Agent Development Kit — Google's toolkit for building multi-agent systems |
| **MCP** | Model Context Protocol — universal standard for AI tool access |
| **FastMCP** | Python framework for building MCP servers quickly |
| **HITL** | Human-in-the-Loop — human approval required before critical actions |
| **CPM** | Cost Per Mille — price per 1,000 views (standard influencer pricing) |
| **Triage** | The process of sorting/classifying incoming items by priority |
| **Orchestrator** | The central controller that coordinates multiple agents |
| **Pipeline** | A series of steps where output of one becomes input of the next |
| **Mock** | Fake/simulated data used for testing without real services |
| **Guardrail** | A safety mechanism that prevents AI from doing harmful things |
| **Counter-offer** | A response to a proposed deal with different (usually higher) terms |
| **Deliverable** | A specific piece of content the creator must produce (video, post, etc.) |
| **Engagement Rate** | % of viewers who interact (like, comment, share) with content |
| **B-roll** | Supplemental footage intercut with the main shot for visual variety |
| **CTA** | Call To Action — prompting viewers to do something (subscribe, click) |
| **iCalendar (.ics)** | Universal file format for calendar events (works with all calendar apps) |
| **Jitter** | Small random variation added to a value to simulate real-world fluctuation |
| **Graceful degradation** | System keeps working (at reduced quality) when a dependency fails |
| **ANSI escape codes** | Special characters that control terminal text color and formatting |
| **Regex** | Regular Expression — a pattern for finding/extracting text |
| **Type hint** | Python annotation (e.g., `str`, `dict`, `list[str]`) declaring expected types |
| **Pydantic** | Python library for strict data validation (what you'd use in production) |
| **EOFError** | Error raised when Python tries to read input but there's no keyboard |
| **UTF-16-LE** | Text encoding that uses 2 bytes per character (used to measure emoji width) |
| **f-string** | Python string with `{}` placeholders: `f"Hello {name}!"` |

---

## 🎓 What to Read Next

1. **Google ADK Documentation** — [adk.dev](https://adk.dev) — The official Agent
   Development Kit docs
2. **MCP Specification** — [modelcontextprotocol.io](https://modelcontextprotocol.io)
   — The official MCP standard
3. **FastMCP on GitHub** — The Python framework for building MCP servers
4. **Python `re` module docs** — [docs.python.org/3/library/re.html](https://docs.python.org/3/library/re.html)
   — Learn how regex works (used heavily in the Triage Agent)
5. **This project's `README.md`** — Setup instructions and architecture diagram

---

> 💡 **Tip:** The best way to understand this project is to **run it** (`python main.py`)
> and watch the terminal output. Every agent prints timestamped logs so you can literally
> *see* the handshake happening in real time. Then open the code file for whichever
> step you found interesting and trace it line by line.

---

*Written by Ashmita Dhawan for the Kaggle Capstone Project — Autonomous Creator Studio & Influencer Manager*
