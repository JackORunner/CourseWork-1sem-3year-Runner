import os
import json
from typing import Dict, Any, Optional
import re

# Defaults for instructions
DEFAULT_READ_INSTRUCTION = (
    "Read the material carefully and focus on understanding the main ideas. "
    "Do not take notes; just read and absorb the concepts."
)
DEFAULT_RECALL_INSTRUCTION = (
    "Close the text and reconstruct it from memory in your own words. "
    "Cover key facts, definitions, and relationships."
)

# Try to import Google SDK; fall back to REST when not available
try:
    import google.generativeai as genai  # type: ignore[import-not-found]
    _HAS_SDK: bool = True
except Exception:
    genai: Any = None
    _HAS_SDK = False

import requests


class AIEngine:
    """AI engine that uses google.generativeai SDK when available,
    otherwise falls back to the Generative Language REST API.
    Works on desktop and Android.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key: Optional[str] = api_key or os.getenv("GOOGLE_API_KEY")
        # SDK-style vs REST-style model names
        self.sdk_model: str = (model or "gemini-2.5-flash")
        # REST defaults to a Gemini model to avoid 404s on deprecated PaLM endpoints
        self.rest_model: str = (model or "models/gemini-2.5-flash")
        self.base = "https://generativelanguage.googleapis.com"

        self._sdk_model: Optional[Any] = None
        if _HAS_SDK and self.api_key:
            try:
                # Use getattr to avoid Pylance private export errors.
                configure = getattr(genai, "configure", None)
                generative_model_cls = getattr(genai, "GenerativeModel", None)
                if callable(configure):
                    configure(api_key=self.api_key)  # type: ignore[misc]
                if generative_model_cls is not None:
                    self._sdk_model = generative_model_cls(self.sdk_model)  # type: ignore[call-arg]
            except Exception:
                self._sdk_model = None

    def set_api_key(self, api_key: str):
        """Updates the API key and refreshes SDK model if available."""
        self.api_key = api_key
        if _HAS_SDK and genai:
            try:
                configure = getattr(genai, "configure", None)
                generative_model_cls = getattr(genai, "GenerativeModel", None)
                if callable(configure):
                    configure(api_key=api_key)  # type: ignore[misc]
                if generative_model_cls is not None:
                    self._sdk_model = generative_model_cls(self.sdk_model)  # type: ignore[call-arg]
            except Exception:
                self._sdk_model = None

    # REST implementation
    def _rest_call(self, prompt: str, max_tokens: int = 2500, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise ValueError("API Key is missing. Set GOOGLE_API_KEY or pass api_key to AIEngine.")
        # Gemini REST uses generateContent on v1beta; fall back to v1 for legacy models if needed.
        version = "v1beta" if "gemini" in self.rest_model else "v1"
        url = f"{self.base}/{version}/{self.rest_model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Extract the first candidate text if present.
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts") or []
            if parts and isinstance(parts[0], dict):
                return parts[0].get("text", "") or parts[0].get("content", "") or ""
        # Fall back to an error message to make failures explicit
        return json.dumps({"error": "empty_response", "data": data})

    def _sdk_call(self, prompt: str):
        if not self._sdk_model:
            raise RuntimeError("SDK model not available")
        return self._sdk_model.generate_content(prompt).text

    def generate_lesson(self, subject: str, topic: str) -> str:
        prompt = (
            f"Generate a concise but comprehensive educational text about '{topic}' within the subject of '{subject}'. "
            "The text should be approximately 300 words, suitable for a student to read and then attempt to recall. "
            "Focus on key facts and core concepts. Give output in the same language as the topic. Provide plain text without markdown. \n\n"
        ) # формування промпту

        try:
            if self._sdk_model:
                return self._sdk_call(prompt)
            else:
                return self._rest_call(prompt)
        except Exception as e:
            return f"Error generating content: {e}"

    def _sanitize_instruction(self, text: Optional[str], fallback: str) -> str:
        if not text:
            return fallback
        clean = text.strip()
        # Simple sanity checks: must have letters, length, and not be mostly repeated chars
        if len(clean) < 4:
            return fallback
        alpha_ratio = sum(ch.isalpha() for ch in clean) / max(len(clean), 1)
        if alpha_ratio < 0.3:
            return fallback
        if len(set(clean.lower())) < 4:
            return fallback
        return clean

    def analyze_recall(
        self,
        original_text: str,
        user_attempt: str,
        recall_instruction: Optional[str] = None,
        memorization_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        # Validate custom instruction; fallback to default if empty or nonsensical
        safe_recall = self._sanitize_instruction(recall_instruction, DEFAULT_RECALL_INSTRUCTION)
        safe_read = self._sanitize_instruction(memorization_instruction, DEFAULT_READ_INSTRUCTION)
        prompt = (
            "You are a strict evaluator. Your goal is to grade a student based on how well they followed the instructions provided below.\n\n"
            
            f"--- CONTEXT (What the student was told to memorize) ---\n"
            f"Memorization Instruction: \"{safe_read}\"\n\n"  
            
            f"--- CURRENT TASK (What the student must do now) ---\n"
            f"Recall Instruction: \"{safe_recall}\"\n\n"
            
            f"--- RULES OF EVALUATION ---\n"
            f"1. SCOPE: Focus ONLY on the information requested in the Instructions above.\n"
            f"2. CONNECTIVITY: If 'Recall Instruction' refers to the 'previous stage' or 'memorization task', refer to the 'Memorization Instruction' to understand what facts are required.\n" # <--- ВАЖЛИВЕ ПРАВИЛО
            f"3. IGNORE EXTRA: If the Original Text contains details NOT requested, do NOT count them as missing.\n"
            f"4. MISSING FACTS: The list 'missing_key_facts' must ONLY contain facts that were REQUESTED but OMITTED.\n"
            f"5. SCORE: If the user fulfilled the specific instruction perfectly, the score must be 100.\n\n"
            
            f"Original Text (Source Material):\n{original_text}\n\n"
            
            f"User Attempt:\n{user_attempt}\n\n"
            
            "Analyze the attempt based on the Rules above. Provide output in the same language as the User Attempt / Original Text.\n"
            "Return STRICT JSON format:\n"
            "{\n  \"score\": <0-100>,\n  \"missing_key_facts\": [],\n  \"misinterpretations\": [],\n  \"summary_feedback\": \"...\"\n}\n"
            "Return ONLY the JSON object."
        )
        
        try:
            if self._sdk_model:
                text = self._sdk_call(prompt)
            else:
                text = self._rest_call(prompt, max_tokens=2500)

            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()

            # Try direct JSON first
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
            # ----------------
                raw_snippet = text[:4000]
                # Fallback: extract the first JSON-looking block
                start = raw_snippet.find("{")
                end = raw_snippet.rfind("}")
                if start != -1 and end != -1 and end > start:
                    candidate = raw_snippet[start : end + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        pass
                # Heuristic parse: pull score and missing_key_facts if present
                score_match = re.search(r'"score"\s*[:=]\s*(\d+)', raw_snippet, re.IGNORECASE)
                score_val = int(score_match.group(1)) if score_match else 0
                facts: list[str] = []
                facts_block = re.search(r'"missing_key_facts"\s*[:=]\s*\[(.*?)\]', raw_snippet, re.IGNORECASE | re.DOTALL)
                if facts_block:
                    for piece in re.findall(r'"(.*?)"', facts_block.group(1)):
                        cleaned = piece.strip()
                        if cleaned:
                            facts.append(cleaned)
                if facts:
                    print("[AIEngine] Heuristic parse used. Raw snippet:", raw_snippet)
                    return {
                        "score": score_val,
                        "missing_key_facts": facts,
                        "misinterpretations": [],
                        "summary_feedback": "Parsed with fallback; check raw output.",
                        "_raw": raw_snippet,
                    }

                # Final fallback: show full raw text so the user sees the exact error/response
                print("[AIEngine] JSON parse fallback. Raw response snippet:", raw_snippet)
                return {
                    "score": 0.12,
                    "missing_key_facts": [f"Error parsing AI response{raw_snippet}"],
                    "misinterpretations": [],
                    "summary_feedback": raw_snippet,
                    "_raw": raw_snippet,
                }
        except Exception as e:
            return {
                "score": 0,
                "missing_key_facts": [f"System Error: {e}"],
                "misinterpretations": [],
                "summary_feedback": f"System error: {e}",
                "_raw": str(e),
            }
