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

def main() -> None:
    """Initialize and run the main application."""
    # Setup logging
    setup_logger()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for consistent cross-platform look
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

async def main():
    # Initialize LLM Manager
    llm = LLMManager()
    
    # Start the LLM server
    print("Starting LLM server...")
    if llm.start_server():
        print("Server started successfully!")
        
        # Wait for server to initialize
        print("Waiting for server to initialize...")
        await asyncio.sleep(15)  # Increased wait time
        
        # Test connection before sending query
        max_retries = 3
        for attempt in range(max_retries):
            print(f"\nTesting connection (attempt {attempt + 1})...")
            if await llm.test_connection():
                print("\nConnection successful! Testing LLM with a sample query...")
                response = await llm.get_command_suggestion("I want to list all files in the current directory")
                print(f"\nLLM Response: {response}")
                break
            else:
                if attempt < max_retries - 1:
                    print(f"Connection attempt {attempt + 1} failed, retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    print("Failed to connect to LLM server after multiple attempts")
        
        # Cleanup
        llm.stop_server()
    else:
        print("Failed to start LLM server!")

if __name__ == "__main__":
    asyncio.run(main()) 