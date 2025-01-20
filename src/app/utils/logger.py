"""
Logging configuration for the application.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

def setup_logger(log_level: int = logging.INFO) -> None:
    """
    Setup application-wide logging configuration.
    
    Args:
        log_level: The logging level to use. Defaults to INFO.
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Setup file handler with rotation
    file_handler = RotatingFileHandler(
        filename=log_dir / "ssh_copilot.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(log_level)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    
    # Add handlers to root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log startup message
    logger.info("Starting SecureSSH+Copilot application") 