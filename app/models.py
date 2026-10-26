"""
Data schemas and models for Quanteinstein B2B Outbound Intelligence Engine.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, field_validator


class ProspectInput(BaseModel):
    """Input payload representing scraped LinkedIn prospect data."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: Optional[str] = Field(default="Prospect", description="Name of the prospect if available")
    company: Optional[str] = Field(default="", description="Prospect company name")
    title: Optional[str] = Field(default="", description="Prospect job title")
    linkedin_url: Optional[str] = Field(default="", description="LinkedIn profile URL")
    
    # Required Scraped Content Blocks
    scraped_profile_bio: str = Field(
        ..., 
        description="Scraped summary / headline / about bio from LinkedIn"
    )
    recent_posts_and_comments: str = Field(
        ..., 
        description="Scraped text from recent LinkedIn posts, articles, and comment activity"
    )
    recent_company_job_listings: str = Field(
        ..., 
        description="Scraped active job postings and descriptions from the prospect's company"
    )


class AnalysisResult(BaseModel):
    """
    STRICT Output Format as defined by the user:
    {
      "score": [Integer 1-10],
      "reasoning": "[1 sentence explaining the specific trigger found or why it was rejected]",
      "message": "[The drafted message, or null if the score is under 8]"
    }
    """
    score: int = Field(..., ge=1, le=10, description="Intent score from 1 to 10")
    reasoning: str = Field(..., description="1 sentence explaining the specific trigger or rejection rationale")
    message: Optional[str] = Field(None, description="Drafted message (max 45 words), or null if score < 8")

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("Score must be an integer between 1 and 10.")
        return v

    @field_validator("message")
    @classmethod
    def validate_message_consistency(cls, v: Optional[str], info) -> Optional[str]:
        # If score is known and under 8, message must be None
        score = info.data.get("score")
        if score is not None and score < 8 and v is not None:
            return None
        return v


class TriggerSignal(BaseModel):
    """Identified behavioral trigger signal."""
    category: str = Field(..., description="Category: pain_point, hiring, tech_stack, niche, none")
    signal: str = Field(..., description="Description or exact excerpt of the detected signal")
    relevance_score: int = Field(..., description="Estimated trigger impact (1-10)")


class EnrichedProspectRecord(BaseModel):
    """Comprehensive prospect record stored in database and served to UI."""
    id: str
    name: str
    company: str
    title: str
    linkedin_url: str
    scraped_profile_bio: str
    recent_posts_and_comments: str
    recent_company_job_listings: str
    score: int
    intent_tier: str
    reasoning: str
    message: Optional[str]
    word_count: int
    triggers: List[TriggerSignal] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BatchAnalysisRequest(BaseModel):
    """Batch analysis input."""
    prospects: List[ProspectInput]


class BatchAnalysisResponse(BaseModel):
    """Batch analysis response summary."""
    total: int
    high_intent_count: int  # score >= 8
    passed_count: int       # score < 8
    average_score: float
    results: List[EnrichedProspectRecord]


class SystemStats(BaseModel):
    """Overview statistics for dashboard."""
    total_analyzed: int
    tier_high_intent: int    # 8-10
    tier_qualified_pass: int # 4-7
    tier_irrelevant: int     # 1-3
    average_score: float
    messages_drafted: int
