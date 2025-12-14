import os
import json
from typing import Dict, Any

# Try to import Google SDK; fall back to REST when not available
try:
    import google.generativeai as genai  # type: ignore
    _HAS_SDK = True
except Exception:
    genai = None
    _HAS_SDK = False

import requests


class AIEngine:
    """AI engine that uses google.generativeai SDK when available,
    otherwise falls back to the Generative Language REST API.
    Works on desktop and Android.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        # SDK-style vs REST-style model names
        self.sdk_model = model or "gemini-2.5-flash-lite"
        self.rest_model = model or "models/text-bison-001"
        self.base = "https://generativelanguage.googleapis.com/v1"

        self._sdk_model = None
        if _HAS_SDK and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._sdk_model = genai.GenerativeModel(self.sdk_model)
            except Exception:
                self._sdk_model = None

    def set_api_key(self, api_key: str):
        """Updates the API key and refreshes SDK model if available."""
        self.api_key = api_key
        if _HAS_SDK and genai:
            try:
                genai.configure(api_key=api_key)
                self._sdk_model = genai.GenerativeModel(self.sdk_model)
            except Exception:
                self._sdk_model = None

    # REST implementation
    def _rest_call(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise ValueError("API Key is missing. Set GOOGLE_API_KEY or pass api_key to AIEngine.")

        url = f"{self.base}/{self.rest_model}:generateText?key={self.api_key}"
        payload = {
            "prompt": {"text": prompt},
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates") or []
        if candidates:
            return candidates[0].get("output") or candidates[0].get("text") or ""
        return data.get("output", "") or data.get("text", "")

    def _sdk_call(self, prompt: str):
        if not self._sdk_model:
            raise RuntimeError("SDK model not available")
        return self._sdk_model.generate_content(prompt).text

    def generate_lesson(self, subject: str, topic: str) -> str:
        prompt = (
            f"Generate a concise but comprehensive educational text about '{topic}' within the subject of '{subject}'. "
            "The text should be approximately 300 words, suitable for a student to read and then attempt to recall. "
            "Focus on key facts and core concepts. Provide plain text without markdown."
        )

        try:
            if self._sdk_model:
                return self._sdk_call(prompt)
            else:
                return self._rest_call(prompt)
        except Exception as e:
            return f"Error generating content: {e}"

    def analyze_recall(self, original_text: str, user_attempt: str) -> Dict[str, Any]:
        prompt = (
            "You are an expert teacher. Compare the following 'Original Text' with the 'User Attempt' at recalling it.\n\n"
            f"Original Text:\n{original_text}\n\n"
            f"User Attempt:\n{user_attempt}\n\n"
            "Identify missing key facts and misinterpretations. Provide the output in STRICT JSON format:"
            "{\n  \"score\": <0-100>,\n  \"missing_key_facts\": [],\n  \"misinterpretations\": [],\n  \"summary_feedback\": \"...\"\n}\n"
            "Return ONLY the JSON object."
        )

        try:
            if self._sdk_model:
                text = self._sdk_call(prompt)
            else:
                text = self._rest_call(prompt, max_tokens=512)

            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()

            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "score": 0,
                "missing_key_facts": ["Error parsing AI response"],
                "misinterpretations": [],
                "summary_feedback": "The AI response could not be processed."
            }
        except Exception as e:
            return {
                "score": 0,
                "missing_key_facts": [f"System Error: {e}"],
                "misinterpretations": [],
                "summary_feedback": "An error occurred during analysis."
            }
