"""
FastAPI REST API and Web Dashboard Server for Quanteinstein B2B Intelligence Engine.
"""

import io
import csv
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.models import (
    ProspectInput, AnalysisResult, EnrichedProspectRecord,
    BatchAnalysisRequest, BatchAnalysisResponse, SystemStats,
    SearchQueryRequest, DiscoveredLead, GeneratedEmail, CampaignRunResponse,
    SendEmailRequest
)
from app.analyzer import B2BIntelligenceAnalyzer
from app.storage import ProspectStorage
from app.discovery import WebDiscoveryEngine
from app.email_generator import EmailOutreachGenerator
from app.email_sender import EmailDispatcher

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Quanteinstein B2B Intelligence Engine",
    description="Analyzes scraped LinkedIn prospect data for high intent and generates hyper-personalized connection requests.",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = B2BIntelligenceAnalyzer()
storage = ProspectStorage()
discovery_engine = WebDiscoveryEngine()
email_generator = EmailOutreachGenerator()

# In-memory store for generated cold emails during session
active_campaign_emails: List[GeneratedEmail] = []


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "provider": settings.LLM_PROVIDER,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "smtp_configured": bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
        "smtp_user": settings.SMTP_USER or ""
    }


@app.get("/api/config")
async def get_config():
    """Returns current project context, audience, and constraints."""
    return {
        "project_name": settings.PROJECT_NAME,
        "project_context": settings.PROJECT_CONTEXT,
        "target_audience": settings.TARGET_AUDIENCE,
        "max_words": settings.MAX_MESSAGE_WORDS,
        "min_score_for_outreach": settings.MIN_SCORE_FOR_OUTREACH,
        "llm_provider": settings.LLM_PROVIDER,
        "gemini_model": settings.GEMINI_MODEL,
        "openai_model": settings.OPENAI_MODEL,
        "smtp_configured": bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
        "smtp_user": settings.SMTP_USER or ""
    }


@app.post("/api/smtp/test")
async def test_smtp():
    """Tests the SMTP connection using configured .env credentials."""
    return EmailDispatcher.test_connection()



@app.post("/api/analyze/strict", response_model=AnalysisResult)
async def analyze_strict(prospect: ProspectInput):
    """
    Analyzes prospect and returns STRICTLY the 3 fields requested by user:
    {
      "score": [Integer 1-10],
      "reasoning": "[1 sentence]",
      "message": "[Drafted message or null]"
    }
    """
    record = await analyzer.analyze_prospect(prospect)
    storage.save_prospect(record)
    return analyzer.to_strict_json(record)


@app.post("/api/analyze", response_model=EnrichedProspectRecord)
async def analyze_prospect_enriched(prospect: ProspectInput):
    """Analyzes a prospect and returns full enriched record including word count and triggers."""
    record = await analyzer.analyze_prospect(prospect)
    storage.save_prospect(record)
    return record


@app.post("/api/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(batch: BatchAnalysisRequest):
    """Analyzes multiple prospects in a single batch request."""
    results: List[EnrichedProspectRecord] = []
    for p in batch.prospects:
        record = await analyzer.analyze_prospect(p)
        storage.save_prospect(record)
        results.append(record)

    total = len(results)
    high_intent = sum(1 for r in results if r.score >= settings.MIN_SCORE_FOR_OUTREACH)
    passed = total - high_intent
    avg_score = round(sum(r.score for r in results) / total, 1) if total > 0 else 0.0

    return BatchAnalysisResponse(
        total=total,
        high_intent_count=high_intent,
        passed_count=passed,
        average_score=avg_score,
        results=results
    )


@app.post("/api/upload-csv", response_model=BatchAnalysisResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV of scraped LinkedIn prospects and analyze all rows."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    content = await file.read()
    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_content = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text_content))
    prospects: List[ProspectInput] = []

    for idx, row in enumerate(reader):
        # Flexible key mapping for common scrapers (Phantombuster, Apify, Bright Data, CSV exports)
        bio = (
            row.get("scraped_profile_bio") or row.get("bio") or row.get("about") or 
            row.get("headline") or row.get("summary") or ""
        )
        posts = (
            row.get("recent_posts_and_comments") or row.get("posts") or 
            row.get("recent_posts") or row.get("comments") or row.get("activity") or ""
        )
        jobs = (
            row.get("recent_company_job_listings") or row.get("job_listings") or 
            row.get("jobs") or row.get("company_hiring") or ""
        )
        name = row.get("name") or row.get("full_name") or f"Prospect #{idx+1}"
        company = row.get("company") or row.get("company_name") or ""
        title = row.get("title") or row.get("job_title") or ""
        url = row.get("linkedin_url") or row.get("profile_url") or row.get("url") or ""

        prospects.append(ProspectInput(
            name=name,
            company=company,
            title=title,
            linkedin_url=url,
            scraped_profile_bio=bio,
            recent_posts_and_comments=posts,
            recent_company_job_listings=jobs
        ))

    return await analyze_batch(BatchAnalysisRequest(prospects=prospects))


@app.get("/api/prospects", response_model=List[EnrichedProspectRecord])
async def list_prospects(
    min_score: Optional[int] = Query(None, ge=1, le=10),
    limit: int = Query(100, ge=1, le=500)
):
    """Retrieve saved prospects from storage."""
    return storage.get_prospects(min_score=min_score, limit=limit)


@app.get("/api/stats", response_model=SystemStats)
async def get_stats():
    """Retrieve current system and campaign metrics."""
    return storage.get_stats()


