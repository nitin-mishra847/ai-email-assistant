import os
import json
import time
import logging
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv
import config

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EMOTIONS = [
    "Urgent",
    "Angry/Negative",
    "Happy/Positive",
    "Neutral",
    "Concerned",
    "Frustrated",
    "Disappointed",
    "Appreciative",
]


class EmotionDetector:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.AI_API_KEY,
            base_url=config.AI_BASE_URL,
            default_headers={
                "HTTP-Referer": config.HTTP_REFERER,
                "X-Title": config.X_TITLE,
            },
        )
        self.model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
        self.max_retries = int(os.getenv("MAX_RETRIES", "2"))
        self.retry_delay = int(os.getenv("RETRY_DELAY_SECONDS", "20"))

    def detect_emotion(self, text: str) -> str:
        """
        Detect emotion from email text.
        Returns one of the ALLOWED_EMOTIONS or 'Neutral' as fallback.
        """
        if not text or not isinstance(text, str):
            logger.warning("Invalid text input for emotion detection")
            return "Neutral"
        
        if len(text.strip()) < 5:
            logger.info("Text too short for meaningful emotion detection")
            return "Neutral"
        
        # Format emotions list as proper string for the prompt
        emotions_str = ", ".join(ALLOWED_EMOTIONS)
        prompt = f"""
        Classify the emotional tone of the following email.

        Allowed emotions: {emotions_str}

        Return ONLY valid JSON:
        {{
        "emotion": "<one of the above>"
        }}

        Email:
        {text}
        """

        retries = 0
        while retries <= self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert emotional tone classifier for corporate emails. Return only valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                )

                # Check if response and choices exist
                if not response or not hasattr(response, 'choices') or not response.choices:
                    logger.error("Invalid response structure from API")
                    return "Neutral"
                
                raw = response.choices[0].message.content
                if not raw:
                    logger.error("Empty response content from API")
                    return "Neutral"
                
                raw = raw.strip()
                logger.debug(f"Raw emotion response: {raw}")
                
                try:
                    parsed = json.loads(raw)
                    emotion = parsed.get("emotion", "Neutral")

                    if emotion not in ALLOWED_EMOTIONS:
                        logger.warning(f"Invalid emotion '{emotion}' not in allowed list, defaulting to Neutral")
                        return "Neutral"

                    logger.info(f"Detected emotion: {emotion}")
                    return emotion

                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in emotion detection: {e}")
                    return "Neutral"

            except RateLimitError as e:
                if retries >= self.max_retries:
                    logger.error(f"Rate limited after {self.max_retries} retries")
                    return "Neutral"
                logger.warning(f"Rate limit hit, retrying in {self.retry_delay}s... (attempt {retries + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
                retries += 1

            except Exception as e:
                logger.error(f"Unexpected error in emotion detection: {type(e).__name__}: {str(e)}", exc_info=True)
                return "Neutral"
        
        return "Neutral"


_detector = EmotionDetector()


def detect_emotion(text: str) -> str:
    """
    Module-level function to detect emotion from email text.
    Uses singleton detector instance.
    """
    return _detector.detect_emotion(text)
