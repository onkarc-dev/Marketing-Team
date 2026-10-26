"""
SQLite Storage Layer for Quanteinstein B2B Outbound Leads.
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from app.config import settings
from app.models import EnrichedProspectRecord, SystemStats, TriggerSignal


class ProspectStorage:
    """Manages persistent SQLite storage for analyzed prospects."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prospects (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    company TEXT,
                    title TEXT,
                    linkedin_url TEXT,
                    scraped_profile_bio TEXT,
                    recent_posts_and_comments TEXT,
                    recent_company_job_listings TEXT,
                    score INTEGER,
                    intent_tier TEXT,
                    reasoning TEXT,
                    message TEXT,
                    word_count INTEGER,
                    triggers_json TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()

    def save_prospect(self, record: EnrichedProspectRecord) -> None:
        """Insert or replace prospect record."""
        triggers_json = json.dumps([t.model_dump() for t in record.triggers])
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO prospects (
                    id, name, company, title, linkedin_url,
                    scraped_profile_bio, recent_posts_and_comments, recent_company_job_listings,
                    score, intent_tier, reasoning, message, word_count, triggers_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.name, record.company, record.title, record.linkedin_url,
                record.scraped_profile_bio, record.recent_posts_and_comments, record.recent_company_job_listings,
                record.score, record.intent_tier, record.reasoning, record.message, record.word_count,
                triggers_json, record.created_at
            ))
            conn.commit()

    def get_prospects(self, min_score: Optional[int] = None, limit: int = 100) -> List[EnrichedProspectRecord]:
        """Fetch saved prospects ordered by recency and score."""
        with self._get_connection() as conn:
            if min_score is not None:
                cursor = conn.execute(
                    "SELECT * FROM prospects WHERE score >= ? ORDER BY created_at DESC LIMIT ?",
                    (min_score, limit)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM prospects ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            rows = cursor.fetchall()
            
        results: List[EnrichedProspectRecord] = []
        for r in rows:
            triggers_data = json.loads(r["triggers_json"]) if r["triggers_json"] else []
            triggers = [TriggerSignal(**t) for t in triggers_data]
            results.append(EnrichedProspectRecord(
                id=r["id"],
                name=r["name"],
                company=r["company"],
                title=r["title"],
                linkedin_url=r["linkedin_url"],
                scraped_profile_bio=r["scraped_profile_bio"],
                recent_posts_and_comments=r["recent_posts_and_comments"],
                recent_company_job_listings=r["recent_company_job_listings"],
                score=r["score"],
                intent_tier=r["intent_tier"],
                reasoning=r["reasoning"],
                message=r["message"],
                word_count=r["word_count"],
                triggers=triggers,
                created_at=r["created_at"]
            ))
        return results

    def get_stats(self) -> SystemStats:
        """Compute system metrics across all records."""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM prospects").fetchone()[0]
            high_intent = conn.execute("SELECT COUNT(*) FROM prospects WHERE score >= 8").fetchone()[0]
            qualified_pass = conn.execute("SELECT COUNT(*) FROM prospects WHERE score BETWEEN 4 AND 7").fetchone()[0]
            irrelevant = conn.execute("SELECT COUNT(*) FROM prospects WHERE score < 4").fetchone()[0]
            avg_score = conn.execute("SELECT AVG(score) FROM prospects").fetchone()[0] or 0.0
            messages_drafted = conn.execute("SELECT COUNT(*) FROM prospects WHERE message IS NOT NULL AND message != ''").fetchone()[0]

        return SystemStats(
            total_analyzed=total,
            tier_high_intent=high_intent,
            tier_qualified_pass=qualified_pass,
            tier_irrelevant=irrelevant,
            average_score=round(avg_score, 1),
            messages_drafted=messages_drafted
        )