@app.get("/api/export")
async def export_prospects_csv(min_score: int = Query(8, ge=1, le=10)):
    """Export qualified leads with their drafted connection requests as a CSV."""
    records = storage.get_prospects(min_score=min_score, limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Name", "Company", "Title", "LinkedIn URL",
        "Score", "Intent Tier", "Reasoning", "Message", "Word Count", "Created At"
    ])
    for r in records:
        writer.writerow([
            r.id, r.name, r.company, r.title, r.linkedin_url,
            r.score, r.intent_tier, r.reasoning, r.message or "", r.word_count, r.created_at
        ])
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=quanteinstein_outreach_score_{min_score}+.csv"}
    )


# =====================================================================
# Regional Web Search, Firm Analysis & Cold Email Endpoints
# =====================================================================

@app.post("/api/discovery/search", response_model=List[DiscoveredLead])
async def search_firms(query: SearchQueryRequest):
    """Search Google/web for firms in the specified region and niche, extracting contact emails."""
    leads = await discovery_engine.search_and_discover(query)
    return leads


@app.post("/api/discovery/generate-email", response_model=GeneratedEmail)
async def generate_firm_email(lead: DiscoveredLead, sender_name: str = Query("Technical Founder")):
    """Analyze a single firm's work and generate a tailored cold email for Quanteinstein."""
    email = await email_generator.generate_email(lead, sender_name=sender_name)
    active_campaign_emails.append(email)
    return email


@app.post("/api/discovery/run-campaign", response_model=CampaignRunResponse)
async def run_full_discovery_campaign(query: SearchQueryRequest):
    """
    End-to-End Pipeline:
    1. Searches the web for firms in the specified region and niche.
    2. Scrapes/identifies firm websites, strategies, and contact emails.
    3. Deeply analyzes their work against Quanteinstein's modular sandbox.
    4. Drafts a tailored, hyper-personalized B2B cold email for each firm.
    """
    leads = await discovery_engine.search_and_discover(query)
    emails: List[GeneratedEmail] = []
    
    sender = query.sender_name or "Technical Founder"
    for lead in leads:
        em = await email_generator.generate_email(lead, sender_name=sender)
        emails.append(em)
        active_campaign_emails.append(em)

    batch_label = query.batch_range or f"{query.offset + 1}-{query.offset + len(leads)}"

    return CampaignRunResponse(
        query=query,
        total_discovered=len(leads),
        offset=query.offset,
        batch_range=batch_label,
        total_pool_size=query.max_target_pool,
        leads=leads,
        emails=emails
    )


@app.get("/api/discovery/export-emails")
async def export_campaign_emails():
    """Export all generated cold emails and follow-up sequences to CSV for email sequencing tools."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Lead ID", "Firm Name", "Region", "Recipient Name", "Recipient Email",
        "Website", "Subject Line", "Email Body", "The Ask",
        "Follow-Up 1 Subject", "Follow-Up 1 Body", "Follow-Up 1 Delay Days",
        "Follow-Up 2 Subject", "Follow-Up 2 Body", "Follow-Up 2 Delay Days",
        "Follow-Up 3 Subject", "Follow-Up 3 Body", "Follow-Up 3 Delay Days",
        "Value Props", "Word Count", "Created At"
    ])
    for em in active_campaign_emails:
        fu1 = em.follow_ups[0] if len(em.follow_ups) > 0 else None
        fu2 = em.follow_ups[1] if len(em.follow_ups) > 1 else None
        fu3 = em.follow_ups[2] if len(em.follow_ups) > 2 else None

        writer.writerow([
            em.lead_id, em.firm_name, em.region, em.recipient_name, em.recipient_email,
            em.website, em.subject, em.body, em.the_ask or "",
            fu1.subject if fu1 else "", fu1.body if fu1 else "", fu1.delay_days if fu1 else "",
            fu2.subject if fu2 else "", fu2.body if fu2 else "", fu2.delay_days if fu2 else "",
            fu3.subject if fu3 else "", fu3.body if fu3 else "", fu3.delay_days if fu3 else "",
            "; ".join(em.value_props_used), em.word_count, em.created_at
        ])
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=quanteinstein_cold_outreach_emails.csv"}
    )


@app.post("/api/discovery/send-email")
async def send_single_email(req: SendEmailRequest):
    """Dispatches a single cold outreach email directly via user's SMTP/Gmail account."""
    result = EmailDispatcher.send_email(
        recipient_email=req.recipient_email,
        subject=req.subject,
        body=req.body,
        sender_email=req.sender_email,
        smtp_password=req.smtp_password,
        smtp_host=req.smtp_host,
        smtp_port=req.smtp_port
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    # Record email in sent suppression list to prevent duplicate outreach
    firm_name = req.firm_name or ""
    if not firm_name:
        for em in active_campaign_emails:
            if em.recipient_email.strip().lower() == req.recipient_email.strip().lower():
                firm_name = em.firm_name
                break

    storage.record_sent_email(
        recipient_email=req.recipient_email,
        recipient_name=req.recipient_name or "",
        firm_name=firm_name,
        subject=req.subject,
        status="sent"
    )

    return result


@app.get("/api/discovery/sent-emails")
async def get_sent_emails():
    """Returns all contacted firms and recipient emails."""
    sent_list = list(storage.get_sent_emails())
    return {
        "sent_count": len(sent_list),
        "sent_emails": sent_list,
        "sent_firms": list(storage.get_sent_firms()),
        "records": storage.get_sent_records()
    }


@app.post("/api/discovery/clear-sent-emails")
async def clear_sent_emails():
    """Clears sent history (suppression list reset)."""
    storage.clear_sent_history()
    return {"message": "Sent suppression list cleared successfully."}



# Mount static directory for frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    """Serve the web dashboard."""
    return FileResponse("app/static/index.html")
