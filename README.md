# 🎬 Autonomous Creator Studio & Influencer Manager

A fully local, multi-agent AI system that automates the business side of content creation — from email triage to deal negotiation to video scripting — with human-in-the-loop safety.

Built as a **Kaggle Capstone Project** demonstrating Multi-Agent Systems and the Model Context Protocol (MCP).

---

## 🏗️ Architecture

```
📬 mock_inbox/              Incoming emails (brand deals, fan mail, spam)
       │
       ▼
🔀 Triage Agent             Classifies → BRAND_DEAL | FAN_MAIL | SPAM
       │
       ├── BRAND_DEAL ──────────────────────────────────────────────┐
       │                                                           │
       ▼                                                           │
💰 Negotiator Agent         Fetches analytics via MCP Server       │
       │                    Calculates counter-offer ($)            │
       │                    Drafts professional reply email         │
       ▼                                                           │
🎬 Creative Agent           Selects creative angle                 │
       │                    Generates video script                  │
       │                    (Hook → Body → Sponsor → Outro)        │
       ▼                                                           │
🛡️ HITL Gatekeeper          Human reviews email + script           │
       │                    [A]pprove / [E]dit / [R]eject          │
       │                                                           │
       ├── Approve → 📁 drafts/ + 📅 calendar/.ics                │
       └── Reject  → Discarded                                    │
                                                                   │
       ├── FAN_MAIL → 💌 Fan Mail Agent → HITL Gatekeeper         │
       └── SPAM     → 🗑️ Discarded                                │
```

---

## ⚡ Quick Start

```bash
# No installation needed — Python 3.10+ standard library only
cd "influencer manager"
python main.py
```

That's it. No `pip install`, no API keys, no `.env` files.

> 🧠 **New to AI agents, MCP, or HITL?** Read the [**Beginner's Tech Guide**](BEGINNER_TECH_GUIDE.md) first — it explains every concept with simple analogies.

---

## 📂 Project Structure

```
influencer manager/
├── main.py                    # Central orchestrator — run this
├── config.py                  # Mock creator metrics & settings
├── calendar_utils.py          # Deadline → .ics calendar linking
│
├── agents/
│   ├── __init__.py
│   ├── triage_agent.py        # Email classifier (BRAND_DEAL/FAN_MAIL/SPAM)
│   ├── negotiator_agent.py    # CPM pricing engine + email drafter
│   ├── creative_agent.py      # Video script generator with improvisation
│   └── fan_mail_agent.py      # Personalized fan response drafter
│
├── mcp_server/
│   ├── __init__.py
│   ├── analytics_tool.py      # Mock MCP tool: get_creator_metrics()
│   └── main.py                # MCP server with tool registration
│
├── security/
│   ├── __init__.py
│   └── hitl_gatekeeper.py     # Human-in-the-loop approval terminal gate
│
├── mock_inbox/                # Drop .txt emails here
│   ├── sample_brand_email.txt
│   ├── sample_fan_email.txt
│   └── sample_spam_email.txt
│
├── drafts/                    # (auto-created) Approved outputs saved here
├── calendar/                  # (auto-created) .ics files + deadlines.json
├── README.md
└── BEGINNER_TECH_GUIDE.md     # Simple explanation of the tech stack for beginners
```

---

## 🤖 Component Details

### 1. Triage Agent (`agents/triage_agent.py`)
- **Input:** Raw email text from `mock_inbox/`
- **Output:** Classification + extracted metadata (sender, budget, deliverables, deadline)
- **Method:** Position-weighted keyword scoring with confidence calculation
- **Swap-ready:** Replace `classify()` with an LLM call to upgrade

### 2. Negotiator Agent (`agents/negotiator_agent.py`)
- **Input:** Triage result for BRAND_DEAL emails
- **Output:** Counter-offer amount + professional email draft + brand brief
- **Pricing formula:**
  ```
  value = (avg_views / 1000) × CPM × deliverables × engagement_bonus × platform_premium
  counter = max(value, brand_budget × 1.35), rounded to nearest $50
  ```
- **MCP Integration:** Calls `get_creator_metrics()` for real-time analytics

### 3. Creative Agent (`agents/creative_agent.py`)
- **Input:** Brand brief from Negotiator
- **Output:** Complete video script (Hook → Body → Sponsor → Outro)
- **Features:** 8 creative angles, category detection, auto-improvisation for sparse briefs

### 4. Fan Mail Agent (`agents/fan_mail_agent.py`)
- **Input:** Triage result for FAN_MAIL emails
- **Output:** Personalized thank-you email draft
- **Features:** Extracts fan's name and drafts a warm, appreciative response for the creator to approve.

### 5. MCP Server (`mcp_server/`)
- Mock Model Context Protocol server with tool registration
- Exposes `get_creator_metrics()` returning JSON analytics
- Adds ±5% random jitter to simulate real-time API variance
- Extensible: register new tools via `server.register_tool()`

### 6. HITL Gatekeeper (`security/hitl_gatekeeper.py`)
- Blocks execution until human approves
- Displays email drafts (and scripts) in styled terminal boxes
- Actions: Approve (save + calendar), Edit (feedback loop), Reject (discard)

### 7. Calendar Integration (`calendar_utils.py`)
- Parses deadlines from brand deals into datetime objects
- Generates `.ics` files importable by Google Calendar / Outlook / Apple Calendar
- Maintains `calendar/deadlines.json` tracker with urgency color-coding
- Adds 3-day and 1-day reminder alarms to calendar events

---

## 📅 Calendar Feature

When you approve a brand deal, the system automatically:
1. Parses the deadline from the email (e.g., "August 15th")
2. Creates a `.ics` calendar event file in `calendar/`
3. Adds reminder alarms (3 days before + 1 day before)
4. Updates the local deadline tracker

**To add to your calendar:** Double-click any `.ics` file in the `calendar/` folder.

---

## 🧪 Testing

### Add Custom Emails
Drop any `.txt` file into `mock_inbox/` and re-run `python main.py`. The system will automatically pick it up and classify it.

### Test All Paths
The included 3 sample emails exercise all classification paths:
- `sample_brand_email.txt` → Full 4-agent pipeline
- `sample_fan_email.txt` → Fan mail pipeline (Fan Mail Agent + HITL)
- `sample_spam_email.txt` → Classified and discarded

---

## 🔧 Configuration

Edit `config.py` to customize the mock creator profile:

```python
CREATOR_NAME = "Ashmita Dhawan"
SUBSCRIBERS = 500_000
AVG_VIEWS = 45_000
BASE_CPM = 20.00
ENGAGEMENT_RATE_PCT = 4.2
```

---

## 🚀 Future Extensions

| Feature | Change Required |
|---|---|
| Real LLM integration | Replace `classify()`/`generate_script()` with API calls |
| HTTP MCP server | Wrap `MCPServer` in FastAPI (like prep_agent's server.py) |
| Real YouTube API | Swap `analytics_tool.py` mock with YouTube Data API v3 |
| Database storage | Replace JSON file storage with SQLite/PostgreSQL |
| Email sending | Add SMTP integration after HITL approval |
| Multi-creator | Extend `config.py` to support creator profiles dict |

---

## 📝 License

Built for educational purposes — Kaggle Capstone Project.
