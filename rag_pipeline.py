import networkx as nx
import logging

import config
from vector_store import VectorDB

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        try:
            self.db = VectorDB()
            self.kg = nx.Graph()
            self._build_initial_kg()
            logger.info("RAGPipeline initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAGPipeline: {str(e)}", exc_info=True)
            raise

    def _build_initial_kg(self):
        """Build initial knowledge graph from config."""
        try:
            for source, target, relation in config.KNOWLEDGE_GRAPH_EDGES:
                self.kg.add_edge(source, target, relation=relation)
            logger.debug(f"Built knowledge graph with {self.kg.number_of_nodes()} nodes")
        except Exception as e:
            logger.error(f"Error building knowledge graph: {str(e)}", exc_info=True)

    def get_kg_context(self, text):
        """Extract knowledge graph context relevant to the text."""
        try:
            if not text or not isinstance(text, str):
                return ""
            
            context = []
            text_lower = text.lower()

            for node in self.kg.nodes():
                if node.lower() in text_lower:
                    neighbors = self.kg[node]
                    for neighbor, attr in neighbors.items():
                        relation = attr.get('relation', 'related to')
                        context.append(f"{node} is {relation} {neighbor}")
            
            result = "; ".join(context)
            logger.debug(f"Generated KG context: {len(result)} chars")
            return result
            
        except Exception as e:
            logger.error(f"Error getting KG context: {str(e)}", exc_info=True)
            return ""

    def check_calendar(self, text):
        """Check for calendar conflicts or relevant events."""
        try:
            if not text or not isinstance(text, str):
                return "No calendar conflicts detected."
            
            notes = []
            for date, event in config.CALENDAR_EVENTS.items():
                if date in text:
                    notes.append(f"NOTE: '{event}' scheduled for {date}")
            
            result = " | ".join(notes) if notes else "No calendar conflicts detected."
            logger.debug(f"Calendar check result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking calendar: {str(e)}", exc_info=True)
            return "Error checking calendar."

    def retrieve_context(self, query):
        """
        Retrieve all contextual information for the query.
        
        Returns:
            Tuple of (rag_docs, kg_info, calendar_info)
        """
        try:
            if not query or not isinstance(query, str):
                logger.warning("Invalid query provided to retrieve_context")
                return [], "", ""
            
            rag_docs = self.db.search(query) or []
            kg_info = self.get_kg_context(query)
            calendar_info = self.check_calendar(query)
            
            logger.debug(f"Retrieved context: {len(rag_docs)} docs, KG info, calendar info")
            return rag_docs, kg_info, calendar_info
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}", exc_info=True)
            return [], "", ""
