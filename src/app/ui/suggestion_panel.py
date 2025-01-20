"""
Suggestion panel for displaying LLM responses and recommendations.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QScrollArea,
    QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

class SuggestionPanel(QWidget):
    """Panel for displaying LLM suggestions and analysis."""
    
    # Signal emitted when a suggested command should be executed
    execute_command = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize suggestion panel."""
        super().__init__(parent)
        
        # Set up the UI
        self._init_ui()
        
        # Track current suggestion
        self._current_suggestion: Optional[str] = None
    
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QWidget()
        header.setObjectName("suggestionHeader")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("AI Assistant")
        title.setObjectName("suggestionTitle")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.setToolTip("Refresh analysis")
        refresh_btn.clicked.connect(self._refresh_analysis)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        
        # Content area
        content_area = QScrollArea()
        content_area.setWidgetResizable(True)
        content_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self._content = QTextEdit()
        self._content.setReadOnly(True)
        self._content.setObjectName("suggestionContent")
        self._content.setFont(QFont("Segoe UI", 10))
        self._content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        content_area.setWidget(self._content)
        
        # Action buttons
        actions = QWidget()
        actions.setObjectName("suggestionActions")
        actions_layout = QHBoxLayout(actions)
        
        self._execute_btn = QPushButton("Execute Suggestion")
        self._execute_btn.setObjectName("executeButton")
        self._execute_btn.clicked.connect(self._execute_suggestion)
        self._execute_btn.setEnabled(False)
        
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("copyButton")
        copy_btn.clicked.connect(self._copy_suggestion)
        
        actions_layout.addWidget(self._execute_btn)
        actions_layout.addWidget(copy_btn)
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(content_area)
        layout.addWidget(actions)
        
        # Apply styles
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
            #suggestionHeader {
                background-color: #e0e0e0;
                border-bottom: 1px solid #ccc;
                padding: 8px;
            }
            #suggestionTitle {
                color: #333;
            }
            #refreshButton {
                background: transparent;
                border: none;
                padding: 4px 8px;
                font-size: 14px;
            }
            #refreshButton:hover {
                background-color: #d0d0d0;
                border-radius: 4px;
            }
            #suggestionContent {
                background-color: white;
                border: none;
                padding: 12px;
            }
            #suggestionActions {
                background-color: #e0e0e0;
                border-top: 1px solid #ccc;
                padding: 8px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #006cbd;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
            #copyButton {
                background-color: #5c5c5c;
            }
            #copyButton:hover {
                background-color: #4c4c4c;
            }
        """)
    
    def set_suggestion(self, text: str, has_command: bool = False) -> None:
        """
        Set the suggestion text.
        
        Args:
            text: Suggestion text to display
            has_command: Whether the suggestion includes an executable command
        """
        self._current_suggestion = text
        self._content.setText(text)
        self._execute_btn.setEnabled(has_command)
        
        # Scroll to top
        cursor = self._content.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self._content.setTextCursor(cursor)
    
    def clear(self) -> None:
        """Clear the current suggestion."""
        self._current_suggestion = None
        self._content.clear()
        self._execute_btn.setEnabled(False)
    
    def _refresh_analysis(self) -> None:
        """Request a refresh of the current analysis."""
        # This will be connected to the LLM manager
        pass
    
    def _execute_suggestion(self) -> None:
        """Execute the suggested command."""
        if self._current_suggestion:
            # Extract command from suggestion
            # For now, just emit the whole suggestion
            self.execute_command.emit(self._current_suggestion)
    
    def _copy_suggestion(self) -> None:
        """Copy suggestion to clipboard."""
        if self._current_suggestion:
            self._content.selectAll()
            self._content.copy()
            # Deselect
            cursor = self._content.textCursor()
            cursor.clearSelection()
            self._content.setTextCursor(cursor) 