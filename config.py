import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# API & MODEL CONFIGURATION
# ============================================================================
AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1")
HTTP_REFERER = os.getenv("HTTP_REFERER", "http://localhost")
X_TITLE = os.getenv("X_TITLE", "Email Assistant")

# Model names for different components
MODEL_NAME_EMOTION = os.getenv("EMO_MODEL", "openai/gpt-oss-120b:free")
MODEL_NAME_RESPONSE = os.getenv("RESP_MODEL", "openai/gpt-oss-120b:free")

# Temperature settings (deterministic vs creative)
TEMPERATURE_EMOTION = float(os.getenv("TEMPERATURE_EMOTION", "0.1"))  # Low = deterministic
TEMPERATURE_RESPONSE = float(os.getenv("TEMPERATURE_RESPONSE", "0.4"))  # Moderate = balanced

# Retry settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "20"))

# ============================================================================
# EMOTION DETECTION
# ============================================================================
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

# ============================================================================
# EMAIL FORMATTING & TEMPLATES
# ============================================================================
SALUTATION_OPTIONS = [
    "Hi",
    "Hello",
    "Dear",
    "Greetings",
    "Hi there",
]

CLOSING_OPTIONS = [
    "Best regards",
    "Sincerely",
    "Thanks",
    "Best",
    "Warm regards",
    "Kind regards",
    "Respectfully",
]

SIGNATURE_TEMPLATE = """
{name}
{title}
{company}
{email}
{phone}
"""

# Default email format settings
DEFAULT_SALUTATION = "Hi"
DEFAULT_CLOSING = "Best regards"
DEFAULT_INCLUDE_SIGNATURE = True
DEFAULT_TONE_PREFERENCE = "Formal"

TONE_PREFERENCES = [
    "Very Formal",
    "Formal",
    "Neutral",
    "Casual",
    "Very Casual",
]

TONE_DESCRIPTORS = {
    "Very Formal": "Use sophisticated vocabulary, passive voice where appropriate, and maintain strict professional boundaries.",
    "Formal": "Professional and courteous, with proper business language and structure.",
    "Neutral": "Clear and straightforward, without excessive formality or casualness.",
    "Casual": "Friendly and approachable, while maintaining professionalism.",
    "Very Casual": "Conversational and relaxed, using contractions and informal language.",
}

# ============================================================================
# SECURITY & PRIVACY
# ============================================================================
SENSITIVE_KEYWORDS = [
    "legal",
    # "sue",
    "lawsuit",
    "audit",
    "financial statement",
    "confidential",
    "compliance",
]

# Privacy masking patterns
PRIVACY_PATTERNS = {
    "email": (r'[\w\.-]+@[\w\.-]+', "[EMAIL_REDACTED]"),
    "phone": (r'\d{10}', "[PHONE_REDACTED]"),
    "ssn": (r'\d{3}-\d{2}-\d{4}', "[SSN_REDACTED]"),
    "credit_card": (r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}', "[CREDIT_CARD_REDACTED]"),
}

# ============================================================================
# CALENDAR & SCHEDULING
# ============================================================================
CALENDAR_EVENTS = {
    "2024-02-05": "Team Standup",
    "2024-02-06": "Project Alpha Milestone Review",
    "2024-02-08": "Client Meeting",
    "2024-02-15": "Quarterly Review",
}

# ============================================================================
# KNOWLEDGE GRAPH - INITIAL DATA
# ============================================================================
KNOWLEDGE_GRAPH_EDGES = [
    ("Project Alpha", "Alice", "Lead"),
    ("Project Alpha", "2024-02-06", "Deadline"),
    ("Bob", "Finance", "Department"),
    ("Finance", "Quarterly Review", "Process"),
]

# ============================================================================
# VECTOR STORE & RAG
# ============================================================================
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "chroma_db")
VECTOR_COLLECTION_NAME = "emails"
RAG_SEARCH_RESULTS = int(os.getenv("RAG_SEARCH_RESULTS", "3"))

# ============================================================================
# HISTORY PERSISTENCE
# ============================================================================
HISTORY_DIR = os.getenv("HISTORY_DIR", "conversation_history")
HISTORY_FILE_SUFFIX = ".json"
ENABLE_HISTORY_PERSISTENCE = os.getenv("ENABLE_HISTORY_PERSISTENCE", "true").lower() == "true"

# ============================================================================
# UI SETTINGS
# ============================================================================
STREAMLIT_PAGE_TITLE = "Autonomous Email Assistant"
STREAMLIT_PAGE_ICON = "🤖"
STREAMLIT_LAYOUT = "wide"

# Theme configuration
DEFAULT_THEME = "light"  # "light" or "dark"
THEME_OPTIONS = ["light", "dark"]
THEME_EMOJIS = {
    "light": "☀️",
    "dark": "🌙"
}

UI_TEXTS = {
    "nav_title": "📂 Navigation",
    "page_assistant": "🏠 Email Assistant",
    "page_history": "🧵 Thread History",
    "page_about": "ℹ️ About System",
    "subtitle_incoming": "📩 Incoming Email",
    "subtitle_reply": "📤 AI Draft Reply",
    "subtitle_reasoning": "🧠 AI Reasoning & Debug View",
}

# ============================================================================
# VALIDATION
# ============================================================================
MIN_EMAIL_LENGTH = 5
MIN_INSTRUCTION_LENGTH = 0
MAX_INSTRUCTION_LENGTH = 2000
MAX_HISTORY_ITEMS = 100  # Prevent unbounded memory growth
