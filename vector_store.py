import chromadb
from chromadb.config import Settings
import uuid
import os
import logging

import config

logger = logging.getLogger(__name__)


class VectorDB:
    def __init__(self):
        self.persist_dir = config.VECTOR_DB_PATH
        os.makedirs(self.persist_dir, exist_ok=True)
        
        try:
            self.client = chromadb.Client(
                Settings(persist_directory=self.persist_dir, anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(name=config.VECTOR_COLLECTION_NAME)
            logger.info(f"VectorDB initialized with {self.collection.count()} items")
        except Exception as e:
            logger.error(f"Error initializing VectorDB: {str(e)}", exc_info=True)
            raise

    def add_email(self, email_id, text, metadata):
        """
        Stores email text and metadata into ChromaDB.
        Embeddings are generated automatically.
        
        Args:
            email_id: ID for the email document
            text: Email text content
            metadata: Dictionary of metadata
        """
        try:
            if not text or not isinstance(text, str):
                logger.warning("Invalid text provided to add_email")
                return False
            
            metadata = metadata or {}
            doc_id = str(email_id) if email_id else str(uuid.uuid4())
            
            self.collection.add(documents=[text], metadatas=[metadata], ids=[doc_id])
            logger.debug(f"Added email {doc_id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding email to VectorDB: {str(e)}", exc_info=True)
            return False

    def search(self, query, n_results=None):
        """
        Searches for most similar emails.
        Returns list of email texts.
        
        Args:
            query: Search query text
            n_results: Number of results to return (uses config default if None)
            
        Returns:
            List of matching email texts
        """
        try:
            if not query or not isinstance(query, str):
                logger.warning("Invalid query provided to search")
                return []
            
            if n_results is None:
                n_results = config.RAG_SEARCH_RESULTS
            
            if self.collection.count() == 0:
                logger.debug("Vector store is empty, returning no results")
                return []
            
            results = self.collection.query(query_texts=[query], n_results=n_results)
            
            if not results or "documents" not in results:
                logger.debug(f"No results found for query: {query[:50]}...")
                return []
            
            logger.debug(f"Found {len(results['documents'][0])} results for query")
            return results["documents"][0]
            
        except Exception as e:
            logger.error(f"Error searching VectorDB: {str(e)}", exc_info=True)
            return []
