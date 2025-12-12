import google.generativeai as genai
import json
import os
from typing import Dict, Any

class AIEngine:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-lite")

    def set_api_key(self, api_key: str):
        """Updates the API key at runtime."""
        self.api_key = api_key
        genai.configure(api_key=api_key)

    def generate_lesson(self, subject: str, topic: str) -> str:
        """
        Generates a structured educational text for a given topic.
        Returns the text content.
        """
        if not self.api_key:
             raise ValueError("API Key is missing. Please set it in Settings.")

        prompt = (
            f"Generate a concise but comprehensive educational text about '{topic}' within the subject of '{subject}'. "
            f"The text should be approximately 300 words, suitable for a student to read and then attempt to recall. "
            f"Focus on key facts, dates (if historical), and core concepts. "
            f"Do not use markdown formatting like bolding or headers, just plain text paragraphs."
        )

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating content: {str(e)}"

    def analyze_recall(self, original_text: str, user_attempt: str) -> Dict[str, Any]:
        """
        Compares the user's recall attempt against the original text.
        Returns a dictionary with score and feedback.
        """
        if not self.api_key:
             raise ValueError("API Key is missing. Please set it in Settings.")

        prompt = (
            "You are an expert teacher. Compare the following 'Original Text' with the 'User Attempt' at recalling it.\n\n"
            f"Original Text:\n{original_text}\n\n"
            f"User Attempt:\n{user_attempt}\n\n"
            "Analyze the attempt for semantic accuracy. Do not penalize for minor wording differences if the meaning is preserved. "
            "Identify missing key facts and any misinterpretations. Give output in the same language as the user attempt.\n"
            "Provide the output in STRICT JSON format with the following structure:\n"
            "{\n"
            '  "score": <integer between 0 and 100>,\n'
            '  "missing_key_facts": [<list of strings>],\n'
            '  "misinterpretations": [<list of strings>],\n'
            '  "summary_feedback": "<concise encouraging feedback string>"\n'
            "}\n"
            "Return ONLY the JSON. Do not include markdown code blocks (```json ... ```)."
        )

        try:
            response = self.model.generate_content(prompt)
            text_response = response.text.strip()
            
            # Clean up potential markdown formatting from the model if it ignores the instruction
            if text_response.startswith("```json"):
                text_response = text_response[7:-3].strip()
            elif text_response.startswith("```"):
                text_response = text_response[3:-3].strip()

            return json.loads(text_response)
        except json.JSONDecodeError:
            # Fallback for malformed JSON
            return {
                "score": 0,
                "missing_key_facts": ["Error parsing AI response"],
                "misinterpretations": [],
                "summary_feedback": "The AI response could not be processed. Please try again."
            }
        except Exception as e:
             return {
                "score": 0,
                "missing_key_facts": [f"System Error: {str(e)}"],
                "misinterpretations": [],
                "summary_feedback": "An error occurred during analysis."
            }
