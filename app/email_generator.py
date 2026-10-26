"""
Hyper-Personalized Cold Email Generator for Quanteinstein B2B Outreach.
Analyzes discovered firm profile, maps their work to Quanteinstein modules,
and generates high-converting, professional, and authentic cold emails.
"""

import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import DiscoveredLead, GeneratedEmail
from app.llm_client import LLMClient

logger = logging.getLogger(__name__)

EMAIL_PROMPT_TEMPLATE = """You are a technical founder of Quanteinstein writing a high-converting, highly tailored B2B cold email to a quantitative trading firm, prop desk, or emerging hedge fund.

### TARGET PROSPECT INFORMATION
Firm Name: {firm_name}
Website: {website}
Region / Location: {region}
Contact Person: {contact_name} ({contact_title})
Summary of Their Work: {summary}
Detected Strategies / Focus: {strategies}

### OUR PROJECT: QUANTEINSTEIN
Website: https://quanteinstein.com
Platform Concept: Risk-guarded quantitative strategy incubation and paper-trading environment that allows traders to formulate mathematical parameters, stress-test rules against historical exchange friction, and forward-incubate models in a simulated live environment before routing orders to live broker pipes.
Target Audience: {target_audience}

### STRICT COPYWRITING RULES
1. Salutation:
   - If contact is a real person (e.g. Doug Greenig, Marcus Kane), use "Hi Firstname,".
   - If contact is a team or desk (e.g. Systematic Research Team, Algorithmic Execution Desk), DO NOT say "Hi Systematic,". Say "Hi {firm_name} Team," or "Hi {firm_name} Research Desk,".
2. Subject Line:
   - 4-8 words. Sharp, professional, and personalized to their firm and strategy.
   - Example: "{firm_name} • execution friction & forward model testing" or "Execution parity before live pipes at {firm_name}".
   - Zero generic marketing gimmicks.
3. Tone & Style:
   - Trader/engineer to trader/engineer. Professional, technical, concise.
   - ZERO meaningless buzzwords. Do NOT repeat the word "sandbox" over and over.
   - Focus on tangible friction: fill divergence, spread widening, queue delays, and forward testing before live capital.
4. Body Structure:
   - Sentence 1: Acknowledge their specific firm, strategies, and location.
   - Paragraph 2: Address the core quant pain point: backtest-to-live execution divergence and infrastructure overhead.
   - Paragraph 3: Introduce Quanteinstein (https://quanteinstein.com) as the solution to stress-test against historical friction and forward-test live fills before broker allocation.
   - 3 crisp bullet points highlighting capabilities for their trading style.
   - Call to Action: Soft, professional, low-friction exchange.
   - Always include the correct website: https://quanteinstein.com.
5. Length: 120-160 words.

### OUTPUT FORMAT
Output valid JSON only:
{{
  "subject": "[Sharp Subject Line]",
  "body": "[Full Email Body]",
  "value_props_used": ["[Capability 1]", "[Capability 2]"]
}}
"""


