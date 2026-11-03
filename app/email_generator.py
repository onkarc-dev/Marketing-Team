"""
Hyper-Personalized, Founder-Led Cold Email Generator for Quanteinstein B2B Outreach.
Strictly adheres to founder-led cold email principles:
- Read in 60 seconds or less
- Exactly 3 sentences in the main body (what you do, why it is exciting, what you want)
- Casual, short subject line resembling a message from a friend
- Explicit ask on its own separate line (never asking for a meeting directly)
- Zero jargon, zero flattery, direct peer-to-peer tone
- Generates 2-3 follow-up variations spaced a few days apart with polite, non-confrontational breakup tone
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import DiscoveredLead, GeneratedEmail, FollowUpEmail
from app.llm_client import LLMClient

logger = logging.getLogger(__name__)

EMAIL_PROMPT_TEMPLATE = """System Prompt: Cold Email Generation Agent (Engineer-to-Engineer Systems Architect)
You are an expert technical cold email writing assistant for Quanteinstein Technologies. Your objective is to draft highly effective, engineer-to-engineer cold outreach to Heads of Quantitative Trading, Founders, and Lead Portfolio Managers.

You must strictly adhere to the following guidelines for every email you generate:

Tone & Approach
- Write engineer-to-engineer like a Systems Architect talking peer-to-peer to a quant fund founder.
- Skip all marketing hype, compliments, and filler words; get straight to technical reality and execution telemetry.
- Open directly by acknowledging what they trade: "Saw {firm_name}'s focus on {strategies}."

Content & Telemetry (From Quanteinstein Enterprise OS v3.0 Architecture Brief):
- Frame their core cold-start pain point: Most desks under $50M AUM spend 6+ months and $200k+ building lock-free shared memory, FIX session recovery, and zero-allocation socket parsers from scratch instead of focusing on alpha models.
- Present the solution with exact verified hardware telemetry:
  • Wire-to-Ring Ingress: 1.5 µs median on live exchange tick feeds
  • Zero Heap Allocation: 0 bytes dynamic memory on hot path
  • Core Throughput: 2.7M orders/sec across hardware-isolated SPSC rings
  • Turnkey Compliance: Built-in SEC 15c3-5 pre-trade checks + WAL crash recovery
- Commercial Terms: "We provide a Commercial Source License ($12.5k/year for early design partners) with private VPC deployment in 48 hours."
- Deliverability: DO NOT attach heavy video files (>10MB). Attach only the lightweight 228 KB Architecture Brief PDF.

The Ask
- Action-oriented terminal walkthrough ask: "Open to a quick 10-minute terminal walkthrough this week to see our live feed benchmarks?"
- Place the ask on its own separate line right before the sign-off.
- Signature:
  Best,
  Onkar Chougule
  Systems Architect | Quanteinstein Technologies
  quanteinstein.com

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

