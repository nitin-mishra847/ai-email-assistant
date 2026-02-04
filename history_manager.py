import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import config

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Manages conversation history persistence to disk.
    Automatically loads history on startup and saves new entries.
    """

    def __init__(self, session_name: str = "default"):
        """
        Initialize history manager.
        
        Args:
            session_name: Name of the session for file storage (e.g., "user_email", "project_alpha")
        """
        self.session_name = session_name
        self.history_dir = config.HISTORY_DIR
        self.max_items = config.MAX_HISTORY_ITEMS
        self.enable_persistence = config.ENABLE_HISTORY_PERSISTENCE
        
        # Create history directory if it doesn't exist
        if self.enable_persistence:
            os.makedirs(self.history_dir, exist_ok=True)
        
        self.history: List[str] = []
        
        # Load existing history
        if self.enable_persistence:
            self._load_history()

    def _get_history_file(self) -> str:
        """Get the full path to the history file."""
        filename = f"{self.session_name}{config.HISTORY_FILE_SUFFIX}"
        return os.path.join(self.history_dir, filename)

    def _load_history(self) -> None:
        """Load conversation history from disk."""
        if not self.enable_persistence:
            return
        
        history_file = self._get_history_file()
        
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, dict) and 'conversations' in data:
                        # Extract just the text from the new format
                        self.history = []
                        for entry in data['conversations']:
                            if 'role' in entry and 'content' in entry:
                                self.history.append(f"{entry['role']}: {entry['content']}")
                    elif isinstance(data, list):
                        # Old format: list of strings
                        self.history = data
                    
                    logger.info(f"Loaded {len(self.history)} history items from {history_file}")
            else:
                logger.info(f"No existing history file at {history_file}")
                
        except Exception as e:
            logger.error(f"Error loading history from {history_file}: {str(e)}")
            self.history = []

    def _save_history(self) -> None:
        """Save conversation history to disk in structured format."""
        if not self.enable_persistence:
            return
        
        history_file = self._get_history_file()
        
        try:
            # Parse history entries into structured format
            conversations = []
            for entry in self.history:
                if ': ' in entry:
                    role, content = entry.split(': ', 1)
                    conversations.append({
                        'role': role,
                        'content': content,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    conversations.append({
                        'role': 'Unknown',
                        'content': entry,
                        'timestamp': datetime.now().isoformat()
                    })
            
            data = {
                'session_name': self.session_name,
                'created_at': datetime.now().isoformat(),
                'conversations': conversations
            }
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Saved {len(self.history)} history items to {history_file}")
            
        except Exception as e:
            logger.error(f"Error saving history to {history_file}: {str(e)}")

    def add_entry(self, role: str, content: str) -> None:
        """
        Add an entry to the conversation history.
        
        Args:
            role: 'User', 'AI', 'System', etc.
            content: The message content
        """
        entry = f"{role}: {content}"
        self.history.append(entry)
        
        # Prevent unbounded memory growth
        if len(self.history) > self.max_items:
            self.history = self.history[-self.max_items:]
            logger.info(f"Trimmed history to {self.max_items} items")
        
        self._save_history()

    def get_history(self, as_string: bool = True) -> Any:
        """
        Get the conversation history.
        
        Args:
            as_string: If True, return as newline-separated string; if False, return list
            
        Returns:
            String or list depending on as_string parameter
        """
        if as_string:
            return "\n".join(self.history)
        return self.history

    def get_recent(self, n: int = 10) -> List[str]:
        """Get the last n items from history."""
        return self.history[-n:] if self.history else []

    def clear_history(self) -> None:
        """Clear all conversation history."""
        self.history = []
        
        if self.enable_persistence:
            history_file = self._get_history_file()
            try:
                if os.path.exists(history_file):
                    os.remove(history_file)
                    logger.info(f"Deleted history file {history_file}")
            except Exception as e:
                logger.error(f"Error deleting history file: {str(e)}")

    def export_history(self, export_path: str) -> bool:
        """
        Export history to a specific file.
        
        Args:
            export_path: Full path where to export the history
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conversations = []
            for entry in self.history:
                if ': ' in entry:
                    role, content = entry.split(': ', 1)
                    conversations.append({
                        'role': role,
                        'content': content,
                    })
            
            data = {
                'session_name': self.session_name,
                'exported_at': datetime.now().isoformat(),
                'conversations': conversations
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully exported history to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting history: {str(e)}")
            return False

    def __len__(self) -> int:
        """Return the number of history items."""
        return len(self.history)

    def __str__(self) -> str:
        """Return history as formatted string."""
        return self.get_history(as_string=True)