class EmailOutreachGenerator:
    """Generates tailored cold emails bridging prospect work to Quanteinstein."""

    def __init__(self):
        self.llm_client = LLMClient()

    @staticmethod
    def format_salutation(lead: DiscoveredLead) -> str:
        """
        Formats a natural, professional salutation.
        Avoids bugs like 'Hi Systematic,' or 'Hi Algorithmic,'.
        """
        contact = (lead.contact_name or "").strip()
        team_keywords = [
            "team", "desk", "group", "capital", "partners", "trading",
            "research", "analytics", "execution", "firm", "associates", "lab", "labs"
        ]

        if not contact or any(k in contact.lower() for k in team_keywords):
            firm_short = lead.firm_name.split("/")[0].strip()
            if "research" in contact.lower():
                return f"Hi {firm_short} Research Team,"
            elif "execution" in contact.lower() or "trading" in contact.lower():
                return f"Hi {firm_short} Execution Desk,"
            else:
                return f"Hi {firm_short} Team,"

        # It's an individual person's name (e.g. "Doug Greenig", "Marcus Kane")
        first_name = contact.split()[0]
        return f"Hi {first_name},"

    @staticmethod
    def format_subject_line(lead: DiscoveredLead) -> str:
        """Constructs a sharp, smart, personalized, professional subject line."""
        primary_strategy = lead.strategies_detected[0] if lead.strategies_detected else "quantitative execution"
        strat_lower = primary_strategy.lower()

        if "stat" in strat_lower or "arbitrage" in strat_lower or "volatility" in strat_lower:
            return f"{lead.firm_name} • fill parity & execution friction in stat arb"
        elif "trend" in strat_lower or "macro" in strat_lower:
            return f"{lead.firm_name} • execution friction & forward model testing"
        elif "alternative" in strat_lower or "exotic" in strat_lower:
            return f"{lead.firm_name} • fill parity in alternative markets"
        elif "futures" in strat_lower or "execution" in strat_lower or "order" in strat_lower:
            return f"{lead.firm_name} • execution parity before live broker pipes"
        else:
            return f"{lead.firm_name} • quantitative strategy testing & paper execution"

    def draft_heuristic_email(self, lead: DiscoveredLead, sender_name: Optional[str] = None) -> GeneratedEmail:
        """
        Generates a deterministic, highly tailored, buzzword-free cold email.
        Grounds every sentence in real quantitative trading reality.
        """
        strategies_str = ", ".join(lead.strategies_detected[:2]) if lead.strategies_detected else "quantitative strategies"
        primary_strat = lead.strategies_detected[0] if lead.strategies_detected else "quantitative models"
        strat_lower = primary_strat.lower()

        # Subject line
        subject = self.format_subject_line(lead)

        # Salutation
        salutation = self.format_salutation(lead)

        # Sender resolution
        clean_sender = sender_name or getattr(settings, "SENDER_NAME", "Onkar (Founder, Quanteinstein)")
        if not clean_sender or clean_sender == "Technical Founder":
            clean_sender = "Onkar\nFounder, Quanteinstein"

        # Strategy-specific context tailoring
        if "stat" in strat_lower or "volatility" in strat_lower:
            friction_focus = "spread friction eroding thin edges, order queue latency, and execution divergence between theoretical models and live fills"
            bullet_1 = "Execution Friction Modeling: Stress-test strategies against real historical bid-ask spreads and order queue delays."
            bullet_2 = "Live Feed Paper Testing: Forward-test strategies against real-time exchange data to verify fill parity before committing capital."
            bullet_3 = "Strategy Parameterization: Translate quantitative rules into deterministic execution without custom engine overhead."
        elif "trend" in strat_lower or "macro" in strat_lower:
            friction_focus = "slippage during market regime shifts, execution drag across fragmented contracts, and backtest overfitting"
            bullet_1 = "Friction-Aware Backtesting: Simulate execution against historical volatility spikes and liquidity gaps."
            bullet_2 = "Simulated Forward Testing: Run paper execution side-by-side with live feeds to benchmark true fill fidelity."
            bullet_3 = "Visual Strategy Builder: Refine mathematical parameters and stop protocols without rewriting low-level infrastructure."
        elif "alternative" in strat_lower or "exotic" in strat_lower:
            friction_focus = "wide bid-ask spreads, low liquidity order books, and model divergence when transitioning from research to live trading"
            bullet_1 = "Illiquid Book Modeling: Benchmark slippage and spread widening across alternative and exotic instruments."
            bullet_2 = "Risk-Guarded Forward Testing: Validate execution logic in simulated conditions before routing orders to live broker pipes."
            bullet_3 = "Trade Journal & Attribution: Audit fill quality, slippage variance, and trade attribution in real time."
        else:
            friction_focus = "execution slippage, queue priority degradation, and the divergence between clean backtests and live broker fills"
            bullet_1 = "Friction-Aware Backtesting: Stress-test quantitative rules against realistic spread and slippage friction."
            bullet_2 = "Forward Paper Incubation: Validate execution logic with live market data before turning on live broker pipes."
            bullet_3 = "Strategy Formulation Suite: Build and refine algorithmic rules with zero custom infrastructure maintenance."

        body = f"""{salutation}

Followed your desk's work at {lead.firm_name} in {lead.region} deploying {strategies_str}.

When models transition from research into live trading, the main bottleneck is execution divergence—backtests looking pristine while {friction_focus}.

We built Quanteinstein (https://quanteinstein.com) to let quant teams stress-test rules against realistic market friction and forward-test execution before deploying capital to live pipes.

Key capabilities for your desk:
• {bullet_1}
• {bullet_2}
• {bullet_3}

Platform overview: https://quanteinstein.com

Curious how your team benchmarks execution parity before going live. Open to a brief 10-minute technical exchange this week?

Best regards,
{clean_sender}
https://quanteinstein.com"""



        word_count = len(body.split())
        value_props = [
            "Friction-Aware Historical Backtesting",
            "Forward-Testing with Simulated Live Fills",
            "Execution Parity Verification Before Live Pipes"
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

    async def generate_email(self, lead: DiscoveredLead, sender_name: Optional[str] = None) -> GeneratedEmail:
        """
        Generates tailored email using LLM if available, otherwise falls back to deterministic engine.
        """
        clean_sender = sender_name or getattr(settings, "SENDER_NAME", "Onkar (Founder, Quanteinstein)")

        if settings.LLM_PROVIDER in ("gemini", "openai") and (settings.GEMINI_API_KEY or settings.OPENAI_API_KEY):
            prompt = EMAIL_PROMPT_TEMPLATE.format(
                firm_name=lead.firm_name,
                website=lead.website,
                region=lead.region,
                contact_name=lead.contact_name or "Trading Lead",
                contact_title=lead.contact_title or "Quantitative Portfolio Manager",
                summary=lead.summary,
                strategies=", ".join(lead.strategies_detected),
                target_audience=settings.TARGET_AUDIENCE
            )

            result, provider = await self.llm_client.generate_analysis(prompt)
            if result and isinstance(result, dict) and "subject" in result and "body" in result:
                subject = str(result["subject"]).strip()
                body = str(result["body"]).strip()
                # Ensure correct link is always present
                if "quanteinstein.com" not in body:
                    body += "\n\nhttps://quanteinstein.com"
                value_props = result.get("value_props_used", ["Friction Modeling", "Execution Testing"])
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

        return self.draft_heuristic_email(lead, sender_name=clean_sender)
