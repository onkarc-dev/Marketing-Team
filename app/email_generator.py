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

EMAIL_PROMPT_TEMPLATE = """You are Onkar, technical founder of Quanteinstein (https://quanteinstein.com), writing a highly tailored 1-on-1 cold email to a Mid-Market Quantitative Firm.

### TARGET PROSPECT INTELLIGENCE
Firm Name: {firm_name}
Website: {website}
Region / Location: {region}
Contact Person: {contact_name} ({contact_title})
Summary of Their Work: {summary}
Detected Strategies / Focus: {strategies}
Studied Website Findings: {website_findings}
Firm Segment: {firm_segment} ({headcount}, {aum})
Target Buyer: {target_decision_maker}
Core Pain Point: {core_pain_point}

### COMMERCIAL POSITIONING: MID-MARKET (NOT ENTERPRISE GIANTS)
We do NOT target Citadel, Jane Street, or HRT (they build everything internally). We target the Mid-Market:
1. The Sweet Spot: Proprietary Trading Firms & Small Family Offices (2-15 people, $10M-$50M AUM).
   - Buyer: Founder or Lead Portfolio Manager (no CISO bureaucracy).
   - Value Prop: They have brilliant quant researchers but lack dedicated C++ infrastructure engineers. An in-house team costs $500,000/yr to build and maintain low-latency FIX execution and single-tenant sandboxes. Quanteinstein ($80k/yr) delivers turnkey C++ FIX execution and single-tenant incubation out of the box -- saving $420k/yr.
2. The Stepping Stone: Emerging Quantitative Funds (15-40 people, $50M-$250M AUM).
   - Buyer: Head of Quantitative Trading or CTO.
   - Value Prop: Scaling past patched-together Python infrastructure; hitting latency limits and needing turnkey SEC Rule 15c3-5 pre-trade risk controls to pass prime broker and regulatory audits.

### STRICT COPYWRITING RULES
1. Salutation:
   - If contact is an individual (e.g. Marcus Kane, Jonathan Ross, Doug Greenig), use "Hi Firstname,".
   - If contact is a desk/team (e.g. Systematic Research Team), use "Hi {firm_name} Trading Desk," or "Hi {firm_name} Team,". Never say "Hi Systematic,".
2. Subject Line:
   - 4-8 words. Natural, direct, commercial.
   - Examples for Sweet Spot:
     * "C++ FIX execution for {firm_name} (without the $500k infra overhead)"
     * "low-latency FIX execution at {firm_name}"
     * "single-tenant C++ FIX engine for {firm_name}"
     * "question on {firm_name}'s C++ execution pipes"
   - Examples for Stepping Stone:
     * "{firm_name} • SEC Rule 15c3-5 risk controls & FIX latency"
     * "scaling {firm_name}'s execution: C++ FIX & SEC 15c3-5 compliance"
     * "low-latency C++ FIX engine for {firm_name}"
3. Tone & Structure:
   - Natural email from Onkar (Founder, Quanteinstein) who visited their site and studied their work.
   - Paragraph 1: Mention finding them and studying their site regarding their specific strategies and market focus.
   - Paragraph 2: Point out their exact commercial pain point (saving $500k/yr on C++ infra or outgrowing Python and needing SEC 15c3-5 risk controls).
   - Paragraph 3: Introduce Quanteinstein (https://quanteinstein.com) as the turnkey C++ FIX execution engine and single-tenant incubation sandbox that solves this for $80k/yr.
   - Paragraph 4: Low-friction CTA (e.g. "Curious how your team currently handles low-latency FIX execution without maintaining a costly internal infra team. Open to a 10-minute technical exchange this week?").
   - Sign-off: "Best regards,\nOnkar (Founder, Quanteinstein)\nhttps://quanteinstein.com"
4. ZERO BULLET POINTS: Write natural conversational prose paragraphs only.
5. KEEP WORD COUNT CRISP: Exactly 95-135 words.

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
        Constructs a sharp, smart, personalized, professional subject line
        tailored to Mid-Market buyers (Prop Desks & Family Offices or Emerging Quant Funds).
        Rotates among 6 organic styles per segment.
        """
        strat_short = self.get_strategy_slug(lead)
        firm = lead.firm_name
        is_sweet_spot = "proprietary" in (lead.firm_segment or "").lower() or "family" in (lead.firm_segment or "").lower()

        if is_sweet_spot:
            # Prop Desks & Family Offices ($10M-$50M AUM): Focus on C++ FIX & saving $500k infra overhead
            templates = [
                f"C++ FIX execution for {firm} (without the $500k infra overhead)",
                f"low-latency FIX execution at {firm}",
                f"single-tenant C++ FIX engine for {firm}",
                f"question on {firm}'s C++ execution pipes",
                f"{firm} • low-latency FIX & single-tenant sandbox",
                f"fill parity & FIX latency in {strat_short} at {firm}"
            ]
        else:
            # Emerging Quant Funds ($50M-$250M AUM): Focus on SEC Rule 15c3-5 risk controls & outgrowing Python
            templates = [
                f"{firm} • SEC Rule 15c3-5 risk controls & FIX latency",
                f"scaling {firm}'s execution: C++ FIX & SEC 15c3-5 compliance",
                f"low-latency C++ FIX engine for {firm}",
                f"passing 15c3-5 risk audits at {firm} without custom infra",
                f"question on {firm}'s broker audits & FIX execution",
                f"{firm} / Quanteinstein: single-tenant C++ FIX infrastructure"
            ]

        return templates[variation_idx % len(templates)]

    def draft_heuristic_email(self, lead: DiscoveredLead, sender_name: Optional[str] = None) -> GeneratedEmail:
        """
        Generates a deterministic, highly tailored, human-sounding cold email.
        Tailored 100% to Mid-Market buyers:
        - Sweet Spot (Prop Desks & Family Offices): $80k Quanteinstein vs $500k/yr in-house C++ infra team.
        - Stepping Stone (Emerging Quant Funds): Outgrowing Python, need C++ FIX + SEC Rule 15c3-5 pre-trade risk controls.
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
        elif "crypto" in strat_lower or "digital" in strat_lower:
            market_focus = "24/7 digital asset order books and cross-venue arbitrage"
            specific_friction = "leg execution latency, rate-limit delays, and cross-exchange slippage erasing edge"
        elif "trend" in strat_lower or "macro" in strat_lower:
            market_focus = "multi-asset futures and global trend momentum"
            specific_friction = "slippage during sharp regime shifts, contract rollover drag, and venue liquidity gaps"
        elif "volatility" in strat_lower or "option" in strat_lower or "dispersion" in strat_lower:
            market_focus = "non-linear volatility surfaces and options dispersion"
            specific_friction = "execution slippage in complex option legs and spread degradation during fast market moves"
        elif "stat" in strat_lower or "arbitrage" in strat_lower:
            market_focus = "high-turnover equity pairs and mean-reversion"
            specific_friction = "queue latency, spread widening at market open, and adverse selection in fragmented venues"
        elif "forex" in strat_lower or "fx" in strat_lower or "currency" in strat_lower:
            market_focus = "systematic currency carry and cross-border FX execution"
            specific_friction = "spread widening during interbank rollover windows and queue priority drops on ECN pipes"
        elif "alternative" in strat_lower or "exotic" in strat_lower:
            market_focus = "exotic futures and alternative market contracts"
            specific_friction = "shallow order book depth, wide bid-ask spreads, and backtests overestimating fill availability"
        else:
            market_focus = "algorithmic execution and quantitative trading"
            specific_friction = "order queue priority degradation, unexpected slippage, and divergence between backtests and live fills"

        # Sender resolution
        clean_sender = sender_name or getattr(settings, "SENDER_NAME", "Onkar (Founder, Quanteinstein)")
        if not clean_sender or clean_sender == "Technical Founder":
            clean_sender = "Onkar (Founder, Quanteinstein)"

        is_sweet_spot = "proprietary" in (lead.firm_segment or "").lower() or "family" in (lead.firm_segment or "").lower()

        # =====================================================================
        # MID-MARKET COPYWRITING FRAMEWORKS
        # =====================================================================
        if is_sweet_spot:
            # -----------------------------------------------------------------
            # PERSONA 1: Boutique Prop Desks & Family Offices ($10M-$50M AUM)
            # Value Prop: Saves $500k/yr on C++ infra team; $80k turnkey FIX engine
            # -----------------------------------------------------------------
            value_props = [
                "Turnkey C++ FIX Execution Engine ($80k vs $500k in-house team)",
                "Single-Tenant Strategy Incubation Sandbox",
                "Sub-Millisecond Fill Parity & Slippage Modeling"
            ]

            if framework_idx == 0:
                body = (
                    f"{salutation}\n\n"
                    f"Came across {lead.firm_name} while researching boutique prop trading desks in {lead.region}, and noted your desk's focus on {strategies_str}.\n\n"
                    f"Most lean quantitative teams have exceptional alpha researchers, but lack dedicated in-house C++ infrastructure engineers. Paying $500,000/year to hire and maintain low-latency FIX execution and single-tenant sandbox environments burns too much balance-sheet capital.\n\n"
                    f"We built Quanteinstein (https://quanteinstein.com) to solve this directly. We provide an institutional-grade, low-latency C++ FIX execution engine and single-tenant strategy incubation sandbox out of the box for $80,000/year -- delivering sub-millisecond execution and forward simulation while saving $420,000/year in engineering overhead.\n\n"
                    f"Curious how your team currently handles low-latency FIX execution without maintaining a costly internal infra team. Would you be open to a brief 10-minute technical exchange this week?\n\n"
                    f"Best regards,\n"
                    f"{clean_sender}\n"
                    f"https://quanteinstein.com"
                )
            elif framework_idx == 1:
                body = (
                    f"{salutation}\n\n"
                    f"Studied {lead.firm_name}'s focus on {strategies_str} in {lead.region}.\n\n"
                    f"When running a focused proprietary book in {market_focus}, formulating high-conviction mathematical models is only half the battle. The core bottleneck is maintaining low-latency FIX execution and realistic paper-to-live incubation without burning $500,000/year on dedicated infrastructure engineers.\n\n"
                    f"At Quanteinstein (https://quanteinstein.com), we built an institutional C++ FIX execution and incubation sandbox designed specifically for prop desks. For $80,000/year, you get single-tenant data isolation, sub-millisecond broker routing, and authentic exchange friction modeling -- saving $420,000/year in engineering overhead.\n\n"
                    f"Would you be open to a brief 5-minute technical chat to test-drive access to the sandbox?\n\n"
                    f"Best,\n"
                    f"{clean_sender}\n"
                    f"https://quanteinstein.com"
                )
            elif framework_idx == 2:
                body = (
                    f"{salutation}\n\n"
                    f"Followed {lead.firm_name}'s work in {lead.region} and reviewed your site's focus on {strategies_str}.\n\n"
                    f"In {market_focus}, backtests often show strong theoretical edge, but live execution suffers when routing through patched-together connectors, queue delays, and {specific_friction}.\n\n"
                    f"Rather than burning $500,000/year attempting to build a custom C++ execution harness internally, Quanteinstein (https://quanteinstein.com) delivers turnkey C++ FIX connectivity and a single-tenant forward incubation sandbox for $80,000/year -- giving your desk enterprise infrastructure with full single-tenant isolation for a fraction of an engineer's salary.\n\n"
                    f"Curious how your desk currently stress-tests execution divergence before routing live orders. Open to a brief 10-minute conversation this week?\n\n"
                    f"Best regards,\n"
                    f"{clean_sender}\n"
                    f"https://quanteinstein.com"
                )
            else:
                body = (
                    f"{salutation}\n\n"
                    f"Found {lead.firm_name} while tracking boutique quantitative trading desks in {lead.region}, and noticed your focus on {strategies_str}.\n\n"
                    f"Boutique prop desks frequently face a dilemma: either burn $500,000/year hiring dedicated C++ engineers to build low-latency execution harnesses, or accept execution drag from off-the-shelf Python connectors.\n\n"
                    f"We created Quanteinstein (https://quanteinstein.com) to eliminate that tradeoff. For $80,000/year, it gives your desk a high-performance C++ FIX engine, single-tenant isolation, and realistic order queue friction modeling -- saving over $400,000/year while enabling your quants to forward-simulate strategies with zero engineering drag.\n\n"
                    f"Would you be open to a 10-minute technical demo to see how we benchmark execution parity?\n\n"
                    f"Best regards,\n"
                    f"{clean_sender}\n"
                    f"https://quanteinstein.com"
                )
        else:
            # -----------------------------------------------------------------
            # PERSONA 2: Emerging Quant Funds ($50M-$250M AUM)
            # Value Prop: Outgrowing Python; C++ FIX + SEC Rule 15c3-5 risk controls
            # -----------------------------------------------------------------
            value_props = [
                "Low-Latency C++ FIX Execution Engine",
                "SEC Rule 15c3-5 Pre-Trade Risk Controls",
                "Single-Tenant Prime Broker Audit Compliance"
            ]

            if framework_idx == 0:
                body = (
                    f"{salutation}\n\n"
                    f"Came across {lead.firm_name} while researching emerging systematic funds in {lead.region}, and noted your fund's focus on {strategies_str}.\n\n"
                    f"As quantitative funds scale past $50M AUM, patched-together Python backtesters and execution harnesses hit hard limits on order book latency, and passing prime broker audits demands institutional pre-trade risk controls under SEC Rule 15c3-5.\n\n"
                    f"We built Quanteinstein (https://quanteinstein.com) to solve this transition. Our low-latency C++ FIX execution engine and single-tenant sandbox come pre-equipped with turnkey SEC Rule 15c3-5 pre-trade risk controls and real-time execution telemetry to clear regulatory and broker audits effortlessly.\n\n"
                    f"Curious how your team is currently scaling its FIX execution and compliance infrastructure. Would you be open to a 10-minute technical exchange this week?\n\n"
                    f"Best regards,\n"
                    f"{clean_sender}\n"
                    f"https://quanteinstein.com"
                )
            elif framework_idx == 1:
                body = (
                    f"{salutation}\n\n"
                    f"Studied {lead.firm_name}'s portal and recent updates regarding your {strategies_str} strategies in {lead.region}.\n\n"
                    f"When scaling systematic strategies in {market_focus}, the primary bottleneck for emerging funds is demonstrating deterministic pre-trade risk limits and SEC Rule 15c3-5 compliance to prime brokers without rewriting research code in C++ from scratch.\n\n"
                    f"At Quanteinstein (https://quanteinstein.com), we built an institutional C++ FIX execution and incubation sandbox with built-in SEC Rule 15c3-5 risk controls, single-tenant isolation, and tick-level execution parity analytics.\n\n"
                    f"Would your trading or technology team be open to a brief technical demo of the FIX engine?\n\n"
                    f"Best,\n"
                    f"{clean_sender}\n"
                    f"https://quanteinstein.com"
                )
            elif framework_idx == 2:
                body = (
                    f"{salutation}\n\n"
                    f"Followed {lead.firm_name}'s work in {lead.region} and reviewed your site's focus on {strategies_str}.\n\n"
                    f"Given your fund's scale in {market_focus}, prime brokers increasingly demand verifiable pre-trade capital thresholds, order size checks, and price collars compliant with SEC Rule 15c3-5 before granting direct market access.\n\n"
                    f"Quanteinstein (https://quanteinstein.com) provides an institutional C++ FIX execution engine with turnkey SEC Rule 15c3-5 risk controls, sub-millisecond execution, and a single-tenant paper incubation sandbox that proves execution parity before routing real capital.\n\n"
                    f"Curious how your desk currently handles pre-trade risk verification for broker audits. Open to a brief 5-minute technical chat?\n\n"
                    f"Best regards,\n"
                    f"{clean_sender}\n"
                    f"https://quanteinstein.com"
                )
            else:
                body = (
                    f"{salutation}\n\n"
                    f"Found {lead.firm_name} while researching systematic funds in {lead.region}, and noticed your team's work in {strategies_str}.\n\n"
                    f"Most emerging systematic managers burn significant engineering bandwidth rebuilding custom C++ FIX infrastructure and compliance monitoring that could otherwise be deployed on core alpha generation.\n\n"
                    f"At Quanteinstein (https://quanteinstein.com), we provide a dedicated single-tenant C++ FIX engine and strategy incubation sandbox equipped with turnkey SEC Rule 15c3-5 pre-trade risk controls, allowing your team to modernize execution without infrastructure overhead.\n\n"
                    f"Would your technology team be open to a brief technical exchange or taking a test drive of the sandbox?\n\n"
                    f"Best regards,\n"
                    f"{clean_sender}\n"
                    f"https://quanteinstein.com"
                )

        word_count = len(body.split())
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
                firm_segment=lead.firm_segment,
                headcount=lead.headcount,
                aum=lead.aum,
                target_decision_maker=lead.target_decision_maker,
                core_pain_point=lead.core_pain_point or "Lacks in-house C++ infra engineers"
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
