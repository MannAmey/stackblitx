import os
import sys
import logging
from pathlib import Path
import structlog
from structlog.stdlib import LoggerFactory
import colorama

# Initialize colorama for Windows
colorama.init()

def setup_logging():
    """Setup structured logging with structlog"""
    
    # Create logs directory
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if os.getenv('FLASK_ENV') == 'development' else logging.WARNING,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer(colors=True) if os.getenv('FLASK_ENV') == 'development' else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # File logging
    file_handler = logging.FileHandler(log_dir / 'rfid-server.log')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Error file logging
    error_handler = logging.FileHandler(log_dir / 'error.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Add handlers to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    return structlog.get_logger()

# Custom logging methods for specific scenarios
def log_rfid_event(event, details=None):
    """Log RFID-specific events"""
    logger = structlog.get_logger()
    logger.info("RFID Event", event=event, details=details or {}, type="RFID_EVENT")

def log_user_action(action, user_id, details=None):
    """Log user actions"""
    logger = structlog.get_logger()
    logger.info("User Action", action=action, user_id=user_id, details=details or {}, type="USER_ACTION")

def log_system_event(event, details=None):
    """Log system events"""
    logger = structlog.get_logger()
    logger.info("System Event", event=event, details=details or {}, type="SYSTEM_EVENT")

def log_purchase_event(event, purchase_data, details=None):
    """Log purchase events"""
    logger = structlog.get_logger()
    logger.info("Purchase Event", event=event, purchase_data=purchase_data, details=details or {}, type="PURCHASE_EVENT")