import os
from mongoengine import connect, disconnect
import structlog

logger = structlog.get_logger()

def init_db(mongodb_uri=None):
    """Initialize MongoDB connection using MongoEngine"""
    if mongodb_uri is None:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/rfid_system')
    
    try:
        # Disconnect any existing connections
        disconnect()
        
        # Connect to MongoDB
        connect(host=mongodb_uri)
        
        logger.info("✅ MongoDB connected successfully", uri=mongodb_uri)
        return True
    except Exception as e:
        logger.error("❌ MongoDB connection failed", error=str(e), uri=mongodb_uri)
        raise e

def close_db():
    """Close MongoDB connection"""
    try:
        disconnect()
        logger.info("✅ MongoDB connection closed")
    except Exception as e:
        logger.error("❌ Error closing MongoDB connection", error=str(e))