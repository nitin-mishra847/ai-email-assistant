import streamlit as st
import logging

import config
from ai_handler import AIHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------
# Page Config
# --------------------------------
st.set_page_config(
    page_title=config.STREAMLIT_PAGE_TITLE,
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout=config.STREAMLIT_LAYOUT
)

# --------------------------------
# Session State
# --------------------------------
if "handler" not in st.session_state:
    st.session_state.handler = AIHandler()

# --------------------------------
# Sidebar Navigation
# --------------------------------
st.sidebar.title(config.UI_TEXTS["nav_title"])
page = st.sidebar.radio(
    "Go to",
    [
        config.UI_TEXTS["page_assistant"],
        config.UI_TEXTS["page_history"],
        config.UI_TEXTS["page_about"],
    ]
)

# --------------------------------
# PAGE 1: EMAIL ASSISTANT
# --------------------------------
if page == config.UI_TEXTS["page_assistant"]:
    st.title("📨 Autonomous Email Reply Generator")
    st.caption("Paste an email and let AI draft a context-aware reply")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(config.UI_TEXTS["subtitle_incoming"])
        email_input = st.text_area(
            "Paste email content here",
            height=200,
            placeholder="Dear Team, I am facing an issue with..."
        )

        # NEW: Customization Section
        with st.expander("⚙️ Customization & Instructions", expanded=False):
            st.markdown("**Special instructions for the AI:**")
            user_instructions = st.text_area(
                "Instructions",
                height=80,
                placeholder="E.g., Keep it brief, mention the budget constraints, be empathetic, etc.",
                label_visibility="collapsed",
            )

            st.markdown("**Tone preference:**")
            tone_preference = st.select_slider(
                "Select tone",
                options=config.TONE_PREFERENCES,
                value=config.DEFAULT_TONE_PREFERENCE,
                label_visibility="collapsed",
            )

            st.markdown("**Email format:**")
            col_sal, col_clos = st.columns(2)
            
            with col_sal:
                salutation = st.selectbox(
                    "Salutation",
                    options=config.SALUTATION_OPTIONS,
                    index=config.SALUTATION_OPTIONS.index(config.DEFAULT_SALUTATION),
                    label_visibility="collapsed",
                )

            with col_clos:
                closing = st.selectbox(
                    "Closing",
                    options=config.CLOSING_OPTIONS,
                    index=config.CLOSING_OPTIONS.index(config.DEFAULT_CLOSING),
                    label_visibility="collapsed",
                )

            include_signature = st.checkbox(
                "Include signature block",
                value=config.DEFAULT_INCLUDE_SIGNATURE,
            )

        if st.button("🚀 Generate AI Reply", use_container_width=True):
            if email_input.strip():
                with st.spinner("🔍 Consulting Knowledge Graph & Vector DB..."):
                    try:
                        reply, metadata = st.session_state.handler.generate_response(
                            email_input,
                            user_instructions=user_instructions,
                            tone_preference=tone_preference,
                            salutation=salutation,
                            closing=closing,
                            include_signature=include_signature,
                        )
                        st.session_state.last_reply = reply
                        st.session_state.last_meta = metadata
                        logger.info("Email reply generated successfully")
                    except Exception as e:
                        st.error(f"Error generating reply: {str(e)}")
                        logger.error(f"Error: {str(e)}", exc_info=True)
            else:
                st.warning("Please paste an email first.")

    with col2:
        st.subheader(config.UI_TEXTS["subtitle_reply"])
        if "last_reply" in st.session_state:
            if "SYSTEM" in st.session_state.last_reply or "Error" in st.session_state.last_reply:
                st.error(st.session_state.last_reply)
            else:
                # Display the reply in a text area for easy copying
                st.text_area(
                    "Email Draft (select and copy):",
                    value=st.session_state.last_reply,
                    height=260,
                    disabled=True,
                    label_visibility="collapsed",
                )
        else:
            st.info("Generate an email reply to see the draft here.")

    st.divider()

    st.subheader(config.UI_TEXTS["subtitle_reasoning"])
    st.caption("Transparency into how the AI made decisions")

    if "last_meta" in st.session_state:
        meta = st.session_state.last_meta

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Detected Emotion", meta.get("emotion", "N/A"))
        col2.metric("Tone Preference", meta.get("tone_preference", "N/A"))
        col3.metric("Calendar Logic", "Applied" if meta.get("calendar_logic_applied") else "N/A")
        col4.metric("KG Context Used", "Yes" if meta.get("kg_nodes") else "No")

        st.subheader("🔗 Knowledge Graph Connections")
        kg_info = meta.get("kg_nodes", "No connections found")
        if kg_info:
            st.info(kg_info)
        else:
            st.info("No relevant knowledge graph connections for this email.")

        st.subheader("📅 Calendar Information")
        cal_info = meta.get("calendar_check", "No conflicts detected")
        if "conflict" not in cal_info.lower() and cal_info != "No calendar conflicts detected.":
            st.warning(cal_info)
        else:
            st.info(cal_info)
    else:
        st.info("Generate an email reply first to view reasoning.")
    st.divider()
     
    st.subheader("📈 System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        history_count = len(st.session_state.handler.history_manager)
        st.metric("Conversation Items", history_count)
    
    with col2:
        st.metric("AI Model", config.MODEL_NAME_RESPONSE.split("/")[-1])
    
    with col3:
        st.metric("History Persistence", "✅ Enabled" if config.ENABLE_HISTORY_PERSISTENCE else "❌ Disabled")


# --------------------------------
# PAGE 3: THREAD HISTORY
# --------------------------------
elif page == config.UI_TEXTS["page_history"]:
    st.title("🧵 Email Thread Context")
    st.caption("Conversation memory used for RAG and context")

    # History controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("**Conversation History**")
    
    with col2:
        if st.button("🔄 Refresh", help="Reload history from disk"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear All", help="Clear entire conversation history"):
            st.session_state.handler.history_manager.clear_history()
            st.success("History cleared successfully!")
            st.rerun()

    # Display history
    if st.session_state.handler.history_manager:
        history_items = st.session_state.handler.history_manager.get_history(as_string=False)
        
        if history_items:
            st.markdown(f"**Total items:** {len(history_items)}")
            
            # Display in expandable sections
            for i, item in enumerate(reversed(history_items[-20:]), 1):  # Show last 20
                with st.expander(f"Entry {len(history_items) - i + 1}: {item[:60]}..."):
                    st.text(item)
            
            # Export option
            if st.button("📥 Export History as JSON"):
                export_path = "email_history_export.json"
                success = st.session_state.handler.history_manager.export_history(export_path)
                if success:
                    st.success(f"History exported to {export_path}")
                    with open(export_path, 'r') as f:
                        st.download_button(
                            label="Download JSON",
                            data=f.read(),
                            file_name=export_path,
                            mime="application/json"
                        )
            
        else:
            st.info("No conversation history yet. Generate some email replies to populate the history.")
    else:
        st.info("History manager not initialized.")

# --------------------------------
# PAGE 4: ABOUT SYSTEM
# --------------------------------
elif page == config.UI_TEXTS["page_about"]:
    st.title("ℹ️ About Autonomous Email Assistant")

    st.markdown(
        """
        ### 🤖 What this system does
        - Uses **RAG (Retrieval-Augmented Generation)** with ChromaDB vector store
        - Connects to a **Knowledge Graph** using NetworkX for context awareness
        - Detects **tone & emotion** using advanced LLM analysis
        - Escalates **sensitive emails** automatically for human review
        - Maintains **persistent conversation history** with export capabilities
        - Respects **user preferences** for tone, format, and special instructions
        - Applies **privacy masking** to sensitive information (emails, phone numbers, SSNs, credit cards)

        ### 🛡️ Design Principles
        - Privacy-first architecture with automatic redaction
        - Explainable AI reasoning with transparent debug view
        - Enterprise-ready with comprehensive error handling and logging
        - Configurable via environment variables and `config.py`
        - Persistent state management for multi-session continuity

        ### ⚙️ Configuration
        All system behavior can be customized through:
        - **`.env` file** for API keys and endpoints
        - **`config.py`** for templates, defaults, and limits
        - **UI controls** for per-email customization (tone, instructions, format)

        ### 🚀 Ideal Use Cases
        - Executive inbox automation and assistance
        - Support ticket response generation
        - Internal IT/helpdesk communications
        - Compliance-aware customer outreach
        - Multi-user team collaboration with shared context

        ### 🔐 Security Features
        - Sensitive keyword detection and escalation
        - Automatic PII (Personally Identifiable Information) masking
        - Configurable redaction patterns
        - Rate limiting and retry logic for API stability

        ### 📊 Upcoming Features
        - Multi-user session management
        - Advanced RAG with semantic search tuning
        - Custom LLM model selection per task
        - Email template library
        - Analytics dashboard for usage patterns
        """
    )

    st.divider()

    st.success("Built for enterprise-scale autonomous communication ✨")
