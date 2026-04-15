import os
import time

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

PRO_MODEL = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config={"temperature": 0.4, "max_output_tokens": 1400},
)

FLASH_MODEL = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={"temperature": 0.3, "max_output_tokens": 900},
)


def _extract_text(response) -> str:
    if response is None:
        return ""
    text = getattr(response, "text", "") or ""
    return text.strip()


def _generate(model, prompt: str, retries: int = 3, initial_backoff_sec: float = 0.8) -> str:
    if not GOOGLE_API_KEY:
        return "Error: Missing GOOGLE_API_KEY. Please set it in your environment or .env file."
    if not prompt or not prompt.strip():
        return "Error: Prompt is empty."

    last_error = "Unknown Gemini error."
    backoff = initial_backoff_sec
    for attempt in range(1, retries + 1):
        try:
            response = model.generate_content(
                prompt,
                request_options={"timeout": 45},
            )
            text = _extract_text(response)
            if text:
                return text
            last_error = "Empty response text from Gemini."
        except Exception as e:
            last_error = str(e)

        if attempt < retries:
            time.sleep(backoff)
            backoff *= 2

    return f"Error: {last_error}"


def ask_pro(prompt: str) -> str:
    return _generate(PRO_MODEL, prompt, retries=3, initial_backoff_sec=0.8)


def ask_flash(prompt: str) -> str:
    return _generate(FLASH_MODEL, prompt, retries=3, initial_backoff_sec=0.6)
