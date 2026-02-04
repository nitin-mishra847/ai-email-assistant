import os
import time
import json
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI, RateLimitError

import config
from rag_pipeline import RAGPipeline
from prompts import EMAIL_RESPONSE_PROMPT
from emotion_detection import detect_emotion
from style_enforcer import StyleEnforcer
from history_manager import HistoryManager

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailResponseSchema(BaseModel):
    subject_line: Optional[str] = Field(default=None)
    draft: str
    detected_tone: str
    calendar_logic_applied: bool
    suggested_follow_up_date: Optional[str] = None


class AIHandler:
    def __init__(self, session_name: str = "default"):
        self.client = OpenAI(
            base_url=config.AI_BASE_URL,
            api_key=config.AI_API_KEY,
            default_headers={
                "HTTP-Referer": config.HTTP_REFERER,
                "X-Title": config.X_TITLE,
            },
        )
        self.model_name = config.MODEL_NAME_RESPONSE
        self.rag = RAGPipeline()
        self.enforcer = StyleEnforcer()
        self.history_manager = HistoryManager(session_name=session_name)
        
        logger.info(f"AIHandler initialized with model: {self.model_name}")

    @property
    def history(self) -> str:
        """Get conversation history as a string for backward compatibility."""
        return self.history_manager.get_history(as_string=True)

    def generate_response(
        self, 
        email_body: str,
        user_instructions: str = "",
        tone_preference: str = config.DEFAULT_TONE_PREFERENCE,
        salutation: str = config.DEFAULT_SALUTATION,
        closing: str = config.DEFAULT_CLOSING,
        include_signature: bool = config.DEFAULT_INCLUDE_SIGNATURE,
    ) -> Tuple[str, dict]:
        """
        Generate an AI email response with user customizations.
        
        Args:
            email_body: The incoming email text
            user_instructions: Optional special instructions for the AI
            tone_preference: Preferred tone (e.g., "Formal", "Casual")
            salutation: Email salutation (e.g., "Hi", "Dear")
            closing: Email closing (e.g., "Best regards", "Sincerely")
            include_signature: Whether to include signature block
            
        Returns:
            Tuple of (reply_text, metadata_dict)
        """
        # Validate inputs
        if not email_body or not isinstance(email_body, str):
            return "❌ Error: Invalid email input.", {}
        
        if len(email_body.strip()) < config.MIN_EMAIL_LENGTH:
            return f"❌ Error: Email is too short (minimum {config.MIN_EMAIL_LENGTH} characters).", {}
        
        if user_instructions and len(user_instructions) > config.MAX_INSTRUCTION_LENGTH:
            return f"❌ Error: Instructions exceed maximum length of {config.MAX_INSTRUCTION_LENGTH} characters.", {}
        
        # Normalize tone preference
        if tone_preference not in config.TONE_PREFERENCES:
            logger.warning(f"Invalid tone preference '{tone_preference}', using default")
            tone_preference = config.DEFAULT_TONE_PREFERENCE
        
        tone_descriptor = config.TONE_DESCRIPTORS.get(tone_preference, "")
        
        logger.info(f"Generating response with tone: {tone_preference}, instructions length: {len(user_instructions)}")
        
        # 1️⃣ Emotion Detection
        emotion = detect_emotion(email_body)
        logger.info(f"Detected emotion: {emotion}")
        
        # 2️⃣ Security Check - Escalation
        escalate, reason, highlighted_text = self.enforcer.check_escalation(email_body)
        if escalate:
            warning_msg = f"⚠️ SYSTEM: {reason}\n\n---\n\n🔍 **Email Content (Sensitive Keywords Highlighted):**\n\n{highlighted_text}\n\n---\n\nThis email has been flagged for human review due to sensitive content."
            logger.warning(reason)
            self.history_manager.add_entry("User", email_body)
            self.history_manager.add_entry("System", warning_msg)
            return warning_msg, {"escalated": True, "reason": reason}

        # 3️⃣ Context Retrieval
        rag_docs, kg_context, calendar_context = self.rag.retrieve_context(email_body)
        logger.debug(f"Retrieved {len(rag_docs)} RAG documents, KG context: {len(kg_context)} chars")

        # 4️⃣ Prompt Construction with new parameters
        full_prompt = EMAIL_RESPONSE_PROMPT.format(
            tone_preference=tone_preference,
            tone_descriptor=tone_descriptor,
            rag_context="\n".join(rag_docs) if rag_docs else "No relevant context found.",
            kg_context=kg_context if kg_context else "No knowledge graph connections.",
            thread_history=self.history if self.history else "No previous conversation history.",
            calendar_context=calendar_context if calendar_context else "No calendar conflicts.",
            style_examples="Professional, concise.",
            user_instructions=user_instructions if user_instructions else "None specified.",
            emotion=emotion,
            email_body=email_body,
            salutation_example=salutation,
            closing_example=closing,
        )

        structured_instruction = """
        Return ONLY valid JSON in this format:
        {
        "subject_line": string or null,
        "draft": string,
        "detected_tone": string,
        "calendar_logic_applied": boolean,
        "suggested_follow_up_date": string or null
        }
        Do not include explanations or markdown.
        """

        retries = 0
        response_data = None
        
        while retries <= config.MAX_RETRIES:
            try:
                logger.debug(f"API call attempt {retries + 1}/{config.MAX_RETRIES + 1}")
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an Executive Communications Assistant. Return only valid JSON.",
                        },
                        {
                            "role": "user",
                            "content": structured_instruction + "\n\n" + full_prompt,
                        },
                    ],
                    temperature=config.TEMPERATURE_RESPONSE,
                )

                if not response or not hasattr(response, 'choices') or not response.choices:
                    logger.error("Invalid response structure from API")
                    if retries < config.MAX_RETRIES:
                        retries += 1
                        continue
                    break

                raw_output = response.choices[0].message.content
                if not raw_output:
                    logger.error("Empty response content from API")
                    if retries < config.MAX_RETRIES:
                        retries += 1
                        continue
                    break
                
                raw_output = raw_output.strip()
                logger.debug(f"Raw API output: {raw_output[:200]}...")

                # Attempt JSON parse
                try:
                    parsed_json = json.loads(raw_output)
                    response_data = EmailResponseSchema(**parsed_json)
                    break
                    
                except (json.JSONDecodeError, ValidationError) as e:
                    logger.warning(f"Failed to parse structured response: {str(e)}")
                    # Fallback if model fails structured formatting
                    response_data = EmailResponseSchema(
                        subject_line=None,
                        draft=raw_output,
                        detected_tone=emotion,
                        calendar_logic_applied=bool(calendar_context),
                        suggested_follow_up_date=None,
                    )
                    break

            except RateLimitError as e:
                if retries >= config.MAX_RETRIES:
                    logger.error(f"Rate limited after {config.MAX_RETRIES} retries")
                    return "❌ Error: API rate limit exceeded. Please try again in a moment.", {}
                    
                logger.warning(f"Rate limit hit, retrying in {config.RETRY_DELAY_SECONDS}s... (attempt {retries + 1}/{config.MAX_RETRIES})")
                time.sleep(config.RETRY_DELAY_SECONDS)
                retries += 1
                
            except Exception as e:
                logger.error(f"Error generating response: {type(e).__name__}: {str(e)}", exc_info=True)
                return f"❌ Error generating response: {str(e)}", {}

        if not response_data:
            logger.error("Failed to generate response after all retries")
            return "❌ Error: Could not generate email response. Please try again.", {}

        # 5️⃣ Privacy Enforcement
        final_draft = self.enforcer.check_privacy(response_data.draft)
        logger.debug("Privacy masking applied")

        # 6️⃣ History Update
        self.history_manager.add_entry("User", email_body)
        self.history_manager.add_entry("AI", final_draft)

        # Return with metadata
        metadata = {
            "emotion": emotion,
            "tone_preference": tone_preference,
            "salutation": salutation,
            "closing": closing,
            "include_signature": include_signature,
            "kg_nodes": kg_context,
            "calendar_check": calendar_context,
            "detected_tone": response_data.detected_tone,
            "calendar_logic_applied": response_data.calendar_logic_applied,
            "suggested_follow_up_date": response_data.suggested_follow_up_date,
            "user_instructions_applied": bool(user_instructions),
        }
        
        logger.info("Response generated successfully")
        return final_draft, metadata
