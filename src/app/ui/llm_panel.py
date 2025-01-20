"""
LLM panel UI component.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

class LLMPanel(QWidget):
    """Panel for LLM interaction and command suggestions."""
    
    # Signals
    command_suggested = pyqtSignal(str)  # Emitted when a command is suggested
    
    def __init__(self) -> None:
        """Initialize the LLM panel."""
        super().__init__()
        
        # Set minimum width
        self.setMinimumWidth(250)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Add header
        header = QLabel("AI Assistant")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(header)
        
        # Add chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        # Add input area
        self.input_area = QTextEdit()
        self.input_area.setMaximumHeight(100)
        self.input_area.setPlaceholderText("Ask a question...")
        layout.addWidget(self.input_area)
        
        # Add send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._on_send)
        layout.addWidget(self.send_button)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Add suggestions area
        suggestions_label = QLabel("Command Suggestions")
        suggestions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        suggestions_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(suggestions_label)
        
        self.suggestions_area = QTextEdit()
        self.suggestions_area.setReadOnly(True)
        self.suggestions_area.setMaximumHeight(150)
        layout.addWidget(self.suggestions_area)
    
    def _on_send(self) -> None:
        """Handle send button click."""
        message = self.input_area.toPlainText().strip()
        if message:
            # Add user message to chat history
            self._add_to_chat("You", message)
            self.input_area.clear()
            
            # TODO: Process message with LLM and get response
            self._add_to_chat("Assistant", "This feature is not yet implemented.")
    
    def _add_to_chat(self, sender: str, message: str) -> None:
        """
        Add a message to the chat history.
        
        Args:
            sender: Name of the message sender
            message: The message content
        """
        self.chat_history.append(f"<b>{sender}:</b> {message}")
    
    def add_suggestion(self, command: str, description: str) -> None:
        """
        Add a command suggestion.
        
        Args:
            command: The suggested command
            description: Description or reason for the suggestion
        """
        self.suggestions_area.append(
            f"<b>Suggestion:</b> {command}<br>"
            f"<i>{description}</i><br><br>"
        ) 