"""
Hyper-Personalized Cold Email Generator for Quanteinstein B2B Outreach.
Analyzes discovered firm profile, maps their work to Quanteinstein modules,
and generates high-converting, professional cold emails.
"""

import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import DiscoveredLead, GeneratedEmail
from app.llm_client import LLMClient

logger = logging.getLogger(__name__)

EMAIL_PROMPT_TEMPLATE = """You are a technical founder of Quanteinstein writing a high-converting, highly tailored B2B cold email to a quantitative trading firm or emerging hedge fund.

### TARGET PROSPECT INFORMATION
Firm Name: {firm_name}
Website: {website}
Region / Location: {region}
Contact Person: {contact_name} ({contact_title})
Summary of Their Work: {summary}
Detected Strategies / Focus: {strategies}

### OUR PROJECT: QUANTEINSTEIN
Value Proposition: "{project_context}"
Target Audience: "{target_audience}"
Key Modules:
- AI Quant Coach: Formulate mathematical parameters from unstructured market intelligence.
- Visual Strategy Builder: Build algorithmic execution rules without code-heavy infrastructure overhead.
- Historical Backtester: Stress-test rules against historical friction, spread degradation, and queue slippage.
- Live Charting & Trade Journal: Comprehensive quantitative attribution.
- Risk-Guarded Paper Sandbox: 100% paper-simulated incubation before routing orders to live exchange pipes.

### STRICT RULES FOR COLD EMAIL
1. Subject line: 3-6 words, direct, lowercase engineer style (e.g. "sandbox for {firm_name}'s execution", "paper simulation before live pipes at {firm_name}").
2. Opening: First sentence must directly acknowledge their specific work, strategies, and firm location.
3. The Bridge: Explain how Quanteinstein integrates into their exact workflow—stress-testing their strategies against historical friction and forward-incubating them in a 100% paper-simulated sandbox before routing to live broker/exchange pipes.
4. Tone: Technical founder to quant lead. Professional, concise, zero marketing buzzwords or generic hype.
5. CTA: Soft, low-friction ask (e.g. "Open to taking a quick look at the sandbox or sharing how your desk currently handles execution parity?").
6. Length: Under 160 words.

### OUTPUT FORMAT
Output valid JSON only:
{{
  "subject": "[Subject Line]",
  "body": "[Full Email Body]",
  "value_props_used": ["[Module 1]", "[Module 2]"]
}}
"""


class EmailOutreachGenerator:
    """Generates tailored cold emails bridging prospect work to Quanteinstein."""

    def __init__(self):
        self.llm_client = LLMClient()

    def draft_heuristic_email(self, lead: DiscoveredLead, sender_name: str = "Technical Founder") -> GeneratedEmail:
        """
        Generates a deterministic high-converting cold email tailored to the firm's focus.
        Guaranteed to work offline and produce high quality, tailored copy.
        """
        strategies_str = ", ".join(lead.strategies_detected[:2]) if lead.strategies_detected else "quantitative strategies"
        primary_strategy = lead.strategies_detected[0] if lead.strategies_detected else "algorithmic execution"

        # Construct tailored subject line
        subject_options = [
            f"sandbox for {lead.firm_name}'s {primary_strategy.lower()}",
            f"paper simulation before live pipes at {lead.firm_name}",
            f"{lead.firm_name} • strategy incubation sandbox"
        ]
        subject = subject_options[0]

        # Construct recipient salutation
        salutation = f"Hi {lead.contact_name.split()[0]}," if lead.contact_name and lead.contact_name != "Trading Team" else f"Hi {lead.firm_name} Team,"

        # Construct tailored body
        body = f"""{salutation}

Saw your work at {lead.firm_name} in {lead.region} deploying {strategies_str}.

We built Quanteinstein—a risk-guarded strategy incubation and paper-trading sandbox that bridges unstructured market intelligence into deterministic algorithmic execution. 

Instead of burning engineering cycles maintaining custom backtesters or risking capital on live execution divergence, our suite (AI Quant Coach, Visual Strategy Builder, and Historical Backtester) allows your desk to formulate mathematical parameters, stress-test rules against real exchange friction, and forward-incubate models in a 100% paper-simulated sandbox before routing orders to live broker pipes.

Curious how your team currently benchmarks execution parity before deploying to live pipes. Would you be open to a brief 10-minute technical exchange or test access to the sandbox?

Best,
{sender_name}
Quanteinstein | Strategy Incubation Sandbox
https://quanteinstein.io"""

        word_count = len(body.split())
        value_props = [
            "100% Paper-Simulated Incubation Sandbox",
            "Historical Exchange Friction & Slippage Modeling",
            "Zero Infrastructure Overhead for Emerging Desks"
        ]

        return GeneratedEmail(
            lead_id=lead.id,
            recipient_email=lead.email,
            recipient_name=lead.contact_name or "Trading Desk",
            firm_name=lead.firm_name,
            website=lead.website,
            region=lead.region,
            subject=subject,
            body=body,
            value_props_used=value_props,
            word_count=word_count
        )

    async def generate_email(self, lead: DiscoveredLead, sender_name: str = "Technical Founder") -> GeneratedEmail:
        """
        Generates tailored email using LLM if available, otherwise falls back to deterministic engine.
        """
        if settings.LLM_PROVIDER in ("gemini", "openai") and (settings.GEMINI_API_KEY or settings.OPENAI_API_KEY):
            prompt = EMAIL_PROMPT_TEMPLATE.format(
                firm_name=lead.firm_name,
                website=lead.website,
                region=lead.region,
                contact_name=lead.contact_name or "Trading Lead",
                contact_title=lead.contact_title or "Quantitative Portfolio Manager",
                summary=lead.summary,
                strategies=", ".join(lead.strategies_detected),
                project_context=settings.PROJECT_CONTEXT,
                target_audience=settings.TARGET_AUDIENCE
            )

            result, provider = await self.llm_client.generate_analysis(prompt)
            if result and isinstance(result, dict) and "subject" in result and "body" in result:
                subject = str(result["subject"]).strip()
                body = str(result["body"]).strip()
                value_props = result.get("value_props_used", ["Paper Sandbox", "Execution Analytics"])
                return GeneratedEmail(
                    lead_id=lead.id,
                    recipient_email=lead.email,
                    recipient_name=lead.contact_name or "Trading Desk",
                    firm_name=lead.firm_name,
                    website=lead.website,
                    region=lead.region,
                    subject=subject,
                    body=body,
                    value_props_used=value_props,
                    word_count=len(body.split())
                )

        return self.draft_heuristic_email(lead, sender_name=sender_name)
