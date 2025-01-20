"""
Status bar UI component.
"""

from typing import Optional
from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import Qt

class StatusBar(QStatusBar):
    """Application status bar showing connection and system status."""
    
    def __init__(self) -> None:
        """Initialize the status bar."""
        super().__init__()
        
        # Create status labels
        self.connection_status = QLabel("Not Connected")
        self.encryption_status = QLabel("🔒 Encryption: On")
        self.llm_status = QLabel("LLM: Ready")
        self.memory_usage = QLabel("Memory: 0MB")
        
        # Add permanent widgets (right-aligned)
        self.addPermanentWidget(self.memory_usage)
        self.addPermanentWidget(self.llm_status)
        self.addPermanentWidget(self.encryption_status)
        
        # Add connection status (left-aligned)
        self.addWidget(self.connection_status)
    
    def update_connection_status(self, status: str, host: Optional[str] = None) -> None:
        """
        Update the connection status display.
        
        Args:
            status: Status message to display
            host: Optional hostname to include
        """
        if host:
            self.connection_status.setText(f"Connected to {host}")
        else:
            self.connection_status.setText(status)
    
    def update_encryption_status(self, enabled: bool) -> None:
        """
        Update the encryption status indicator.
        
        Args:
            enabled: Whether encryption is enabled
        """
        icon = "🔒" if enabled else "🔓"
        status = "On" if enabled else "Off"
        self.encryption_status.setText(f"{icon} Encryption: {status}")
    
    def update_llm_status(self, status: str) -> None:
        """
        Update the LLM status display.
        
        Args:
            status: Status message to display
        """
        self.llm_status.setText(f"LLM: {status}")
    
    def update_memory_usage(self, usage_mb: int) -> None:
        """
        Update the memory usage display.
        
        Args:
            usage_mb: Memory usage in megabytes
        """
        self.memory_usage.setText(f"Memory: {usage_mb}MB") 