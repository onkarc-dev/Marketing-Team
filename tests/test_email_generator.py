"""
Unit & Integration tests for Web Discovery and Cold Email Generator in Quanteinstein.
"""

import unittest
import asyncio
from fastapi.testclient import TestClient
from app.api import app
from app.models import SearchQueryRequest, DiscoveredLead
from app.discovery import WebDiscoveryEngine
from app.email_generator import EmailOutreachGenerator


class TestDiscoveryAndEmailGenerator(unittest.TestCase):

    def setUp(self):
        self.discovery = WebDiscoveryEngine()
        self.generator = EmailOutreachGenerator()
        self.client = TestClient(app)

    def test_search_and_discover_by_region(self):
        """Discovers firms by target region and returns valid emails and strategies."""
        req = SearchQueryRequest(
            niche="statistical arbitrage",
            region="London, UK",
            firm_type="emerging hedge fund",
            num_results=2
        )
        leads = asyncio.run(self.discovery.search_and_discover(req))
        self.assertGreaterEqual(len(leads), 1)
        
        lead = leads[0]
        self.assertTrue("@" in lead.email)
        self.assertTrue(len(lead.strategies_detected) > 0)
        self.assertIsNotNone(lead.website)

    def test_generate_proper_cold_email(self):
        """Generates tailored cold email bridging firm's work into Quanteinstein."""
        lead = DiscoveredLead(
            firm_name="Apex Quant Labs",
            website="https://apexquant.com",
            region="New York, NY",
            contact_name="Elena Rostova",
            contact_title="Head of Systematic Trading",
            email="elena@apexquant.com",
            summary="Boutique trading desk running statistical arbitrage and volatility dispersion.",
            strategies_detected=["Statistical Arbitrage", "Volatility Dispersion"],
            relevance_score=10
        )

        email = self.generator.draft_heuristic_email(lead, sender_name="Onkar (Founder)")
        
        self.assertEqual(email.recipient_email, "elena@apexquant.com")
        self.assertIn("Apex Quant Labs", email.body)
        self.assertIn("New York, NY", email.body)
        self.assertIn("Statistical Arbitrage", email.body)
        self.assertIn("Quanteinstein", email.body)
        self.assertIn("quanteinstein.com", email.body.lower())
        self.assertLessEqual(email.word_count, 170)


    def test_api_discovery_campaign_endpoint(self):
        """Integration test for POST /api/discovery/run-campaign."""
        payload = {
            "niche": "quantitative hedge fund",
            "region": "Singapore",
            "firm_type": "emerging hedge fund",
            "num_results": 2,
            "sender_name": "Technical Founder"
        }
        resp = self.client.post("/api/discovery/run-campaign", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total_discovered"], 1)
        self.assertEqual(len(data["leads"]), len(data["emails"]))
        
        # Test export endpoint
        export_resp = self.client.get("/api/discovery/export-emails")
        self.assertEqual(export_resp.status_code, 200)
        self.assertIn("text/csv", export_resp.headers["content-type"])


if __name__ == "__main__":
    unittest.main()
