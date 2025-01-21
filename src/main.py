#!/usr/bin/env python3
"""
SecureSSH+Copilot - Main Application Entry Point
"""

import sys
import logging
from typing import Optional
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
import asyncio
import time
from app.core.llm_manager import LLMManager

from app.main_window import MainWindow
from app.utils.logger import setup_logger

async def init_llm_server() -> Optional[LLMManager]:
    """Initialize the LLM server and ensure it's ready."""
    try:
        # Initialize LLM Manager
        llm = LLMManager()
        
        # Start the LLM server
        logging.info("Starting LLM server...")
        if not llm.start_server():
            logging.error("Failed to start LLM server")
            return None
            
        logging.info("Server started successfully!")
        
        # Wait for server to initialize
        logging.info("Waiting for server to initialize...")
        await asyncio.sleep(15)  # Increased wait time
        
        # Test connection before proceeding
        max_retries = 3
        for attempt in range(max_retries):
            logging.info(f"Testing connection (attempt {attempt + 1})...")
            if await llm.test_connection():
                logging.info("Connection successful!")
                return llm
            else:
                if attempt < max_retries - 1:
                    logging.warning(f"Connection attempt {attempt + 1} failed, retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    logging.error("Failed to connect to LLM server after multiple attempts")
                    return None
    except Exception as e:
        logging.error(f"Error initializing LLM server: {e}")
        return None

async def main() -> None:
    """Initialize and run the main application."""
    try:
        # Setup logging
        setup_logger()
        logging.info("Starting SecureSSH+Copilot application")
        
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Initialize LLM server first
        logging.info("Initializing LLM server...")
        llm = await init_llm_server()
        if not llm:
            logging.warning("Failed to initialize LLM server. Some features may be limited.")
            QMessageBox.warning(
                None,
                "LLM Initialization Warning",
                "Failed to initialize LLM server. Some features may be limited."
            )
        else:
            logging.info("LLM server initialized successfully.")
        
        # Initialize and show the main window
        try:
            logging.info("Creating main window...")
            main_window = MainWindow(llm_manager=llm)
            logging.info("Showing main window...")
            main_window.show()
            logging.info("MainWindow initialized and shown successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize MainWindow: {e}")
            QMessageBox.critical(
                None,
                "Initialization Error",
                f"Failed to initialize application window: {e}"
            )
            sys.exit(1)
        
        # Execute the application
        logging.info("Starting Qt event loop...")
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"Critical error during startup: {e}")
        QMessageBox.critical(
            None,
            "Critical Error",
            f"A critical error occurred during startup: {e}"
        )
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 