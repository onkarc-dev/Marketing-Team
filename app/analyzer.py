"""
Core B2B Intelligence Analyst Engine for Quanteinstein.
Performs behavioral trigger extraction, intent scoring (1-10),
and hyper-personalized, peer-to-peer connection request drafting.
"""

import re
import logging
from typing import Tuple, List, Optional
from app.config import settings
from app.models import ProspectInput, AnalysisResult, TriggerSignal, EnrichedProspectRecord
from app.prompts import format_analyst_prompt
from app.llm_client import LLMClient

logger = logging.getLogger(__name__)


# =====================================================================
# Behavioral Signal Taxonomies & Keywords
# =====================================================================

PAIN_POINT_TRIGGERS = [
    {
        "pattern": r"(?:slippage|spread|friction|execution delay|fill rate|market impact)",
        "label": "Execution slippage / market friction",
        "weight": 9,
        "first_sentence_hook": "Saw your post on slippage and execution friction during volatile sessions"
    },
    {
        "pattern": r"(?:backtest(?:ing)? (?:overfitting|bias|unrealistic|divergence|discrepancy|nightmare|broken))",
        "label": "Backtester-to-live execution discrepancy",
        "weight": 10,
        "first_sentence_hook": "Saw your thoughts on backtest overfitting and live execution divergence"
    },
    {
        "pattern": r"(?:paper trading|simulat(?:ed|ion)) (?:doesn't match|vs live|unreliable|sandbox)",
        "label": "Paper trading vs live execution parity gap",
        "weight": 9,
        "first_sentence_hook": "Saw your note on the gap between paper simulation and live exchange fills"
    },
    {
        "pattern": r"(?:emotional trading|discipline|manual override|revenge trad|fat-finger|blowup)",
        "label": "Emotional execution risk / discretionary overrides",
        "weight": 9,
        "first_sentence_hook": "Saw your comment on discretionary emotional overrides sabotaging rule-based setups"
    },
    {
        "pattern": r"(?:infrastructure overhead|maintaining (?:our own|custom) (?:backtester|oms|feed|infrastructure)|reinventing the wheel)",
        "label": "Heavy quant infrastructure overhead",
        "weight": 9,
        "first_sentence_hook": "Saw your point on the infrastructure overhead of maintaining custom backtest engines"
    },
    {
        "pattern": r"(?:unstructured market intelligence|news to trade|sentiment into execution|nlp trading)",
        "label": "Bridging unstructured sentiment to deterministic execution",
        "weight": 9,
        "first_sentence_hook": "Saw your post on turning unstructured sentiment signals into deterministic parameters"
    }
]

HIRING_TRIGGERS = [
    {
        "pattern": r"(?:hiring|looking for|seeking|open role|job)[\s\S]{0,50}(?:quant(?:itative)? (?:developer|engineer|researcher|trader)|algorithmic trading|algo engineer|backtest(?:ing)? engineer|execution engineer)",
        "label": "Actively hiring Quant / Algo Execution Engineer",
        "weight": 9,
        "first_sentence_hook": "Noticed {company} is hiring a Quant Execution Engineer"
    },
    {
        "pattern": r"(?:hiring|openings?)[\s\S]{0,50}(?:risk engineer|portfolio manager|trading infrastructure|oms developer)",
        "label": "Actively hiring Trading Infrastructure / Risk Engineer",
        "weight": 9,
        "first_sentence_hook": "Saw that {company} is scaling out quantitative execution infrastructure"
    }
]

TECH_STACK_KEYWORDS = [
    "vectorbt", "backtrader", "quantconnect", "ccxt", "interactive brokers", "ibkr api",
    "pandas", "numpy", "c++", "order book", "market making", "statistical arbitrage",
    "algo trading", "quant trading", "vwap", "twap", "execution analytics", "risk engine"
]

RELEVANT_TITLES = [
    "quant", "trader", "portfolio manager", "hedge fund", "prop trader", "algorithmic",
    "head of trading", "chief investment officer", "cio", "founding partner", "managing director"
]


