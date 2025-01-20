#!/usr/bin/env python3
"""
SecureSSH+Copilot - Main Application Entry Point
"""

import sys
from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

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

if __name__ == "__main__":
    main() 