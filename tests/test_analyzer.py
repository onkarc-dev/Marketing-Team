"""
Unit tests for Quanteinstein B2B Intelligence Analyzer.
Validates intent scoring rules and connection request generation constraints.
"""

import unittest
import asyncio
from app.models import ProspectInput, AnalysisResult
from app.analyzer import B2BIntelligenceAnalyzer
from app.config import settings


class TestB2BIntelligenceAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = B2BIntelligenceAnalyzer()

    def test_high_intent_slippage_pain_point(self):
        """Rule 1: Pain point explicitly mentioned should score 9-10 and generate message <= 45 words."""
        prospect = ProspectInput(
            name="Marcus Vance",
            company="Apex Alpha Capital",
            title="Head Quant",
            scraped_profile_bio="Managing quantitative equity market-neutral prop book.",
            recent_posts_and_comments="Live execution slippage completely destroyed our statistical arbitrage alpha on the open.",
            recent_company_job_listings="No current listings."
        )

        record = asyncio.run(self.analyzer.analyze_prospect(prospect))
        
        self.assertGreaterEqual(record.score, 9)
        self.assertLessEqual(record.score, 10)
        self.assertIsNotNone(record.message)
        
        # Check max 45 words constraint
        word_count = len(record.message.split())
        self.assertLessEqual(word_count, settings.MAX_MESSAGE_WORDS)
        
        # Check first sentence references trigger
        self.assertTrue(
            "slippage" in record.message.lower() or "friction" in record.message.lower() or "execution" in record.message.lower()
        )

        # Check strict JSON format
        strict = self.analyzer.to_strict_json(record)
        self.assertIn("score", strict)
        self.assertIn("reasoning", strict)
        self.assertIn("message", strict)

    def test_high_intent_hiring_trigger(self):
        """Rule 2: Company actively hiring for this exact problem should score 9-10."""
        prospect = ProspectInput(
            name="Elena Rostova",
            company="Krypton Labs",
            title="CTO",
            scraped_profile_bio="Algorithmic trading firm founder.",
            recent_posts_and_comments="Automating our volatility models.",
            recent_company_job_listings="Hiring: Quant Execution Engineer / Algo Trader to build backtesting infrastructure."
        )

        record = asyncio.run(self.analyzer.analyze_prospect(prospect))
        self.assertGreaterEqual(record.score, 9)
        self.assertIsNotNone(record.message)
        self.assertLessEqual(len(record.message.split()), 45)
        self.assertTrue("hiring" in record.message.lower() or "krypton" in record.message.lower())

    def test_tech_stack_niche_score_8(self):
        """Rule 3: Frequently posting about niche and using tech stack scores 8."""
        prospect = ProspectInput(
            name="David Chen",
            company="Independent",
            title="Systematic Trader",
            scraped_profile_bio="Systematic trading researcher.",
            recent_posts_and_comments="Comparing vectorbt and ccxt backtest execution pipelines for statistical arbitrage.",
            recent_company_job_listings="None."
        )

        record = asyncio.run(self.analyzer.analyze_prospect(prospect))
        self.assertEqual(record.score, 8)
        self.assertIsNotNone(record.message)
        self.assertLessEqual(len(record.message.split()), 45)

    def test_right_icp_no_active_signals_pass(self):
        """Rule 4: Right industry/title but no active signals scores 4-7 and MUST have message = None."""
        prospect = ProspectInput(
            name="Robert Langdon",
            company="OldGuard",
            title="Senior Quantitative Portfolio Manager",
            scraped_profile_bio="Quantitative asset management for institutional macro books.",
            recent_posts_and_comments="Shared an article: Market outlook 2026.",
            recent_company_job_listings="None."
        )

        record = asyncio.run(self.analyzer.analyze_prospect(prospect))
        self.assertGreaterEqual(record.score, 4)
        self.assertLessEqual(record.score, 7)
        self.assertIsNone(record.message)

    def test_irrelevant_prospect_pass(self):
        """Rule 5: Irrelevant domain scores 1-3 and has message = None."""
        prospect = ProspectInput(
            name="Sarah Jenkins",
            company="Realty Corp",
            title="Real Estate Broker",
            scraped_profile_bio="Top luxury real estate agent in Miami.",
            recent_posts_and_comments="Just listed a 4-bedroom oceanfront condo!",
            recent_company_job_listings="Hiring sales assistant."
        )

        record = asyncio.run(self.analyzer.analyze_prospect(prospect))
        self.assertLessEqual(record.score, 3)
        self.assertIsNone(record.message)

    def test_empty_or_placeholder_data_pass(self):
        """Raw template placeholders or empty data must score 1 with null message."""
        prospect = ProspectInput(
            scraped_profile_bio="{scraped_profile_bio}",
            recent_posts_and_comments="{recent_posts_and_comments}",
            recent_company_job_listings="{recent_company_job_listings}"
        )

        record = asyncio.run(self.analyzer.analyze_prospect(prospect))
        self.assertEqual(record.score, 1)
        self.assertIsNone(record.message)


if __name__ == "__main__":
    unittest.main()
