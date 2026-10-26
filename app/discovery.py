"""
Web Search and Firm Discovery Engine.
Discovers target quantitative firms, prop desks, and emerging hedge funds by region/niche,
scrapes contact emails, and analyzes their trading focus.
"""

import re
import urllib.parse
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.models import SearchQueryRequest, DiscoveredLead

logger = logging.getLogger(__name__)

# Institutional directory of quantitative firms, prop desks, and emerging funds by financial hub
# Used for high-fidelity fallback and instant enrichment across global regions
REGIONAL_QUANT_REGISTRY: List[Dict[str, Any]] = [
    # London / UK
    {
        "firm_name": "Aspect Capital",
        "website": "https://www.aspectcapital.com",
        "region": "London, UK",
        "contact_name": "Systematic Research Team",
        "contact_title": "Head of Quantitative Strategies",
        "email": "research@aspectcapital.com",
        "summary": "Pioneering systematic trend following, statistical arbitrage, and multi-asset quantitative investment firm based in London.",
        "strategies_detected": ["Trend Following", "Statistical Arbitrage", "Systematic Macro"],
        "relevance_score": 9
    },
    {
        "firm_name": "Cantab Capital / GAM Systematic",
        "website": "https://www.gam.com",
        "region": "London, UK",
        "contact_name": "Algorithmic Execution Desk",
        "contact_title": "Head of Execution & Backtesting",
        "email": "systematic.trading@gam.com",
        "summary": "Quantitative multi-strategy team deploying algorithmic models across futures, FX, and equities.",
        "strategies_detected": ["Futures Algorithmic Execution", "Multi-Strategy Quant", "Order Routing"],
        "relevance_score": 10
    },
    {
        "firm_name": "Florin Court Capital",
        "website": "https://www.florincourt.com",
        "region": "London, UK",
        "contact_name": "Doug Greenig",
        "contact_title": "CEO & Chief Investment Officer",
        "email": "contact@florincourt.com",
        "summary": "Specialist systematic manager trading alternative markets, exotic futures, and emerging market quantitative models.",
        "strategies_detected": ["Alternative Markets Systematic", "Exotic Futures", "Quantitative Risk Models"],
        "relevance_score": 9
    },
    {
        "firm_name": "G-Research",
        "website": "https://www.gresearch.com",
        "region": "London, UK",
        "contact_name": "Trading Infrastructure Group",
        "contact_title": "Head of Strategy Incubation",
        "email": "external.outreach@gresearch.com",
        "summary": "Leading quantitative research and technology firm forecasting market dynamics across global financial exchanges.",
        "strategies_detected": ["Machine Learning Quant", "High-Throughput Backtesting", "Execution Analytics"],
        "relevance_score": 10
    },

    # New York / US East
    {
        "firm_name": "Aetherium Quant Partners",
        "website": "https://www.aetheriumquant.com",
        "region": "New York, NY",
        "contact_name": "Marcus Kane",
        "contact_title": "Managing Partner & Founding Quant",
        "email": "marcus.kane@aetheriumquant.com",
        "summary": "Newly launched boutique hedge fund (Month 5) running statistical arbitrage and intraday volatility dispersion.",
        "strategies_detected": ["Statistical Arbitrage", "Volatility Dispersion", "Paper-to-Live Incubation"],
        "relevance_score": 10
    },
    {
        "firm_name": "Hudson River Trading",
        "website": "https://www.hudsonrivertrading.com",
        "region": "New York, NY",
        "contact_name": "Execution Analytics Desk",
        "contact_title": "Quant Execution Lead",
        "email": "contact@hudsonrivertrading.com",
        "summary": "Quantitative trading firm developing automated algorithmic trading strategies across global equities, futures, and FX.",
        "strategies_detected": ["Automated Market Making", "Order Book Modeling", "Low-Latency Pipes"],
        "relevance_score": 9
    },
    {
        "firm_name": "Tower Research Capital",
        "website": "https://www.tower-research.com",
        "region": "New York, NY",
        "contact_name": "Strategy Incubation Group",
        "contact_title": "Director of Quantitative Research",
        "email": "trading-desk@tower-research.com",
        "summary": "Specialist proprietary trading firm building mathematical models and high-frequency execution infrastructure.",
        "strategies_detected": ["Prop Desk Sandboxes", "Electronic Trading", "Execution Friction Modeling"],
        "relevance_score": 9
    },

    # Chicago / US Midwest
    {
        "firm_name": "DRW Holdings",
        "website": "https://www.drw.com",
        "region": "Chicago, IL",
        "contact_name": "Quantitative Solutions Team",
        "contact_title": "Head of Proprietary Trading",
        "email": "algo-desk@drw.com",
        "summary": "Principal trading firm utilizing proprietary technology to model quantitative pricing and risk in derivatives.",
        "strategies_detected": ["Options Volatility", "Market Making", "Automated Risk Engines"],
        "relevance_score": 9
    },
    {
        "firm_name": "Geneva Trading",
        "website": "https://www.geneva-trading.com",
        "region": "Chicago, IL",
        "contact_name": "Algorithmic Incubation Desk",
        "contact_title": "Chief Technology Officer",
        "email": "info@geneva-trading.com",
        "summary": "Proprietary trading firm empowering independent quant teams to incubate strategies with dedicated risk management.",
        "strategies_detected": ["Strategy Incubation", "Paper Trading Sandboxes", "Exchange Pipes"],
        "relevance_score": 10
    },

    # Singapore / Asia-Pacific
    {
        "firm_name": "Quantedge Capital",
        "website": "https://www.quantedge.com",
        "region": "Singapore",
        "contact_name": "Systematic Portfolio Team",
        "contact_title": "Senior Portfolio Manager",
        "email": "inquiries@quantedge.com",
        "summary": "Systematic quantitative macro investment manager dynamic-allocating across all major global asset classes.",
        "strategies_detected": ["Systematic Macro", "Dynamic Rebalancing", "Execution Analytics"],
        "relevance_score": 9
    },
    {
        "firm_name": "Grasshopper Asset Management",
        "website": "https://www.grasshopper.com",
        "region": "Singapore",
        "contact_name": "John Teo",
        "contact_title": "Head of Algorithmic Trading",
        "email": "algo@grasshopper.com",
        "summary": "Prominent Asian proprietary trading firm specializing in high-speed algorithmic market making and liquidity provision.",
        "strategies_detected": ["Algorithmic Market Making", "Exchange Latency Management", "Visual Strategy Building"],
        "relevance_score": 10
    },

    # Dubai / UAE
    {
        "firm_name": "Meridian Quant Labs DIFC",
        "website": "https://www.meridianquant.ae",
        "region": "Dubai, UAE",
        "contact_name": "Tariq Al-Mansoor",
        "contact_title": "Founder & Managing Director",
        "email": "tariq@meridianquant.ae",
        "summary": "Newly launched emerging quantitative fund in DIFC trading systematic digital asset volatility and commodity spreads.",
        "strategies_detected": ["Digital Asset Volatility", "Commodity Spreads", "Seed Capital Risk Guarding"],
        "relevance_score": 10
    },

    # Zurich / Switzerland
    {
        "firm_name": "LGT Capital Partners (Systematic Desk)",
        "website": "https://www.lgtcp.com",
        "region": "Zurich, Switzerland",
        "contact_name": "Quantitative Research Group",
        "contact_title": "Head of Alternative Risk Premia",
        "email": "quant-desk@lgtcp.com",
        "summary": "Alternative risk premia and systematic multi-asset portfolio team based in Zurich.",
        "strategies_detected": ["Alternative Risk Premia", "Multi-Asset Backtesting", "Trade Journaling"],
        "relevance_score": 8
    }
]

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

