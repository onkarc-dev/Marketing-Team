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
    
    # Scraped Content Blocks (default to empty string if missing)
    scraped_profile_bio: str = Field(
        default="", 
        description="Scraped summary / headline / about bio from LinkedIn"
    )
    recent_posts_and_comments: str = Field(
        default="", 
        description="Scraped text from recent LinkedIn posts, articles, and comment activity"
    )
    recent_company_job_listings: str = Field(
        default="", 
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


# =====================================================================
# Web Search, Email Extraction & Cold Outreach Models
# =====================================================================

class SearchQueryRequest(BaseModel):
    """Search parameters entered by the user with batch pagination support up to 1,000 targets."""
    niche: str = Field(
        default="proprietary trading desk",
        description="Target industry niche (e.g., proprietary trading desk, quantitative family office, emerging quant fund)"
    )
    region: str = Field(
        default="London, UK",
        description="Target geographical region, city, or country"
    )
    firm_type: Optional[str] = Field(
        default="Boutique Prop Desk & Family Office (2-15 people, $10M-$50M AUM)",
        description="Target customer persona: Sweet Spot (Prop Desk/Family Office $10M-$50M AUM) or Stepping Stone (Emerging Quant Fund $50M-$250M AUM)"
    )
    num_results: int = Field(default=50, ge=1, le=1000, description="Number of firms per batch (e.g. 10, 25, 50, 100)")
    offset: int = Field(default=0, ge=0, le=1000, description="Pagination offset (e.g., 0 for 1-50, 50 for 51-100)")
    batch_range: Optional[str] = Field(default=None, description="Batch range label (e.g. '1-50', '51-100', '101-150', up to '951-1000')")
    max_target_pool: int = Field(default=1000, ge=1, le=5000, description="Total target pool capacity for country")
    sender_name: Optional[str] = Field(default="Technical Founder", description="Sender name for email signature")


class DiscoveredLead(BaseModel):
    """A target mid-market firm discovered through web search with extracted contact data."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    firm_name: str
    website: str
    region: str
    contact_name: Optional[str] = "Trading Team"
    contact_title: Optional[str] = "Portfolio Manager / Quant Lead"
    email: str
    phone: Optional[str] = None
    summary: str
    strategies_detected: List[str] = []
    website_findings: Optional[str] = Field(
        default=None,
        description="Granular findings and observations extracted after studying the firm's website/portal"
    )
    # Mid-Market Persona Attributes
    firm_segment: str = Field(
        default="Proprietary Trading Firm & Family Office",
        description="Customer tier: 'Proprietary Trading Firm & Family Office' (Sweet Spot) or 'Emerging Quantitative Fund' (Stepping Stone)"
    )
    headcount: str = Field(
        default="2–15 employees",
        description="Estimated firm headcount (2-15 for Sweet Spot, 15-40 for Stepping Stone)"
    )
    aum: str = Field(
        default="$10M – $50M AUM",
        description="Estimated AUM ($10M-$50M for Sweet Spot, $50M-$250M for Stepping Stone)"
    )
    target_decision_maker: str = Field(
        default="Founder & Lead PM",
        description="Target buyer: 'Founder & Lead PM' (no CISO bureaucracy) or 'Head of Quant Trading / CTO' (seeking SEC 15c3-5 compliance)"
    )
    core_pain_point: Optional[str] = Field(
        default="Lacks $500k/yr C++ infra team; needs turnkey low-latency FIX execution & single-tenant sandbox",
        description="Primary commercial trigger for $80k Quanteinstein deployment"
    )
    relevance_score: int = Field(default=10, ge=1, le=10)


class GeneratedEmail(BaseModel):
    """Hyper-personalized cold email crafted for a discovered firm."""
    lead_id: str
    recipient_email: str
    recipient_name: str
    firm_name: str
    website: str
    region: str
    subject: str
    body: str
    website_findings: Optional[str] = None
    value_props_used: List[str]
    word_count: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CampaignRunResponse(BaseModel):
    """Full response for automated discovery and cold email generation campaign."""
    query: SearchQueryRequest
    total_discovered: int
    offset: int = 0
    batch_range: str = "1-50"
    total_pool_size: int = 1000
    leads: List[DiscoveredLead]
    emails: List[GeneratedEmail]


class SendEmailRequest(BaseModel):
    """Payload to dispatch an email via SMTP."""
    recipient_email: str
    subject: str
    body: str
    recipient_name: Optional[str] = None
    firm_name: Optional[str] = None
    sender_email: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None


