"""
Logging configuration for ARA v2.
Implements structured JSON logging for easy parsing and analysis.
"""

import logging
import json
import os
from logging.handlers import RotatingFileHandler
from flask import has_request_context, g, request


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing."""

    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        # Add request context if available
        if has_request_context():
            log_obj['request'] = {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
            }
            if hasattr(g, 'request_id'):
                log_obj['request_id'] = g.request_id

        # Add custom attributes
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id

        if hasattr(record, 'paper_id'):
            log_obj['paper_id'] = record.paper_id

        return json.dumps(log_obj)


def configure_logging(app):
    """
    Configure application logging.

    Args:
        app: Flask application instance
    """

    # Remove default handlers
    app.logger.handlers.clear()

    # Set log level
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    app.logger.setLevel(log_level)

    # Create logs directory if it doesn't exist
    log_file = app.config.get('LOG_FILE', 'logs/ara_v2.log')
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Console handler (for development)
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(
            logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
        )
        app.logger.addHandler(console_handler)
    else:
        # JSON formatted console logs in production
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(JSONFormatter())
        app.logger.addHandler(console_handler)

    # File handler (production)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(JSONFormatter())
        app.logger.addHandler(file_handler)

    # Error file handler (errors only)
    error_log_file = log_file.replace('.log', '_errors.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10485760,
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    app.logger.addHandler(error_handler)

    app.logger.info("Logging configured successfully")
