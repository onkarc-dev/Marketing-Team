"""
Hyper-Personalized Cold Email Generator for Quanteinstein B2B Outreach.
Analyzes discovered firm profile, studied website/portal findings, and
crafts authentic, high-converting, human-sounding cold emails with varied subject lines.
Zero robotic bullet points, zero spam buzzwords, 100% grounded in institutional quant realities.
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import DiscoveredLead, GeneratedEmail
from app.llm_client import LLMClient

logger = logging.getLogger(__name__)

EMAIL_PROMPT_TEMPLATE = """You are Onkar, technical founder of Quanteinstein (https://quanteinstein.com), writing a highly tailored 1-on-1 cold email to a quantitative trading desk or emerging hedge fund.

### TARGET PROSPECT INTELLIGENCE
Firm Name: {firm_name}
Website: {website}
Region / Location: {region}
Contact Person: {contact_name} ({contact_title})
Summary of Their Work: {summary}
Detected Strategies / Focus: {strategies}
Studied Website Findings: {website_findings}

### OUR PLATFORM: QUANTEINSTEIN
Website: https://quanteinstein.com
What Quanteinstein Does: A risk-guarded strategy incubation and forward-simulation sandbox for quants. It allows quants to formulate mathematical parameters, stress-test rules against historical exchange friction (bid-ask spreads, queue priority delays), and forward-simulate models on live exchange feeds to verify fill parity before routing capital to live broker pipes.

### STRICT COPYWRITING RULES
1. Salutation:
   - If contact is an individual (e.g. Doug Greenig, Marcus Vance), use "Hi Firstname,".
   - If contact is a desk/team (e.g. Systematic Research Team), say "Hi {firm_name} Research Team," or "Hi {firm_name} Trading Desk,". Never say "Hi Systematic,".
2. Subject Line:
   - 4-8 words. Natural, authentic, conversational.
   - Examples:
     * "{firm_name} • execution drag & forward testing in {primary_strategy}"
     * "question on {firm_name}'s {primary_strategy} execution"
     * "{primary_strategy} fill parity at {firm_name}"
     * "{firm_name} / Quanteinstein: paper-testing {primary_strategy}"
3. Tone & Structure:
   - Natural email from a technical founder who visited their site and studied their work.
   - Sentence 1: Mention finding them and studying their site / portal regarding their specific strategy.
   - Paragraph 2: Point out the tangible execution challenge in their specific strategy (queue latency, spread widening at market open, backtest-to-live execution divergence).
   - Paragraph 3: Introduce Quanteinstein (https://quanteinstein.com) as the risk-guarded incubation sandbox that lets quants test against historical friction and forward-test live fills before broker pipes.
   - Paragraph 4: Low-friction CTA (e.g. "Curious how your team currently benchmarks execution parity before going live. Would you be open to a 10-minute technical exchange this week?").
   - Sign-off: "Best regards,\nOnkar (Founder, Quanteinstein)\nhttps://quanteinstein.com"
4. ZERO BULLET POINTS: Write natural conversational prose paragraphs only.
5. ZERO JARGON BUZZWORDS: Do not repeat "sandbox" repeatedly. Keep word count crisp (100-140 words).

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
            firm_clean = re.sub(r'\s+(trading\s+desk|desk|team|group)$', '', firm_short, flags=re.IGNORECASE)
            if "research" in contact.lower():
                return f"Hi {firm_clean} Research Team,"
            elif "execution" in contact.lower() or "trading" in contact.lower():
                return f"Hi {firm_clean} Trading Desk,"
            else:
                return f"Hi {firm_clean} Team,"

        # Real individual person's name (e.g. "Doug Greenig", "Marcus Kane", "Alexei Voronov")
        first_name = contact.split()[0]
        return f"Hi {first_name},"

    @staticmethod
    def get_strategy_slug(lead: DiscoveredLead) -> str:
        """Extracts a short, natural strategy descriptor for subject lines."""
        primary_strat = lead.strategies_detected[0] if lead.strategies_detected else "quantitative models"
        strat_lower = primary_strat.lower()

        if "futures" in strat_lower:
            return "futures execution"
        elif "crypto" in strat_lower or "digital" in strat_lower:
            return "crypto arbitrage"
        elif "forex" in strat_lower or "fx" in strat_lower:
            return "FX carry models"
        elif "trend" in strat_lower or "macro" in strat_lower:
            return "systematic macro"
        elif "volatility" in strat_lower or "dispersion" in strat_lower or "option" in strat_lower:
            return "volatility dispersion"
        elif "stat" in strat_lower or "arbitrage" in strat_lower:
            return "stat arb"
        elif "market make" in strat_lower or "hft" in strat_lower:
            return "market making"
        elif "alternative" in strat_lower or "exotic" in strat_lower:
            return "alternative markets"
        else:
            return "algorithmic models"

    def format_subject_line(self, lead: DiscoveredLead, variation_idx: int = 0) -> str:
        """
        Constructs a sharp, smart, personalized, professional subject line.
        Rotates among 6 organic styles so multiple emails in a campaign don't repeat the same subject.
        """
        strat_short = self.get_strategy_slug(lead)
        firm = lead.firm_name

        templates = [
            f"{firm} • execution drag & forward testing in {strat_short}",
            f"question on {firm}'s {strat_short} execution",
            f"{strat_short} fill parity at {firm}",
            f"{firm} / Quanteinstein: paper-testing {strat_short}",
            f"quick question re: {firm}'s forward simulation workflow",
            f"minimizing slippage before live pipes at {firm}"
        ]

        return templates[variation_idx % len(templates)]

    def draft_heuristic_email(self, lead: DiscoveredLead, sender_name: Optional[str] = None) -> GeneratedEmail:
        """
        Generates a deterministic, highly tailored, human-sounding cold email.
        Grounds every sentence in actual website analysis and real quantitative trading realities.
        Rotates across 4 distinct copywriting frameworks to guarantee variety across leads.
        """
        # Deterministic seed for variety based on firm name + email
        hash_seed = int(hashlib.md5(f"{lead.firm_name}_{lead.email}".encode()).hexdigest(), 16)
        framework_idx = hash_seed % 4
        subject_idx = (hash_seed >> 2) % 6

        # Salutation & Subject
        salutation = self.format_salutation(lead)
        subject = self.format_subject_line(lead, variation_idx=subject_idx)

        # Strategies & market focus
        strategies_str = ", ".join(lead.strategies_detected[:2]) if lead.strategies_detected else "quantitative strategies"
        primary_strat = lead.strategies_detected[0] if lead.strategies_detected else "quantitative models"
        strat_lower = primary_strat.lower()

        if "futures" in strat_lower:
            market_focus = "algorithmic futures and multi-asset contract execution"
            specific_friction = "spread widening during rollover windows and queue latency across liquid contracts"
            sandbox_benefit = "stress-test execution parameters against historical spread friction and benchmark paper fills on live feeds"
            value_prop = "full forward-incubation of futures rules without burning cycles on bespoke paper harnesses"
        elif "crypto" in strat_lower or "digital" in strat_lower:
            market_focus = "24/7 digital asset order books and cross-venue arbitrage"
            specific_friction = "leg execution latency, rate-limit delays, and cross-exchange slippage erasing edge"
            sandbox_benefit = "forward-test multi-venue execution against real-time exchange order books before risking capital"
            value_prop = "benchmark true fill fidelity across venues without building bespoke crypto simulation infrastructure"
        elif "trend" in strat_lower or "macro" in strat_lower:
            market_focus = "multi-asset futures and global trend momentum"
            specific_friction = "slippage during sharp regime shifts, contract rollover drag, and venue liquidity gaps"
            sandbox_benefit = "simulate regime shift execution against historical tick volatility and validate live feed fidelity"
            value_prop = "full forward-incubation of rebalance protocols without maintaining in-house simulation harnesses"
        elif "volatility" in strat_lower or "option" in strat_lower or "dispersion" in strat_lower:
            market_focus = "non-linear volatility surfaces and options dispersion"
            specific_friction = "execution slippage in complex option legs and spread degradation during fast market moves"
            sandbox_benefit = "parameterize non-linear rules, stress-test delta-neutral bounds, and paper-test execution on live option feeds"
            value_prop = "forward-simulate volatility dispersion strategies with zero low-level infrastructure overhead"
        elif "stat" in strat_lower or "arbitrage" in strat_lower:
            market_focus = "high-turnover equity pairs and mean-reversion"
            specific_friction = "queue latency, spread widening at market open, and adverse selection in fragmented venues"
            sandbox_benefit = "stress-test execution rules against historical spread widening and paper-simulate fills on live exchange feeds"
            value_prop = "verifiable fill parity and slippage analytics without spending months engineering custom paper engines"
        elif "forex" in strat_lower or "fx" in strat_lower or "currency" in strat_lower:
            market_focus = "systematic currency carry and cross-border FX execution"
            specific_friction = "spread widening during interbank rollover windows and queue priority drops on ECN pipes"
            sandbox_benefit = "simulate historical spread widening and forward-test FX execution on real-time feeds"
            value_prop = "audit fill quality and slippage attribution in real time before live allocation"
        elif "alternative" in strat_lower or "exotic" in strat_lower:
            market_focus = "exotic futures and alternative market contracts"
            specific_friction = "shallow order book depth, wide bid-ask spreads, and backtests overestimating fill availability"
            sandbox_benefit = "benchmark execution logic against authentic historical book depth and simulated illiquid friction"
            value_prop = "validate rule stability in simulated live conditions before routing orders to broker pipes"
        else:
            market_focus = "algorithmic execution and quantitative trading"
            specific_friction = "order queue priority degradation, unexpected slippage, and divergence between backtests and live fills"
            sandbox_benefit = "stress-test mathematical parameters against historical market friction and paper-simulate on live feeds"
            value_prop = "verify true execution parity before committing capital to live broker pipes"

        # Sender resolution
        clean_sender = sender_name or getattr(settings, "SENDER_NAME", "Onkar (Founder, Quanteinstein)")
        if not clean_sender or clean_sender == "Technical Founder":
            clean_sender = "Onkar (Founder, Quanteinstein)"

        # =====================================================================
        # 4 DISTINCT ORGANIC COPYWRITING FRAMEWORKS (No Robotic Bullets!)
        # =====================================================================
        if framework_idx == 0:
            # Framework 1: "Studied Website & Execution Friction"
            body = (
                f"{salutation}\n\n"
                f"Came across {lead.firm_name} while studying systematic desks in {lead.region}, and reviewed your focus on {strategies_str}.\n\n"
                f"Noticed from your portal that your models trade {market_focus}. A common friction in this space is execution divergence—clean backtests often degrade in live trading due to {specific_friction}.\n\n"
                f"We built Quanteinstein (https://quanteinstein.com) as a risk-guarded strategy incubation sandbox to address this. It allows your quants to {sandbox_benefit} before routing capital to live broker pipes.\n\n"
                f"Curious how your team currently benchmarks execution parity before going live. Would you be open to a 10-minute technical exchange this week?\n\n"
                f"Best regards,\n"
                f"{clean_sender}\n"
                f"https://quanteinstein.com"
            )
        elif framework_idx == 1:
            # Framework 2: "Portal Overview & Forward Incubation"
            body = (
                f"{salutation}\n\n"
                f"Studied {lead.firm_name}'s portal and recent updates regarding your {strategies_str} models in {lead.region}.\n\n"
                f"When formulating new quantitative rules in {market_focus}, the primary bottleneck for emerging desks is validating how models handle volatile liquidity and queue priority before risking balance-sheet capital.\n\n"
                f"We created Quanteinstein (https://quanteinstein.com) to solve this out of the box. Our platform provides a dedicated strategy incubation sandbox where quants can parameterize execution logic, simulate historical order book friction, and forward-incubate strategies on real-time market data.\n\n"
                f"Would your desk be open to a quick technical demo or testing access to the sandbox?\n\n"
                f"Best,\n"
                f"{clean_sender}\n"
                f"https://quanteinstein.com"
            )
        elif framework_idx == 2:
            # Framework 3: "Mandate Review & Slippage Bottleneck"
            body = (
                f"{salutation}\n\n"
                f"Followed {lead.firm_name}'s work in {lead.region} and reviewed your site's focus on {strategies_str}.\n\n"
                f"Given your desk's mandate in {market_focus}, backtests can be notoriously optimistic about fill availability, especially when {specific_friction} cause substantial execution drag once deployed to live pipes.\n\n"
                f"We developed Quanteinstein (https://quanteinstein.com)—a risk-guarded sandbox where systematic teams stress-test parameters against historical market friction and benchmark real-time paper execution before live broker allocation.\n\n"
                f"Curious how your team currently stress-tests execution divergence before connecting live broker pipes. Open to a brief 5-minute technical chat?\n\n"
                f"Best regards,\n"
                f"{clean_sender}\n"
                f"https://quanteinstein.com"
            )
        else:
            # Framework 4: "Desk Research & Fill Parity Verification"
            body = (
                f"{salutation}\n\n"
                f"Found {lead.firm_name} while researching quantitative trading teams in {lead.region}, and noticed your desk's emphasis on {strategies_str}.\n\n"
                f"Most quant desks burn considerable engineering bandwidth building in-house paper-trading harnesses just to ensure theoretical models match real-world broker fills in {market_focus}.\n\n"
                f"At Quanteinstein (https://quanteinstein.com), we built an institutional strategy incubation sandbox designed to eliminate that friction. Quants can formulate mathematical parameters, stress-test rules against historical tick depth, and forward-test live feed fills in real time.\n\n"
                f"Would your team be open to a brief technical exchange or taking a test drive of the incubation sandbox?\n\n"
                f"Best regards,\n"
                f"{clean_sender}\n"
                f"https://quanteinstein.com"
            )

        word_count = len(body.split())
        value_props = [
            "Friction-Aware Historical Backtesting",
            "Forward-Testing with Simulated Live Fills",
            "Execution Parity Verification Before Live Pipes"
        ]

        website_findings = lead.website_findings or f"Studied {lead.firm_name} portal: specializes in {strategies_str}."

        return GeneratedEmail(
            lead_id=lead.id,
            recipient_email=lead.email,
            recipient_name=lead.contact_name or "Trading Desk",
            firm_name=lead.firm_name,
            website=lead.website,
            region=lead.region,
            subject=subject,
            body=body,
            website_findings=website_findings,
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
                website_findings=lead.website_findings or "Studied firm's website and trading mandate.",
                primary_strategy=self.get_strategy_slug(lead)
            )

            result, provider = await self.llm_client.generate_analysis(prompt)
            if result and isinstance(result, dict) and "subject" in result and "body" in result:
                subject = str(result["subject"]).strip()
                body = str(result["body"]).strip()
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
                    website_findings=lead.website_findings,
                    value_props_used=value_props,
                    word_count=len(body.split())
                )

        return self.draft_heuristic_email(lead, sender_name=clean_sender)
