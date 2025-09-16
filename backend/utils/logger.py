import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(app):
    """Setup application logging."""
    if not app.debug:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Setup file handler with rotation
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'], 
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('Radiological Detection System startup')

def log_system_event(level, message, module=None, user_id=None, session_id=None):
    """Log system events to database."""
    from models.database import SystemLog
    from utils.auth import get_client_ip
    
    try:
        SystemLog.create(
            level=level,
            message=message,
            module=module,
            user_id=user_id,
            session_id=session_id,
            ip_address=get_client_ip()
        )
    except Exception as e:
        # Fallback to application logger if database logging fails
        logging.error(f"Failed to log to database: {str(e)}")

class DatabaseLogHandler(logging.Handler):
    """Custom log handler that writes to database."""
    
    def emit(self, record):
        try:
            log_system_event(
                level=record.levelname,
                message=record.getMessage(),
                module=record.module if hasattr(record, 'module') else None
            )
        except Exception:
            # Prevent logging errors from breaking the application
            pass
