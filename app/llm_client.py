"""
LLM Client handling Gemini, OpenAI, and fallback mechanisms for B2B Intelligence.
"""

import json
import re
import logging
from typing import Optional, Dict, Any, Tuple
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Clean and parse JSON from raw LLM output even if wrapped in markdown code blocks."""
    if not text:
        return None
    cleaned = text.strip()
    
    # Strip markdown code blocks if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Direct parse attempt
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Regex search for first outer {...}
    match = re.search(r"(\{[\s\S]*\})", cleaned)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None


class LLMClient:
    """Client for invoking LLM APIs with structured JSON output enforcement."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.gemini_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL

    async def call_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Google Gemini API using native JSON mode."""
        if not self.gemini_key:
            logger.warning("Gemini API key is not configured.")
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.error(f"Gemini API returned {resp.status_code}: {resp.text}")
                    return None
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return extract_json_from_text(raw_text)
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None

    async def call_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI API using response_format json_object."""
        if not self.openai_key:
            logger.warning("OpenAI API key is not configured.")
            return None

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": "You are an elite B2B Intelligence Analyst. You always output valid raw JSON without markdown."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"OpenAI API returned {resp.status_code}: {resp.text}")
                    return None
                data = resp.json()
                raw_text = data["choices"][0]["message"]["content"]
                return extract_json_from_text(raw_text)
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None

    async def generate_analysis(self, prompt: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Dispatches request to configured provider with automatic fallback.
        Returns (parsed_json_dict, provider_used)
        """
        if self.provider == "gemini" and self.gemini_key:
            result = await self.call_gemini(prompt)
            if result:
                return result, "gemini"
        elif self.provider == "openai" and self.openai_key:
            result = await self.call_openai(prompt)
            if result:
                return result, "openai"

        # If provider was set to gemini or openai but failed or lacked key, check if other has key
        if self.gemini_key:
            result = await self.call_gemini(prompt)
            if result:
                return result, "gemini"
        if self.openai_key:
            result = await self.call_openai(prompt)
            if result:
                return result, "openai"

        return None, "heuristic"