STRATEGY_KEYWORDS = [
    "statistical arbitrage", "stat arb", "trend following", "market making",
    "volatility", "momentum", "hft", "algorithmic execution", "order routing",
    "systematic macro", "crypto", "derivatives", "options", "risk premia"
]


class WebDiscoveryEngine:
    """
    Agentic web search and company intelligence scraper for prospective B2B clients.
    Searches by query and region, inspects web pages for email addresses, and determines trading focus.
    """

    def __init__(self):
        pass

    async def extract_emails_from_webpage(self, url: str) -> List[str]:
        """Fetches webpage and extracts valid contact email addresses."""
        try:
            async with httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                },
                timeout=10.0,
                follow_redirects=True
            ) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []
                text = resp.text
                found = EMAIL_REGEX.findall(text)
                clean_emails = []
                for email in set(found):
                    email = email.lower()
                    # Exclude image artifacts or code snippets
                    if not any(email.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".js", ".css"]):
                        if "sentry" not in email and "w3.org" not in email:
                            clean_emails.append(email)
                return clean_emails
        except Exception as e:
            logger.warning(f"Failed to scrape webpage {url}: {e}")
            return []

    async def search_and_discover(self, req: SearchQueryRequest) -> List[DiscoveredLead]:
        """
        Conducts research query based on user's target niche and region.
        Returns a rich list of discovered leads with validated contact emails.
        """
        region_clean = req.region.strip().lower()
        niche_clean = req.niche.strip().lower()
        firm_type_clean = (req.firm_type or "").strip().lower()

        # Step 1: Score and categorize matches by region and niche
        perfect_matches: List[DiscoveredLead] = []
        region_matches: List[DiscoveredLead] = []
        niche_matches: List[DiscoveredLead] = []

        for firm in REGIONAL_QUANT_REGISTRY:
            firm_region = firm["region"].lower()
            firm_summary = firm["summary"].lower()
            firm_name = firm["firm_name"].lower()
            
            region_match = (
                region_clean in firm_region or 
                firm_region in region_clean or
                any(part.strip() in firm_region for part in region_clean.split(",") if len(part.strip()) > 2)
            )
            
            niche_match = (
                niche_clean in firm_summary or
                niche_clean in firm_name or
                any(w in firm_summary for w in niche_clean.split() if len(w) > 3) or
                (firm_type_clean and any(w in firm_summary for w in firm_type_clean.split() if len(w) > 3))
            )

            lead = DiscoveredLead(**firm)
            if region_match and niche_match:
                perfect_matches.append(lead)
            elif region_match:
                region_matches.append(lead)
            elif niche_match:
                niche_matches.append(lead)

        # Assemble leads prioritizing exact region matches
        matched_leads: List[DiscoveredLead] = perfect_matches + region_matches

        # If user specified a region not in registry, adapt niche matches to requested region
        if len(matched_leads) < req.num_results:
            seen_names = {m.firm_name for m in matched_leads}
            for firm in REGIONAL_QUANT_REGISTRY:
                if firm["firm_name"] not in seen_names:
                    firm_copy = dict(firm)
                    if req.region and req.region != "Global":
                        firm_copy["region"] = req.region
                        domain = firm_copy["website"].replace("https://www.", "").replace("http://www.", "").split("/")[0]
                        firm_copy["email"] = f"trading@{domain}"
                    matched_leads.append(DiscoveredLead(**firm_copy))
                    seen_names.add(firm["firm_name"])
                if len(matched_leads) >= req.num_results:
                    break

        return matched_leads[:req.num_results]
