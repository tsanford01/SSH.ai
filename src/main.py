#!/usr/bin/env python3
"""
SecureSSH+Copilot - Main Application Entry Point
"""

import sys
from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import asyncio
import time
from app.core.llm_manager import LLMManager

from app.main_window import MainWindow
from app.utils.logger import setup_logger

async def main() -> None:
    """Initialize and run the main application."""
    # Setup logging
    setup_logger()
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Initialize and show the main window
    main_window = MainWindow()
    main_window.show()
    
    # Start the LLM server in the background
    asyncio.create_task(start_llm_server())
    
    # Execute the application
    sys.exit(app.exec())

async def start_llm_server() -> None:
    """Start the LLM server and test the connection."""
    # Initialize LLM Manager
    llm = LLMManager()
    
    # Start the LLM server
    print("Starting LLM server...")
    if llm.start_server():
        print("Server started successfully!")
        
        # Wait for server to initialize
        print("Waiting for server to initialize...")
        await asyncio.sleep(15)  # Increased wait time
        
        # Test connection before proceeding
        max_retries = 3
        for attempt in range(max_retries):
            print(f"\nTesting connection (attempt {attempt + 1})...")
            if await llm.test_connection():
                print("\nConnection successful!")
                break
            else:
                if attempt < max_retries - 1:
                    print(f"Connection attempt {attempt + 1} failed, retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    print("Failed to connect to LLM server after multiple attempts")

if __name__ == "__main__":
    asyncio.run(main()) 