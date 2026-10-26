"""
Integration tests for FastAPI endpoints in Quanteinstein B2B Intelligence Engine.
"""

import unittest
from fastapi.testclient import TestClient
from app.api import app


class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["project"], "Quanteinstein")

    def test_config_endpoint(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["max_words"], 45)
        self.assertEqual(data["min_score_for_outreach"], 8)

    def test_analyze_strict_high_intent(self):
        payload = {
            "name": "Marcus Vance",
            "company": "Apex Alpha",
            "title": "Head Quant",
            "scraped_profile_bio": "Quant prop firm founder.",
            "recent_posts_and_comments": "Backtest overfitting vs live exchange friction is our biggest headache.",
            "recent_company_job_listings": "Hiring Quant Dev"
        }
        response = self.client.post("/api/analyze/strict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify strict 3-field format
        self.assertIn("score", data)
        self.assertIn("reasoning", data)
        self.assertIn("message", data)
        self.assertGreaterEqual(data["score"], 8)
        self.assertIsNotNone(data["message"])
        self.assertLessEqual(len(data["message"].split()), 45)

    def test_analyze_strict_low_intent(self):
        payload = {
            "name": "Sarah",
            "company": "Real Estate",
            "title": "Realtor",
            "scraped_profile_bio": "Real estate broker.",
            "recent_posts_and_comments": "Selling homes.",
            "recent_company_job_listings": "None"
        }
        response = self.client.post("/api/analyze/strict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLess(data["score"], 8)
        self.assertIsNone(data["message"])

    def test_batch_analysis(self):
        payload = {
            "prospects": [
                {
                    "name": "High Intent Lead",
                    "company": "Alpha Desk",
                    "scraped_profile_bio": "Quant trader",
                    "recent_posts_and_comments": "Suffering from severe slippage during morning opens.",
                    "recent_company_job_listings": "None"
                },
                {
                    "name": "Pass Lead",
                    "company": "Unknown",
                    "scraped_profile_bio": "Marketing consultant",
                    "recent_posts_and_comments": "Social media tips.",
                    "recent_company_job_listings": "None"
                }
            ]
        }
        response = self.client.post("/api/batch", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["high_intent_count"], 1)
        self.assertEqual(data["passed_count"], 1)


if __name__ == "__main__":
    unittest.main()
