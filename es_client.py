"""
Elasticsearch client for executing ESQL queries
"""
from elasticsearch import Elasticsearch
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElasticsearchClient:
    """Wrapper for Elasticsearch operations"""
    
    def __init__(self):
        """Initialize Elasticsearch client"""
        self.client = Elasticsearch(
            [Config.ES_HOST],
            basic_auth=(Config.ES_USERNAME, Config.ES_PASSWORD),
            request_timeout=Config.ES_TIMEOUT,
            max_retries=Config.ES_MAX_RETRIES,
            retry_on_timeout=True,
            verify_certs=False,
            ssl_show_warn=False
        )
        
    def ping(self):
        """Test Elasticsearch connection"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Failed to ping Elasticsearch: {e}")
            return False
    
    def execute_esql(self, query, params=None):
        """
        Execute an ES|QL query
        
        Args:
            query: ES|QL query string
            params: Optional query parameters (list format for ES|QL)
            
        Returns:
            Query results or None if error
        """
        try:
            logger.info(f"Executing ES|QL query: {query[:100]}...")
            
            # Use the ES|QL API - params should be a list, not dict
            # If params is None or empty dict, use empty list
            query_params = params if params and isinstance(params, list) else []
            
            response = self.client.esql.query(
                query=query,
                params=query_params
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing ES|QL query: {e}")
            logger.error(f"Query: {query}")
            return None
    
    def get_index_info(self, index_pattern):
        """Get information about indices matching a pattern"""
        try:
            return self.client.indices.get(index=index_pattern)
        except Exception as e:
            logger.error(f"Error getting index info for {index_pattern}: {e}")
            return None
    
    def count_documents(self, index_pattern):
        """Count documents in indices matching a pattern"""
        try:
            response = self.client.count(index=index_pattern)
            return response.get('count', 0)
        except Exception as e:
            logger.error(f"Error counting documents in {index_pattern}: {e}")
            return 0
