"""
Configuration settings for the SIEM Dashboard
"""
import os

class Config:
    """Application configuration"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 1212
    
    # Elasticsearch configuration
    ES_HOST = ''
    ES_USERNAME = ''
    ES_PASSWORD = ''
    ES_TIMEOUT = 30
    ES_MAX_RETRIES = 3
    
    # Rules configuration
    RULES_DIRECTORY = 'rules'
    RULE_EXECUTION_TIMEOUT = 60  # seconds
    
    # Dashboard configuration
    AUTO_REFRESH_INTERVAL = 30000  # milliseconds (30 seconds)
    ALERTS_PER_PAGE = 20
    MAX_ALERTS_STORED = 1000
    
    # Chart configuration
    TIMELINE_BUCKETS = 24  # Number of time buckets for timeline chart
    TOP_ITEMS_LIMIT = 10   # Number of items for top charts
