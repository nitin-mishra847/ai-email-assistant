import re
import logging

import config

logger = logging.getLogger(__name__)


class StyleEnforcer:
    def __init__(self):
        self.privacy_patterns = config.PRIVACY_PATTERNS
        self.sensitive_keywords = config.SENSITIVE_KEYWORDS
        logger.debug("StyleEnforcer initialized")

    def check_privacy(self, text):
        """
        Mask sensitive information in text using regex patterns.
        
        Args:
            text: The text to mask
            
        Returns:
            Text with sensitive information masked
        """
        try:
            if not text or not isinstance(text, str):
                return text
            
            masked_text = text
            
            # Apply all privacy patterns
            for pattern_name, (pattern, replacement) in self.privacy_patterns.items():
                try:
                    masked_text = re.sub(pattern, replacement, masked_text)
                except Exception as e:
                    logger.warning(f"Error applying {pattern_name} pattern: {str(e)}")
            
            logger.debug(f"Applied privacy masking to text ({len(text)} -> {len(masked_text)} chars)")
            return masked_text
            
        except Exception as e:
            logger.error(f"Error in check_privacy: {str(e)}", exc_info=True)
            return text  # Return original text if masking fails

    def check_escalation(self, text):
        """
        Check if text contains sensitive keywords requiring escalation.
        Uses word boundary matching to avoid partial matches.
        
        Args:
            text: The text to check
            
        Returns:
            Tuple of (should_escalate, reason_message, highlighted_text)
        """
        try:
            if not text or not isinstance(text, str):
                return False, "Safe", text
            
            text_lower = text.lower()
            found_keywords = []
            highlighted_text = text
            
            # Check each keyword with word boundaries
            for keyword in self.sensitive_keywords:
                # Use word boundaries to match whole words only
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower, re.IGNORECASE):
                    found_keywords.append(keyword)
                    # Highlight the keyword in the text
                    highlighted_text = re.sub(
                        pattern,
                        lambda m: f"🚨 [{m.group(0).upper()}] 🚨",
                        highlighted_text,
                        flags=re.IGNORECASE
                    )
            
            if found_keywords:
                keywords_str = ", ".join([f"'{k}'" for k in found_keywords])
                reason = f"ESCALATION: Sensitive keyword(s) detected: {keywords_str}"
                logger.warning(reason)
                return True, reason, highlighted_text
            
            logger.debug("No escalation keywords detected")
            return False, "Safe", text
            
        except Exception as e:
            logger.error(f"Error in check_escalation: {str(e)}", exc_info=True)
            return False, "Safe", text