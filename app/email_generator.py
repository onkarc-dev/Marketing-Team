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

EMAIL_PROMPT_TEMPLATE = """System Prompt: Cold Email Generation Agent
You are an expert cold email writing assistant. Your objective is to draft highly effective, founder-led cold emails. You must strictly adhere to the following guidelines for every email you generate:

Format & Structure
- Keep the email short enough to be read in 60 seconds or less.
- Limit the body to exactly three sentences covering: what you do, why it is exciting, and what you want.
- Give every email a single goal and cut any words that do not serve that specific goal.
- Place the explicit ask on its own separate line right before you sign off.

Tone & Voice
- Write like you are talking to a friend; the text should sound natural when read out loud.
- Keep the subject line casual, short, and relevant, resembling a message from a friend.
- Skip all compliments and flattery; get directly to the point.
- Explain what you do right away using plain words and absolutely zero jargon.

Content & Strategy
- Make the email about the recipient and frame their problem using their own words.
- Focus purely on their specific pain point (e.g. execution slippage, lack of in-house C++ infra devs, Python latency limits, SEC 15c3-5 broker audits) and how we solve it properly.
- NEVER state direct pricing, fees, or dollar figures (do not quote $80,000/year, $500k savings, or software costs) in the initial cold email.
- Find and mention an uncommon commonality to prove there is a real reason you are contacting them.
- Lead with your best proof, such as metrics on execution latency (e.g., 18-microsecond routing, zero fill divergence), turnkey prime broker audit compliance, or technical sandbox capabilities.
- Borrow credibility by naturally incorporating notable affiliations, past employers, or customer names (e.g., YC).
- Skip all backstory, origin stories, and resume details.

The Ask
- Make the ask highly explicit (e.g., asking for advice, feedback, or permission to share benchmark data).
- Never ask for a meeting directly; leave room for the recipient to escalate the interaction.

Operational Directives (For the Agent's Context)
- Ensure the drafted email is intended to be sent from a company email address that includes the sender's name (Onkar, Founder of Quanteinstein).
- Draft content meant for a highly targeted audience, as 100 good-fit emails beat 1,000 random ones.
- Make the output read as though it was hand-written by a founder, avoiding any corporate or automated feel.
- Be prepared to generate 2-4 follow-up variations spaced a few days apart.
- Maintain a polite, non-confrontational tone in all follow-ups, acknowledging that it is okay if they ignore it and that you will check back in a few months.

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
  "subject": "[Casual, short subject line resembling a friend's message]",
  "body": "[Exactly 3 sentences: what you do, why it is exciting, and what you want]",
  "the_ask": "[Explicit ask on its own separate line -- NEVER ask for a meeting]",
  "follow_ups": [
    {{
      "step": "Follow-Up 1 (Day +3)",
      "delay_days": 3,
      "subject": "quick follow up / {firm_name}",
      "body": "[Short bump with quick proof point and isolated ask]"
    }},
    {{
      "step": "Follow-Up 2 (Day +7)",
      "delay_days": 7,
      "subject": "c++ fix benchmarks for {firm_name}",
      "body": "[Short follow-up sharing a single technical proof metric]"
    }},
    {{
      "step": "Follow-Up 3 (Day +14 Breakup)",
      "delay_days": 14,
      "subject": "closing the loop for now",
      "body": "[Polite breakup, acknowledging it is fine to pass, checking back in a few months]"
    }}
  ],
  "value_props_used": ["[Capability 1]", "[Capability 2]"]
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
        Constructs a casual, short, relevant subject line resembling a message from a friend.
        """
        short_name = self.get_firm_shortname(lead)
        is_sweet_spot = "proprietary" in (lead.firm_segment or "").lower() or "family" in (lead.firm_segment or "").lower()

        if is_sweet_spot:
            templates = [
                f"quick question for {short_name}",
                f"{short_name} / fix engine",
                f"c++ execution at {short_name}",
                f"quick question re: {short_name}",
                f"fix latency question",
                f"{short_name} / single-tenant sandbox"
            ]
        else:
            templates = [
                f"quick question for {short_name}",
                f"{short_name} • sec 15c3-5 check",
                f"c++ fix infrastructure",
                f"{short_name} / broker audits",
                f"quick question re: execution",
                f"broker compliance at {short_name}"
            ]

        return templates[variation_idx % len(templates)]

    def draft_heuristic_email(self, lead: DiscoveredLead, sender_name: Optional[str] = None) -> GeneratedEmail:
        """
        Generates a founder-led cold email strictly adhering to the 3-sentence rule:
        Sentence 1: What you do (about recipient's problem, plain words, no jargon)
        Sentence 2: Why it is exciting (best proof: $420k savings, sub-millisecond execution, SEC 15c3-5 audit pass)
        Sentence 3: What you want (single goal)
        The Ask: Placed on its own separate line right before sign-off (NEVER asking for a meeting)
        Includes 3 spaced follow-up variations with polite breakup tone.
        """
        hash_seed = int(hashlib.md5(f"{lead.firm_name}_{lead.email}".encode()).hexdigest(), 16)
        framework_idx = hash_seed % 4
        subject_idx = (hash_seed >> 2) % 6
        ask_idx = (hash_seed >> 4) % 4

        salutation = self.format_salutation(lead)
        subject = self.format_subject_line(lead, variation_idx=subject_idx)
        short_name = self.get_firm_shortname(lead)
        city = lead.region.split(",")[0].strip()
        primary_strat = lead.strategies_detected[0] if lead.strategies_detected else "quantitative strategies"

        # Clean sender signature
        clean_sender = sender_name or getattr(settings, "SENDER_NAME", "Onkar (Founder, Quanteinstein)")
        if not clean_sender or clean_sender == "Technical Founder":
            clean_sender = "Onkar"

        # Determine target segment (Sweet Spot vs Stepping Stone)
        is_sweet_spot = True
        if lead.firm_segment and ("emerging" in lead.firm_segment.lower() or "stepping" in lead.firm_segment.lower() or "50m" in lead.firm_segment.lower()):
            is_sweet_spot = False

        region_str = lead.region or "your area"

        # =====================================================================
        # EXACT THREE-SENTENCE BODY GENERATION
        # =====================================================================
        if is_sweet_spot:
            # SWEET SPOT: Prop Desks & Family Offices ($10M-$50M AUM)
            # Focus: Pain point (execution slippage, lacking dedicated C++ team) + Proper solution (turnkey FIX engine, fill parity sandbox)
            # NO direct price quoting in initial cold outreach
            s1_options = [
                f"We built Quanteinstein (https://quanteinstein.com) so boutique prop trading desks like {lead.firm_name} in {region_str} can run low-latency C++ FIX execution for {primary_strat} without having to build and maintain complex infrastructure in-house.",
                f"We provide a turnkey C++ FIX execution engine and private strategy sandbox for boutique desks like {lead.firm_name} in {region_str} scaling {primary_strat} without the burden of an internal infrastructure engineering team.",
                f"We built Quanteinstein (https://quanteinstein.com) to help lean prop trading teams like {lead.firm_name} in {region_str} eliminate the execution divergence and spread slippage that happens when {primary_strat} models move from backtests to live broker fills.",
                f"At Quanteinstein (https://quanteinstein.com), we help boutique trading desks like {lead.firm_name} in {region_str} deploy {primary_strat} into sub-millisecond C++ FIX pipes without burning research cycles on custom trading infrastructure."
            ]
            # Sentence 2: How we solve it properly (best proof: sub-millisecond execution, queue friction modeling, fill parity)
            s2_options = [
                f"Our single-tenant C++ engine models real exchange queue friction and delivers sub-millisecond fill parity, giving your desk institutional execution speed and private data isolation out of the box.",
                f"Our private incubation sandbox lets quantitative desks stress-test order routing against authentic exchange friction and verify true fill parity before routing capital to live broker pipes.",
                f"Our engine delivers turnkey sub-millisecond order routing with built-in queue friction modeling and single-tenant isolation, eliminating execution drag so your researchers can focus purely on alpha.",
                f"Our single-tenant C++ engine delivers sub-millisecond execution parity and real exchange friction modeling, bridging mathematical models directly into live trading without execution drop-off."
            ]
            # Sentence 3: What you want (single goal)
            s3_options = [
                f"I am reaching out to a handful of quantitative founders in {region_str} to see how you are currently tackling execution latency and fill divergence.",
                f"I am getting in touch with a few prop desk founders in {region_str} to see if our execution benchmarks match what you are seeing in live broker fills.",
                f"I am checking in with a few boutique fund founders in {region_str} to see if execution slippage and infrastructure maintenance are on your radar right now.",
                f"I am reaching out to a few quantitative founders in {region_str} to compare notes on how lean desks are handling execution latency."
            ]

            # The Ask: on its own separate line (NEVER ask for a meeting)
            ask_options = [
                "Would you be open to giving some quick feedback on our benchmark data?",
                "Worth sending over a 2-minute video breakdown of our latency numbers?",
                "Open to checking out a sandbox test login to see the fill numbers?",
                "Would you be open to sharing your thoughts on this?"
            ]

            value_props = [
                "Turnkey C++ FIX Execution Engine",
                "Single-Tenant Strategy Incubation Sandbox",
                "Sub-Millisecond Fill Parity & Slippage Modeling"
            ]
        else:
            # STEPPING STONE: Emerging Quant Funds ($50M-$250M AUM)
            # Focus: Pain point (scaling past Python scripts, prime broker SEC 15c3-5 audits) + Proper solution (institutional C++ FIX + turnkey pre-trade compliance)
            # NO direct price quoting in initial cold outreach
            s1_options = [
                f"We built Quanteinstein (https://quanteinstein.com) so growing systematic funds like {lead.firm_name} in {region_str} can scale {primary_strat} past Python execution scripts into an institutional C++ FIX engine with turnkey SEC Rule 15c3-5 risk controls.",
                f"We provide an institutional-grade C++ FIX execution engine and private sandbox for growing quantitative funds like {lead.firm_name} in {region_str} scaling past $50M in {primary_strat} that need to clear prime broker compliance audits.",
                f"At Quanteinstein (https://quanteinstein.com), we help emerging quantitative funds like {lead.firm_name} in {region_str} upgrade {primary_strat} from patched-together Python execution into sub-millisecond C++ FIX infrastructure.",
                f"We built Quanteinstein (https://quanteinstein.com) to give growing systematic teams like {lead.firm_name} in {region_str} turnkey C++ FIX connectivity with built-in SEC Rule 15c3-5 pre-trade checks for prime broker audits."
            ]
            # Sentence 2: How we solve it properly (best proof: SEC 15c3-5 risk controls, prime broker audits, sub-millisecond)
            s2_options = [
                f"Our single-tenant C++ engine delivers sub-millisecond execution and turnkey SEC Rule 15c3-5 pre-trade risk controls that let growing funds pass prime broker audits effortlessly.",
                f"Funds using our single-tenant C++ engine achieve sub-millisecond order routing and clear SEC Rule 15c3-5 broker audits without writing custom compliance code.",
                f"Our engine eliminates execution latency bottlenecks and gives your fund audit-ready SEC Rule 15c3-5 pre-trade risk controls out of the box to pass prime broker reviews.",
                f"Our single-tenant C++ engine delivers sub-millisecond routing and passes prime broker SEC Rule 15c3-5 risk audits out of the box, saving months of internal dev work."
            ]
            # Sentence 3: What you want (single goal)
            s3_options = [
                f"I am reaching out to a few quantitative leaders in {region_str} to see how you are currently handling pre-trade risk controls and FIX latency as you scale.",
                f"I am getting in touch with a few systematic leaders in {region_str} to see if broker audit compliance and execution latency are top of mind as you grow.",
                f"I am checking in with a handful of quantitative leads in {region_str} to see how you are managing the transition from Python prototypes into institutional C++ execution.",
                f"I am reaching out to a few quantitative fund leaders in {region_str} to see if our execution benchmarks could be helpful for your team."
            ]

            # The Ask: on its own separate line (NEVER ask for a meeting)
            ask_options = [
                "Would you be open to taking a look at our SEC 15c3-5 compliance checklist?",
                "Worth sending over a 2-minute walkthrough of our C++ FIX engine?",
                "Open to checking out our execution benchmark numbers?",
                "Would you be open to sharing some quick feedback on how you handle this?"
            ]

            value_props = [
                "Low-Latency C++ FIX Execution Engine",
                "SEC Rule 15c3-5 Pre-Trade Risk Controls",
                "Single-Tenant Prime Broker Audit Compliance"
            ]

        sentence_1 = s1_options[framework_idx]
        sentence_2 = s2_options[framework_idx]
        sentence_3 = s3_options[framework_idx]
        the_ask = ask_options[ask_idx]

        # Assemble strictly formatted 3-sentence body + isolated ask
        body = (
            f"{salutation}\n\n"
            f"{sentence_1} {sentence_2} {sentence_3}\n\n"
            f"{the_ask}\n\n"
            f"Best,\n"
            f"{clean_sender}\n"
            f"Founder, Quanteinstein\n"
            f"https://quanteinstein.com"
        )

        # =====================================================================
        # 3 SPACED FOLLOW-UP VARIATIONS (Polite, Non-Confrontational Breakup)
        # =====================================================================
        follow_up_1 = FollowUpEmail(
            step="Follow-Up 1 (Day +3)",
            delay_days=3,
            subject=f"quick follow up / {short_name}",
            body=(
                f"{salutation}\n\n"
                f"Quick bump on this in case it slipped down your inbox. We recently clocked 18-microsecond order routing on our single-tenant C++ FIX engine without desks needing an in-house infrastructure team.\n\n"
                f"Worth sending over a 1-page summary of our benchmark data?\n\n"
                f"Best,\n"
                f"{clean_sender}\n"
                f"Founder, Quanteinstein"
            )
        )

        follow_up_2 = FollowUpEmail(
            step="Follow-Up 2 (Day +7)",
            delay_days=7,
            subject=f"c++ fix benchmarks for {short_name}",
            body=(
                f"{salutation}\n\n"
                f"Wanted to share one quick data point -- our single-tenant engine includes turnkey SEC Rule 15c3-5 pre-trade risk controls that let quantitative teams clear prime broker audits with zero custom compliance dev work.\n\n"
                f"Open to checking out our sandbox test login?\n\n"
                f"Best,\n"
                f"{clean_sender}\n"
                f"Founder, Quanteinstein"
            )
        )

        follow_up_3 = FollowUpEmail(
            step="Follow-Up 3 (Day +14 Breakup)",
            delay_days=14,
            subject="closing the loop for now",
            body=(
                f"{salutation}\n\n"
                f"Totally understand you are heads down trading and this might not be relevant right now. No worries at all if you pass on this -- I will check back in a few months to see how your execution infrastructure is holding up.\n\n"
                f"Wishing you and the team at {lead.firm_name} great trading this quarter.\n\n"
                f"Best,\n"
                f"{clean_sender}\n"
                f"Founder, Quanteinstein"
            )
        )

        word_count = len(body.split())
        website_findings = lead.website_findings or f"Studied {lead.firm_name} portal: specializes in {primary_strat}."

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
                    full_body = f"{full_body}\n\n{the_ask}\n\nBest,\n{clean_sender}\nFounder, Quanteinstein\nhttps://quanteinstein.com"

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
                    value_props_used=result.get("value_props_used", ["Turnkey C++ FIX Execution", "Single-Tenant Sandbox"]),
                    word_count=len(full_body.split())
                )

        return self.draft_heuristic_email(lead, sender_name=clean_sender)
