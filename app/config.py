"""
Configuration and Domain Context for Quanteinstein B2B Marketing Intelligence Engine.
"""

import os
from typing import Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings(BaseModel):
    # Project Identity
    PROJECT_NAME: str = "Quanteinstein"
    PROJECT_CONTEXT: str = (
        "Quanteinstein is a risk-guarded quantitative strategy incubation and paper-trading sandbox "
        "that bridges unstructured market intelligence into deterministic algorithmic execution. "
        "Through an integrated modular suite—featuring an AI Quant Coach, visual Strategy Builder, "
        "historical Backtester, live Charting, Trade Journal, and execution Analytics—it allows traders "
        "to formulate mathematical parameters, stress-test rules against historical friction, and forward-incubate "
        "strategies in a 100% paper-simulated environment before routing orders to live exchange pipes."
    )
    
    TARGET_AUDIENCE: str = (
        "Systematic retail traders, proprietary trading desks, emerging hedge funds, boutique quant firms, "
        "and portfolio management teams—including newly launched firms within their first 6 months—who want "
        "to build, backtest, and incubate automated trading strategies without the risk of emotional execution, "
        "code-heavy infrastructure overhead, or capital blowups. Systematic retail traders, proprietary trading "
        "desks, and quantitative asset management teams who want to build, backtest, and incubate automated "
        "trading strategies without the risk of emotional execution, code-heavy infrastructure overhead, "
        "or capital blowups."
    )

    # Scoring & Generation Constraints
    MAX_MESSAGE_WORDS: int = 45
    MIN_SCORE_FOR_OUTREACH: int = 8

    # LLM Settings
    LLM_PROVIDER: Literal["gemini", "openai", "heuristic"] = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "heuristic").lower()  # type: ignore
    )
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    OPENAI_API_KEY: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    OPENAI_MODEL: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    # Server Settings
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "true").lower() in ("true", "1", "yes"))

    # Database
    DB_PATH: str = Field(default_factory=lambda: os.getenv("DB_PATH", "prospects.db"))

    # Local Email (SMTP) Configuration
    SMTP_HOST: str = Field(default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com"))
    SMTP_PORT: int = Field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    SMTP_USER: str = Field(default_factory=lambda: os.getenv("SMTP_USER", ""))
    SMTP_PASSWORD: str = Field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    SENDER_NAME: str = Field(default_factory=lambda: os.getenv("SENDER_NAME", "Technical Founder"))

settings = Settings()