class B2BIntelligenceAnalyzer:
    """
    Elite B2B Intelligence Analyst engine implementing two execution tiers:
    1. LLM-based analysis via Gemini/OpenAI when available.
    2. Deterministic high-precision heuristic NLP engine with rule-based fallback.
    """

    def __init__(self):
        self.llm_client = LLMClient()

    def _count_words(self, text: Optional[str]) -> int:
        if not text:
            return 0
        return len(text.strip().split())

    def _truncate_to_max_words(self, message: str, max_words: int = 45) -> str:
        """Enforces strictly <= max_words constraint while preserving punctuation."""
        words = message.strip().split()
        if len(words) <= max_words:
            return message.strip()

        # Truncate cleanly at sentence boundary if possible
        truncated_words = words[:max_words]
        truncated_text = " ".join(truncated_words)
        
        # Ensure it closes properly with a period or question mark
        if not truncated_text.endswith((".", "?", "!")):
            # Remove trailing comma or semicolon if present
            truncated_text = re.sub(r"[,;:\-]+$", "", truncated_text) + "."
        return truncated_text

    def _ensure_single_sentence(self, text: str) -> str:
        """Ensure reasoning is strictly 1 single sentence."""
        cleaned = text.strip()
        # Find first sentence ending in period, question mark, or exclamation
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        if sentences:
            first = sentences[0].strip()
            if not first.endswith((".", "!", "?")):
                first += "."
            return first
        return cleaned

    def detect_triggers(self, prospect: ProspectInput) -> Tuple[List[TriggerSignal], int, Optional[str], Optional[str]]:
        """
        Extract behavioral signals from prospect data.
        Returns: (triggers_list, suggested_score, detected_hook, reasoning_sentence)
        """
        combined_text = (
            f"Bio: {prospect.scraped_profile_bio}\n"
            f"Posts: {prospect.recent_posts_and_comments}\n"
            f"Jobs: {prospect.recent_company_job_listings}"
        ).lower()

        posts_lower = prospect.recent_posts_and_comments.lower()
        jobs_lower = prospect.recent_company_job_listings.lower()
        bio_lower = prospect.scraped_profile_bio.lower()

        triggers: List[TriggerSignal] = []
        company_name = prospect.company or "your team"

        # Check for empty / template placeholder data
        if (
            "{scraped_profile_bio}" in prospect.scraped_profile_bio or
            "{recent_posts_and_comments}" in prospect.recent_posts_and_comments or
            "{recent_company_job_listings}" in prospect.recent_company_job_listings or
            (not prospect.scraped_profile_bio.strip() and not prospect.recent_posts_and_comments.strip())
        ):
            return [], 1, None, "No prospect information or behavioral triggers were provided in the input fields."

        # 1. Check for Active Pain Point (Score 9-10)
        for tp in PAIN_POINT_TRIGGERS:
            match = re.search(tp["pattern"], posts_lower, flags=re.IGNORECASE)
            if match:
                triggers.append(TriggerSignal(
                    category="pain_point",
                    signal=f"{tp['label']}: '{match.group(0)}'",
                    relevance_score=tp["weight"]
                ))
                hook = tp["first_sentence_hook"].format(company=company_name)
                reasoning = f"The prospect explicitly posted about {tp['label'].lower()}, representing an active pain point directly solved by Quanteinstein."
                return triggers, tp["weight"], hook, reasoning

        # 2. Check for Active Hiring Signal (Score 9-10)
        for th in HIRING_TRIGGERS:
            match = re.search(th["pattern"], jobs_lower, flags=re.IGNORECASE)
            if match:
                triggers.append(TriggerSignal(
                    category="hiring",
                    signal=f"{th['label']}: '{match.group(0)}'",
                    relevance_score=th["weight"]
                ))
                hook = th["first_sentence_hook"].format(company=company_name)
                reasoning = f"The prospect's company is actively hiring for quantitative execution and backtesting infrastructure, indicating immediate domain need."
                return triggers, th["weight"], hook, reasoning

        # 3. Check for Niche & Tech Stack Alignment (Score 8)
        found_tech = [k for k in TECH_STACK_KEYWORDS if k in combined_text]
        if len(found_tech) >= 2 and len(posts_lower.strip()) > 30:
            tech_str = ", ".join(found_tech[:2])
            triggers.append(TriggerSignal(
                category="tech_stack",
                signal=f"Posts actively on {tech_str}",
                relevance_score=8
            ))
            hook = f"Saw your technical posts on {tech_str} pipeline architecture"
            reasoning = f"The prospect actively posts about algorithmic trading strategies using relevant stack components ({tech_str})."
            return triggers, 8, hook, reasoning

        # 4. Check for Right Industry / Title but No Active Signals (Score 4-7)
        is_relevant_title = any(t in bio_lower or t in prospect.title.lower() for t in RELEVANT_TITLES)
        if is_relevant_title:
            triggers.append(TriggerSignal(
                category="title_match",
                signal="Relevant role/title in quantitative finance but no active posting or hiring signals",
                relevance_score=5
            ))
            reasoning = "Prospect matches the target quantitative finance profile, but has no recent active signals, posts, or company hiring triggers to warrant immediate outreach."
            return triggers, 5, None, reasoning

        # 5. Irrelevant (Score 1-3)
        triggers.append(TriggerSignal(
            category="none",
            signal="No quantitative or systematic trading correlation detected",
            relevance_score=2
        ))
        reasoning = "Prospect profile and company activities are outside the quantitative trading, prop desk, and systematic asset management domain."
        return triggers, 2, None, reasoning

    def draft_heuristic_message(self, hook: str) -> str:
        """
        Drafts a connection request message strictly complying with all 5 rules:
        1. Max 45 words.
        2. First sentence references exact trigger found.
        3. Peer-to-peer exchange mention (built open-source/sandbox tool).
        4. Soft, low-friction ask.
        5. Zero buzzwords, tired brilliant engineer tone.
        """
        # Template variations for engineer-to-engineer tone
        templates = [
            f"{hook}. We just built an open-source sandbox to forward-incubate strategies against real exchange friction before touching live pipes. Would love your technical feedback if open to connecting.",
            f"{hook}. I recently built a paper-trading sandbox to stress-test execution friction before routing to live broker pipes. Curious how you handle this currently.",
            f"{hook}. Put together an incubation sandbox that models historical friction without running heavy infrastructure. Would value your engineering thoughts if open to connecting."
        ]
        
        # Pick the most concise one and verify word count
        msg = templates[0]
        trimmed = self._truncate_to_max_words(msg, max_words=settings.MAX_MESSAGE_WORDS)
        return trimmed

    async def analyze_prospect(self, prospect: ProspectInput) -> EnrichedProspectRecord:
        """
        Full analysis pipeline:
        - Tries LLM if enabled and API key is present.
        - Falls back to deterministic heuristic intelligence analyst.
        - Validates all output constraints (max 45 words, 1-sentence reasoning, score 1-10, null message for score < 8).
        """
        # Step 1: Detect deterministic triggers first
        detected_triggers, heuristic_score, detected_hook, heuristic_reasoning = self.detect_triggers(prospect)

        llm_result: Optional[dict] = None
        provider_used = "heuristic"

        # Step 2: If LLM is configured, prompt it
        if settings.LLM_PROVIDER in ("gemini", "openai") and (settings.GEMINI_API_KEY or settings.OPENAI_API_KEY):
            prompt = format_analyst_prompt(prospect)
            llm_result, provider_used = await self.llm_client.generate_analysis(prompt)

        final_score: int
        final_reasoning: str
        final_message: Optional[str]

        if llm_result and isinstance(llm_result, dict) and "score" in llm_result:
            try:
                final_score = int(llm_result.get("score", heuristic_score))
                final_score = max(1, min(10, final_score))
                raw_reasoning = str(llm_result.get("reasoning", heuristic_reasoning))
                final_reasoning = self._ensure_single_sentence(raw_reasoning)
                raw_message = llm_result.get("message")
                
                if final_score >= settings.MIN_SCORE_FOR_OUTREACH and raw_message:
                    final_message = self._truncate_to_max_words(str(raw_message), max_words=settings.MAX_MESSAGE_WORDS)
                else:
                    final_message = None
            except Exception as e:
                logger.warning(f"Error parsing LLM result, using heuristic fallback: {e}")
                final_score = heuristic_score
                final_reasoning = self._ensure_single_sentence(heuristic_reasoning)
                final_message = self.draft_heuristic_message(detected_hook) if final_score >= 8 and detected_hook else None
        else:
            final_score = heuristic_score
            final_reasoning = self._ensure_single_sentence(heuristic_reasoning)
            final_message = self.draft_heuristic_message(detected_hook) if final_score >= 8 and detected_hook else None

        # Double check message constraint
        if final_score < settings.MIN_SCORE_FOR_OUTREACH:
            final_message = None

        word_count = self._count_words(final_message)

        # Categorize intent tier
        if final_score >= 9:
            intent_tier = "High Intent (Urgent Pain / Hiring)"
        elif final_score == 8:
            intent_tier = "Strong Match (Tech Stack & Niche)"
        elif final_score >= 4:
            intent_tier = "Qualified Pass (ICP / Inactive)"
        else:
            intent_tier = "Irrelevant Pass"

        return EnrichedProspectRecord(
            id=prospect.id,
            name=prospect.name or "Prospect",
            company=prospect.company or "",
            title=prospect.title or "",
            linkedin_url=prospect.linkedin_url or "",
            scraped_profile_bio=prospect.scraped_profile_bio,
            recent_posts_and_comments=prospect.recent_posts_and_comments,
            recent_company_job_listings=prospect.recent_company_job_listings,
            score=final_score,
            intent_tier=intent_tier,
            reasoning=final_reasoning,
            message=final_message,
            word_count=word_count,
            triggers=detected_triggers
        )

    def to_strict_json(self, record: EnrichedProspectRecord) -> dict:
        """Returns the EXACT strict JSON structure required by the specification."""
        return {
            "score": record.score,
            "reasoning": record.reasoning,
            "message": record.message
        }