### OUTPUT FORMAT
Output valid JSON only:
{{
  "subject": "C++20 execution engine / 1.5µs live wire-to-ring / zero-alloc",
  "body": "[Full Engineer-to-Engineer email body including bullet points and signature]",
  "the_ask": "Open to a quick 10-minute terminal walkthrough this week to see our live feed benchmarks?",
  "follow_ups": [
    {{
      "step": "Follow-Up 1 (Day +3)",
      "delay_days": 3,
      "subject": "quick follow up / {firm_name}",
      "body": "[Short bump with verified 363ns core latency metric, 1-min video offer on request, and terminal ask]"
    }},
    {{
      "step": "Follow-Up 2 (Day +7)",
      "delay_days": 7,
      "subject": "C++20 benchmarks for {firm_name}",
      "body": "[Short technical follow-up on 2.71M/sec throughput + SEC 15c3-5 compliance]"
    }},
    {{
      "step": "Follow-Up 3 (Day +14 Breakup)",
      "delay_days": 14,
      "subject": "closing the loop / {firm_name}",
      "body": "[Polite breakup, acknowledging it is fine to pass, checking back in a few months]"
    }}
  ],
  "value_props_used": ["Deterministic C++20 Core Substrate", "1.50 μs Wire-to-Ring Latency", "SEC Rule 15c3-5 Pre-Trade Risk Filters"]
}}
"""


class EmailOutreachGenerator:
    """Generates tailored 3-sentence cold emails bridging prospect work to Quanteinstein."""

    def __init__(self):
        self.llm_client = LLMClient()

    @staticmethod
    def format_salutation(lead: DiscoveredLead) -> str:
        """
        Formats a natural, friendly salutation like talking to a friend.
        """
        contact = (lead.contact_name or "").strip()
        team_keywords = [
            "team", "desk", "group", "capital", "partners", "trading",
            "research", "analytics", "execution", "firm", "associates", "lab", "labs"
        ]

        if not contact or any(k in contact.lower() for k in team_keywords):
            firm_short = lead.firm_name.split("/")[0].strip()
            firm_clean = re.sub(r'\s+(trading\s+desk|desk|team|group|capital|partners)$', '', firm_short, flags=re.IGNORECASE)
            return f"Hi {firm_clean} team,"

        first_name = contact.split()[0]
        return f"Hi {first_name},"

    @staticmethod
    def get_firm_shortname(lead: DiscoveredLead) -> str:
        """Extracts a short, casual firm name for subject lines (e.g. 'Aetherium', 'Mayfair')."""
        raw = lead.firm_name.split("/")[0].strip()
        cleaned = re.sub(r'\s+(capital|partners|quant|quantitative|trading|asset management|labs|group)$', '', raw, flags=re.IGNORECASE).strip()
        return cleaned or raw

    @staticmethod
    def get_strategy_slug(lead: DiscoveredLead) -> str:
        """Extracts a short, natural strategy descriptor for subject lines."""
        primary_strat = lead.strategies_detected[0] if lead.strategies_detected else "quantitative trading"
        strat_lower = primary_strat.lower()

        if "futures" in strat_lower:
            return "futures execution"
        elif "crypto" in strat_lower or "digital" in strat_lower:
            return "crypto arbitrage"
        elif "forex" in strat_lower or "fx" in strat_lower:
            return "FX trading"
        elif "trend" in strat_lower or "macro" in strat_lower:
            return "systematic macro"
        elif "volatility" in strat_lower or "dispersion" in strat_lower or "option" in strat_lower:
            return "volatility dispersion"
        elif "stat" in strat_lower or "arbitrage" in strat_lower:
            return "stat arb"
        elif "market make" in strat_lower or "hft" in strat_lower:
            return "market making"
        else:
            return "algorithmic execution"

    def format_subject_line(self, lead: DiscoveredLead, variation_idx: int = 0) -> str:
        """
        Constructs a concise, engineer-to-engineer subject line targeting quant technical founders and CTOs.
        """
        short_name = self.get_firm_shortname(lead)
        templates = [
            "C++20 execution engine / 1.5µs live wire-to-ring / zero-alloc",
            f"{short_name} / C++20 execution engine (1.5µs wire-to-ring)",
            f"{short_name} / zero-alloc C++20 substrate",
            f"C++20 execution engine for {short_name}",
            f"quick question re: {short_name} execution",
            f"{short_name} / 1.5µs live wire-to-ring"
        ]
        return templates[variation_idx % len(templates)]

    def draft_heuristic_email(self, lead: DiscoveredLead, sender_name: Optional[str] = None) -> GeneratedEmail:
        """
        Generates an Engineer-to-Engineer cold email strictly adhering to the Systems Architect persona:
        1. Direct acknowledgment: Saw {firm}'s focus on {strategy}.
        2. Core cold-start pain point: Desks under $50M AUM spending 6+ months & $200k+ building lock-free SHM & FIX from scratch.
        3. Verified hardware telemetry bullets (1.5 µs median ingress, 0 bytes heap, 2.7M/sec SPSC throughput, SEC 15c3-5).
        4. Commercial Source License ($12.5k/year early partner CSLA, 48h private VPC).
        5. Action-oriented terminal walkthrough ask on its own line.
        6. Systems Architect signature + 228 KB Architecture Brief PDF auto-attached (NO heavy video attachments).
        """
        hash_seed = int(hashlib.md5(f"{lead.firm_name}_{lead.email}".encode()).hexdigest(), 16)
        subject_idx = (hash_seed >> 2) % 6

        salutation = self.format_salutation(lead)
        subject = self.format_subject_line(lead, variation_idx=subject_idx)
        short_name = self.get_firm_shortname(lead)
        primary_strat = lead.strategies_detected[0].lower() if lead.strategies_detected else "quantitative strategies"

        # Systems Architect persona & signature
        sender_full = sender_name or getattr(settings, "SENDER_NAME", "Onkar Chougule")
        if not sender_full or "Founder" in sender_full or sender_full == "Technical Founder":
            sender_full = "Onkar Chougule"
        sender_title = "Systems Architect | Quanteinstein Technologies"

        # Determine target segment
        is_sweet_spot = True
        if lead.firm_segment and ("emerging" in lead.firm_segment.lower() or "stepping" in lead.firm_segment.lower() or "50m" in lead.firm_segment.lower()):
            is_sweet_spot = False

        # Paragraph 1: Direct acknowledgment of trading focus
        p1 = f"Saw {lead.firm_name}'s focus on {primary_strat}."

        # Paragraph 2: Core cold-start pain point
        if is_sweet_spot:
            p2 = "Most desks under $50M AUM spend 6+ months and $200k+ building lock-free shared memory, FIX session recovery, and zero-allocation socket parsers from scratch instead of focusing on alpha models."
        else:
            p2 = "Most emerging funds scaling past $50M AUM spend 6+ months and $200k+ rebuilding Python execution scripts into C++ FIX engines and custom SEC Rule 15c3-5 risk filters for prime broker audits."

        # Paragraph 3: Telemetry block from Architecture Brief
        p3_header = "We built Quanteinstein to solve that infrastructure cold start:"
        bullets = (
            "• Wire-to-Ring Ingress: 1.5 µs median on live exchange tick feeds\n"
            "• Zero Heap Allocation: 0 bytes dynamic memory on hot path\n"
            "• Core Throughput: 2.7M orders/sec across hardware-isolated SPSC rings\n"
            "• Turnkey Compliance: Built-in SEC 15c3-5 pre-trade checks + WAL crash recovery"
        )

        # Paragraph 4: CSLA Commercial Source License terms from PDF
        p4 = "We provide a Commercial Source License ($12.5k/year for early design partners) with private VPC deployment in 48 hours."

        # Explicit action-oriented terminal ask on its own line
        the_ask = "Open to a quick 10-minute terminal walkthrough this week to see our live feed benchmarks?"

        # Assemble email body
        body = (
            f"{salutation}\n\n"
            f"{p1}\n\n"
            f"{p2}\n\n"
            f"{p3_header}\n"
            f"{bullets}\n\n"
            f"{p4}\n\n"
            f"{the_ask}\n\n"
            f"Best,\n"
            f"{sender_full}\n"
            f"{sender_title}\n"
            f"quanteinstein.com"
        )

        # 3 Spaced Follow-Up Variations
        follow_up_1 = FollowUpEmail(
            step="Follow-Up 1 (Day +3)",
            delay_days=3,
            subject=f"quick follow up / {short_name}",
            body=(
                f"{salutation}\n\n"
                f"Quick bump on this in case it slipped down your inbox. In our verified telemetry from the attached 1-page architecture brief, our C++20 ingestion core clocked 363 ns p50 core latency and 1.5 µs live wire-to-ring with 0 bytes steady-state memory allocation.\n\n"
                f"We also have a 1-minute live terminal benchmark recording available if you'd prefer to see it before a call.\n\n"
                f"Open to a quick 10-minute terminal walkthrough this week?\n\n"
                f"Best,\n"
                f"{sender_full}\n"
                f"{sender_title}\n"
                f"quanteinstein.com"
            )
        )

        follow_up_2 = FollowUpEmail(
            step="Follow-Up 2 (Day +7)",
            delay_days=7,
            subject=f"C++20 benchmarks for {short_name}",
            body=(
                f"{salutation}\n\n"
                f"Wanted to share one quick data point from the brief — our C++20 engine sustains 2.7M orders/sec across SPSC rings while enforcing turnkey SEC Rule 15c3-5 pre-trade risk filters in real time without custom compliance code.\n\n"
                f"Happy to spin up a private sandbox instance or run a 10-minute terminal demo to compare notes against your current fill latency.\n\n"
                f"Worth connecting this week?\n\n"
                f"Best,\n"
                f"{sender_full}\n"
                f"{sender_title}\n"
                f"quanteinstein.com"
            )
        )

        follow_up_3 = FollowUpEmail(
            step="Follow-Up 3 (Day +14 Breakup)",
            delay_days=14,
            subject=f"closing the loop for now / {short_name}",
            body=(
                f"{salutation}\n\n"
                f"Totally understand you are heads down trading and this might not be a fit right now. No worries at all if you pass on this — I will check back in a few months to see how your execution infrastructure is holding up.\n\n"
                f"Wishing you and the team at {lead.firm_name} great trading this quarter.\n\n"
                f"Best,\n"
                f"{sender_full}\n"
                f"{sender_title}\n"
                f"quanteinstein.com"
            )
        )

        word_count = len(body.split())
        website_findings = lead.website_findings or f"Studied {lead.firm_name} portal: specializes in {primary_strat}."

        value_props = [
            "Deterministic C++20 Core Substrate",
            "1.50 μs Wire-to-Ring Latency (363 ns p50 Core)",
            "2.7M / sec SPSC Ring Throughput (0 Bytes Dynamic Alloc)",
            "Turnkey SEC Rule 15c3-5 Risk Filters & WAL Recovery"
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
            the_ask=the_ask,
            follow_ups=[follow_up_1, follow_up_2, follow_up_3],
            website_findings=website_findings,
            value_props_used=value_props,
            attachments=[
                "Quanteinstein_Enterprise_OS_v3.0_Architecture_Brief.pdf"
            ],
            word_count=word_count
        )

    async def generate_email(self, lead: DiscoveredLead, sender_name: Optional[str] = None) -> GeneratedEmail:
        """
        Generates tailored email using LLM if available, otherwise falls back to deterministic engine.
        """
        clean_sender = sender_name or getattr(settings, "SENDER_NAME", "Onkar Chougule")
        if not clean_sender or "Founder" in clean_sender or clean_sender == "Technical Founder":
            clean_sender = "Onkar Chougule"
        sender_title = "Systems Architect | Quanteinstein Technologies"

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
                follow_ups_raw = result.get("follow_ups", [])
                follow_ups = []
                for fu in follow_ups_raw:
                    if isinstance(fu, dict) and "subject" in fu and "body" in fu:
                        follow_ups.append(FollowUpEmail(
                            step=fu.get("step", "Follow-Up"),
                            delay_days=int(fu.get("delay_days", 3)),
                            subject=fu.get("subject", ""),
                            body=fu.get("body", "")
                        ))

                full_body = result.get("body", "")
                the_ask = result.get("the_ask", "")
                if the_ask and the_ask not in full_body:
                    full_body = f"{full_body}\n\n{the_ask}\n\nBest,\n{clean_sender}\n{sender_title}\nquanteinstein.com"

                return GeneratedEmail(
                    lead_id=lead.id,
                    recipient_email=lead.email,
                    recipient_name=lead.contact_name or "Trading Desk",
                    firm_name=lead.firm_name,
                    website=lead.website,
                    region=lead.region,
                    subject=result.get("subject", self.format_subject_line(lead)),
                    body=full_body,
                    the_ask=the_ask,
                    follow_ups=follow_ups or self.draft_heuristic_email(lead, sender_name).follow_ups,
                    website_findings=lead.website_findings,
                    value_props_used=result.get("value_props_used", ["Deterministic C++20 Core Substrate", "1.50 μs Wire-to-Ring Latency", "SEC Rule 15c3-5 Pre-Trade Risk Filters"]),
                    attachments=[
                        "Quanteinstein_Enterprise_OS_v3.0_Architecture_Brief.pdf"
                    ],
                    word_count=len(full_body.split())
                )

        return self.draft_heuristic_email(lead, sender_name=clean_sender)
