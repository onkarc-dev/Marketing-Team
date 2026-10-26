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
    BatchAnalysisRequest, BatchAnalysisResponse, SystemStats
)
from app.analyzer import B2BIntelligenceAnalyzer
from app.storage import ProspectStorage

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


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "provider": settings.LLM_PROVIDER,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "openai_configured": bool(settings.OPENAI_API_KEY)
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
        "openai_model": settings.OPENAI_MODEL
    }


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


# Mount static directory for frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    """Serve the web dashboard."""
    return FileResponse("app/static/index.html")
