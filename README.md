# Quanteinstein — B2B Outbound Intelligence & Connection Request Engine

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.8%2B-E92063.svg)](https://docs.pydantic.dev)
[![Tests](https://img.shields.io/badge/Tests-11%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

> **Elite B2B Outbound Intelligence system for Quanteinstein.** Ingests scraped LinkedIn profile bios, recent posts/comments, and company job listings; computes behavioral intent scores (1–10); and drafts hyper-personalized, peer-to-peer connection requests with zero buzzwords strictly under 45 words for high-intent matches.

---

## 🎯 Strategic Context

### Our Project: Quanteinstein
> *"Quanteinstein is a risk-guarded quantitative strategy incubation and paper-trading sandbox that bridges unstructured market intelligence into deterministic algorithmic execution. Through an integrated modular suite—featuring an AI Quant Coach, visual Strategy Builder, historical Backtester, live Charting, Trade Journal, and execution Analytics—it allows traders to formulate mathematical parameters, stress-test rules against historical friction, and forward-incubate strategies in a 100% paper-simulated environment before routing orders to live exchange pipes."*

### Target ICP (Ideal Customer Profile)
- Systematic retail traders & algorithmic developers
- Proprietary trading desks & market makers
- Emerging hedge funds (especially newly launched firms within their first 6 months)
- Boutique quant asset management and portfolio teams

---

## ⚡ Core Operational Rules

### Step 1: Behavioral Intent Scoring (1–10)
* **Score 9–10 (High Intent — Urgent Need)**: Explicitly mentioned a pain point Quanteinstein solves in a post/comment (execution slippage, backtest-to-live divergence, emotional manual overrides, heavy infrastructure overhead), OR their company is actively hiring for quantitative execution / backtesting infrastructure.
* **Score 8 (Strong Match — Tech Stack & Niche)**: Frequently posts about quantitative/systematic trading and uses relevant stack components (`vectorbt`, `backtrader`, `ccxt`, `IBKR API`, order book dynamics, statistical arbitrage).
* **Score 4–7 (Qualified Pass)**: Right industry or title (Quant PM, Trader), but no active signals, recent posts, or company hiring triggers to justify outreach. *(PASS)*
* **Score 1–3 (Irrelevant Pass)**: Outside the quantitative trading domain. *(PASS)*

### Step 2: Connection Request Generation (Score ≥ 8 ONLY)
1. **Max 45 words** *(strictly enforced)*.
2. **First sentence MUST reference the exact trigger found** (*e.g.*, *"Saw your post on slippage and execution friction during volatile sessions..."* or *"Noticed [Company] is hiring a Quant Execution Engineer..."*).
3. **DO NOT pitch**. Frame Quanteinstein as a peer-to-peer engineer exchange (*e.g.*, *"We just built an open-source sandbox to forward-incubate strategies..."*).
4. **End with a soft, low-friction ask** (*e.g.*, *"Would love your technical feedback if open to connecting."* or *"Curious how you handle this currently."*).
5. **Zero buzzwords**. Sound like a tired, brilliant engineer talking to another engineer.

### Strict Output Schema
```json
{
  "score": [Integer 1-10],
  "reasoning": "[1 sentence explaining the specific trigger found or why it was rejected]",
  "message": "[The drafted message, or null if the score is under 8]"
}
```

---

## 🏗️ Architecture Overview

```
Marketing-Team/
├── app/
│   ├── analyzer.py       # Core B2B Intelligence Analyst (Trigger detection & LinkedIn message generation)
│   ├── discovery.py      # Regional Web Search, Scraper & Email Extraction Engine
│   ├── email_generator.py# Hyper-personalized Cold Email Outreach Generator
│   ├── api.py            # FastAPI REST API endpoints, discovery & CSV upload handler
│   ├── cli.py            # Command-line interface (single, batch, stats, prospect, interactive)
│   ├── config.py         # Application settings, Quanteinstein context, and thresholds
│   ├── llm_client.py     # Gemini & OpenAI client wrappers with heuristic fallback
│   ├── models.py         # Pydantic schemas (ProspectInput, SearchQuery, GeneratedEmail)
│   ├── prompts.py        # System prompt and prompt formatting pipeline
│   ├── storage.py        # SQLite persistent storage and analytics tracking
│   └── static/           # Interactive Web UI (dark-mode dashboard)
│       ├── index.html
│       ├── style.css
│       └── app.js
├── data/
│   ├── sample_prospects.json  # 8 realistic scraped LinkedIn leads across all score tiers
│   └── sample_prospects.csv   # CSV version for batch upload testing
├── tests/
│   ├── test_analyzer.py        # Unit tests for scoring rules & constraints
│   ├── test_api.py             # Integration tests for FastAPI endpoints
│   └── test_email_generator.py # Unit tests for web search & cold email generation
├── main.py               # Unified entry point for Server and CLI
├── Dockerfile            # Container deployment image
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variables template
```

---

## 🚀 Quickstart: Run 100% Locally on Your Windows Laptop

No cloud deployment or Docker is required. You can run the entire engine locally on your laptop, connect your personal email account to dispatch cold emails directly, and connect to LinkedIn for 1-click connection note dispatch.

### 1. Windows Command Prompt (`cmd`) / PowerShell Setup

Open your terminal or `cmd` in `C:\Marketing Team`:

```cmd
:: 1. Activate your local virtual environment
.venv\Scripts\activate

:: 2. (Optional) Install dependencies if not already installed
pip install -r requirements.txt
```

---

## ✉️ Connect Your Personal Email (Gmail / Outlook / Custom SMTP)

You can send real cold outreach directly from your personal inbox through local SMTP:

1. **For Gmail Accounts:**
   - Turn on **2-Step Verification** on your Google Account: [https://myaccount.google.com/signinoptions/two-step-verification](https://myaccount.google.com/signinoptions/two-step-verification)
   - Generate an **App Password**: Go to [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), select "Other", enter `Marketing-Team`, and copy the 16-character password.
2. **For Outlook / Office 365:**
   - Host: `smtp.office365.com`, Port: `587`.
3. **Configure `.env`**:
   Open `.env` in `C:\Marketing Team` and set your credentials:
   ```ini
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_16_char_app_password
   SENDER_NAME=Technical Founder
   ```
4. **Test Your Email Connection in CMD:**
   ```cmd
   python main.py test-smtp
   ```
   *You will see:* `[+] SUCCESS: Successfully connected and authenticated as your_email@gmail.com!`

---

## 🔗 Connect Your LinkedIn Account (Safe 1-Click Dispatch)

To protect your LinkedIn account from bot detection and scraping bans, the system uses a **safe, instant 1-click clipboard integration**:

1. Make sure you are logged into [linkedin.com](https://www.linkedin.com) in your regular web browser.
2. When any prospect scores **8 or higher**, click **"Connect on LinkedIn (Copy & Open)"** in the dashboard.
3. The engine automatically copies the **≤ 45-word personalized hook** to your Windows clipboard and opens the prospect's profile or search page.
4. Click **Connect** &rarr; **Add a note** &rarr; press `Ctrl + V` &rarr; **Send**. *(Takes 3 seconds, zero ban risk!)*

---

## 💻 Exact Command Line (`cmd`) Cheat-Sheet

| Action | Windows Command |
| :--- | :--- |
| **Launch Web Dashboard** | `python main.py` *(opens at `http://127.0.0.1:8000`)* |
| **Test Email Connection** | `python main.py test-smtp` |
| **Web Search & Draft Cold Emails** | `python main.py prospect --region "London, UK" --niche "quantitative hedge fund" --count 3` |
| **Search, Draft & SEND via Email** | `python main.py prospect --region "New York, NY" --count 3 --send` |
| **Send Single Test Email** | `python main.py send-email --to "target@example.com" --subject "Test Sandbox" --body "Hi there"` |
| **Analyze Single Prospect** | `python main.py analyze --bio "Managing quant fund" --posts "Slippage is killing our alpha"` |
| **Analyze Strict JSON Only** | `python main.py analyze --bio "Managing quant fund" --posts "Slippage friction" --strict` |
| **Process Batch CSV Leads** | `python main.py batch --file data\sample_prospects.csv` |
| **Show Intelligence Stats** | `python main.py stats` |
| **Run All 24 Unit Tests** | `python -m unittest discover tests` |

---

### 2. Run the Interactive Web Dashboard


```bash
python main.py
```
Open your browser at **`http://127.0.0.1:8000`**.
- **Interactive Lead Inspector**: Test with one-click presets (10/10 slippage pain, 9/10 hiring, 8/10 tech stack, 4–7 inactive pass, 1–3 irrelevant).
- **Batch CSV Processor**: Upload scraped leads from Phantombuster, Apify, or custom scrapers.
- **Instant Copy**: Copy approved 45-word connection requests with 1 click.
- **Interactive Swagger Docs**: Available at **`http://127.0.0.1:8000/docs`**.

---

## 💻 CLI Usage

### Analyze a Single Prospect (Strict JSON Output)
```bash
python main.py analyze \
  --bio "Ex-Citadel. Head of Quantitative Strategies." \
  --posts "Our live slippage and execution friction is destroying our statistical arbitrage fills." \
  --jobs "Hiring Quant Execution Engineer" \
  --strict
```

**Output:**
```json
{
  "score": 9,
  "reasoning": "The prospect explicitly posted about execution slippage / market friction, representing an active pain point directly solved by Quanteinstein.",
  "message": "Saw your post on slippage and execution friction during volatile sessions. We just built an open-source sandbox to forward-incubate strategies against real exchange friction before touching live pipes. Would love your technical feedback if open to connecting."
}
```

### Search Web & Generate Tailored Cold Emails by Region
```bash
python main.py prospect \
  --region "London, UK" \
  --niche "statistical arbitrage" \
  --firm-type "emerging hedge fund" \
  --count 3 \
  --sender "Technical Founder"
```

### Batch Analyze Scraped Prospects (JSON or CSV)
```bash
python main.py batch --file data/sample_prospects.json --out exports/results.json
```

### View Lead Conversion & Pipeline Statistics
```bash
python main.py stats
```

---

## 📡 REST API Reference

### 1. Web Prospecting & Tailored Cold Email Campaign
* **Endpoint:** `POST /api/discovery/run-campaign`
* **Request Body:**
```json
{
  "niche": "quantitative hedge fund",
  "region": "London, UK",
  "firm_type": "emerging hedge fund (first 6 months)",
  "num_results": 3,
  "sender_name": "Technical Founder"
}
```
* **Response (200 OK):**
```json
{
  "total_discovered": 3,
  "leads": [...],
  "emails": [
    {
      "recipient_email": "research@aspectcapital.com",
      "recipient_name": "Systematic Research Team",
      "firm_name": "Aspect Capital",
      "subject": "sandbox for Aspect Capital's trend following",
      "body": "Saw your work at Aspect Capital in London, UK deploying Trend Following, Statistical Arbitrage. We built Quanteinstein—a risk-guarded strategy incubation and paper-trading sandbox...",
      "word_count": 126
    }
  ]
}
```

### 2. Export Generated Cold Emails
* **Endpoint:** `GET /api/discovery/export-emails`
* Downloads a CSV of all drafted cold emails ready for Lemlist, Smartlead, Instantly, or your CRM.

### 1. Analyze Prospect (Strict 3-Field JSON)
* **Endpoint:** `POST /api/analyze/strict`
* **Request Body:**
```json
{
  "name": "Marcus Vance",
  "company": "Apex Alpha Capital",
  "title": "Managing Partner",
  "scraped_profile_bio": "Managing quant equity prop book.",
  "recent_posts_and_comments": "Backtest overfitting vs live exchange friction is our biggest headache.",
  "recent_company_job_listings": "Hiring Quant Dev"
}
```
* **Response (200 OK):**
```json
{
  "score": 9,
  "reasoning": "The prospect explicitly posted about execution slippage / market friction, representing an active pain point directly solved by Quanteinstein.",
  "message": "Saw your post on slippage and execution friction during volatile sessions. We just built an open-source sandbox to forward-incubate strategies against real exchange friction before touching live pipes. Would love your technical feedback if open to connecting."
}
```

### 2. Batch Processing
* **Endpoint:** `POST /api/batch`
* Ingests multiple prospects, outputs batch conversion metrics (`high_intent_count`, `average_score`) and scored records.

### 3. Upload Scraped CSV
* **Endpoint:** `POST /api/upload-csv`
* Accepts multipart file upload (`.csv`).

### 4. Export Qualified Leads
* **Endpoint:** `GET /api/export?min_score=8`
* Downloads a CSV of high-intent prospects and their drafted connection requests ready for sales outreach.

---

## 🧪 Testing & Verification

Run the comprehensive unit and integration test suite:

```bash
python -m unittest discover tests
```

Tests verify:
- ✅ High-intent pain points trigger Score 9–10
- ✅ Active company hiring triggers Score 9–10
- ✅ Niche & tech stack triggers Score 8
- ✅ Inactive ICP profiles correctly PASS (Score 4–7, `message = null`)
- ✅ Irrelevant prospects correctly PASS (Score 1–3, `message = null`)
- ✅ Hard cap of **≤ 45 words** on all generated messages
- ✅ Exactly **1 sentence reasoning** constraint
- ✅ First sentence hook matches detected trigger
- ✅ API endpoints and batch CSV uploads

---

## 🐳 Docker Deployment

Run the complete application in a container with a single command:

```bash
docker compose up -d
```
The dashboard and REST API will be available at `http://localhost:8000`.

---

## 📄 License
MIT License. Built for the Quanteinstein Marketing & Outbound Intelligence Team.
