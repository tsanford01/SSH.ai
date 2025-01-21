"""
Suggestion panel for displaying LLM responses and recommendations.
"""

from typing import Optional, List, Dict
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QListWidget,
    QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor
from PyQt6.QtWidgets import QApplication
from ..core.llm_manager import LLMManager

class SuggestionPanel(QWidget):
    """Panel for displaying LLM suggestions."""
    
    # Signal emitted when a suggested command should be executed
    execute_command = pyqtSignal(str)
    
    def __init__(self, llm_manager: LLMManager, parent: Optional[QWidget] = None) -> None:
        """
        Initialize suggestion panel.

        Args:
            llm_manager: LLM manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.llm = llm_manager
        
        # Set up the UI
        self._init_ui()
        
        # Track current suggestions
        self._current_suggestions: List[Dict[str, str]] = []
    
    async def analyze_command(self, command: str, output: str) -> None:
        """
        Analyze a command and its output to generate suggestions.
        
        Args:
            command: The command that was executed
            output: The command's output
        """
        try:
            # Get suggestions from LLM
            suggestions = await self.llm.get_intelligent_suggestions(
                partial_command=command,
                working_dir=None  # TODO: Get working directory
            )
            
            # Update UI with suggestions
            self.set_suggestions(suggestions)
        except Exception as e:
            print(f"Error analyzing command: {e}")
            self.clear()
    
    async def analyze_error(self, error: str) -> None:
        """
        Analyze an error message to generate helpful suggestions.
        
        Args:
            error: The error message to analyze
        """
        try:
            # Get suggestions from LLM
            suggestions = await self.llm.get_intelligent_suggestions(
                partial_command=None,
                working_dir=None,  # TODO: Get working directory
                environment={"error": error}
            )
            
            # Update UI with suggestions
            self.set_suggestions(suggestions)
        except Exception as e:
            print(f"Error analyzing error: {e}")
            self.clear()
    
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QWidget()
        header.setObjectName("suggestionHeader")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("Command Suggestions")
        title.setObjectName("suggestionTitle")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.setToolTip("Refresh suggestions")
        refresh_btn.clicked.connect(self._refresh_suggestions)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        
        # Suggestions list
        self._suggestions_list = QListWidget()
        self._suggestions_list.setObjectName("suggestionsList")
        self._suggestions_list.setFont(QFont("Segoe UI", 10))
        self._suggestions_list.itemClicked.connect(self._suggestion_selected)
        self._suggestions_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e5f3ff;
                color: black;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        
        # Action buttons
        actions = QWidget()
        actions.setObjectName("suggestionActions")
        actions_layout = QHBoxLayout(actions)
        
        self._execute_btn = QPushButton("Execute")
        self._execute_btn.setObjectName("executeButton")
        self._execute_btn.clicked.connect(self._execute_suggestion)
        self._execute_btn.setEnabled(False)
        
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("copyButton")
        copy_btn.clicked.connect(self._copy_suggestion)
        copy_btn.setEnabled(False)
        self._copy_btn = copy_btn
        
        actions_layout.addWidget(self._execute_btn)
        actions_layout.addWidget(copy_btn)
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(self._suggestions_list)
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
    
    def set_suggestions(self, suggestions: List[Dict[str, str]]) -> None:
        """
        Set the suggestions to display.
        
        Args:
            suggestions: List of suggestions, each containing:
                command: The suggested command
                description: Why this command is suggested
                confidence: Confidence score (0-1)
        """
        self._current_suggestions = suggestions
        self._suggestions_list.clear()
        
        for suggestion in suggestions:
            item = QListWidgetItem()
            item.setText(
                f"{suggestion['command']}\n"
                f"{suggestion['description']}"
            )
            
            # Set background color based on confidence
            confidence = float(suggestion['confidence'])
            if confidence >= 0.8:
                item.setBackground(QColor("#e3f2fd"))  # Light blue
            elif confidence >= 0.6:
                item.setBackground(QColor("#f1f8e9"))  # Light green
            else:
                item.setBackground(QColor("#fff3e0"))  # Light orange
            
            self._suggestions_list.addItem(item)
        
        # Enable/disable buttons
        has_suggestions = len(suggestions) > 0
        self._execute_btn.setEnabled(has_suggestions)
        self._copy_btn.setEnabled(has_suggestions)
        
        if has_suggestions:
            self._suggestions_list.setCurrentRow(0)
    
    def clear(self) -> None:
        """Clear the current suggestions."""
        self._current_suggestions = []
        self._suggestions_list.clear()
        self._execute_btn.setEnabled(False)
        self._copy_btn.setEnabled(False)
    
    def _suggestion_selected(self, item: QListWidgetItem) -> None:
        """Handle suggestion selection."""
        index = self._suggestions_list.row(item)
        if 0 <= index < len(self._current_suggestions):
            suggestion = self._current_suggestions[index]
            self._execute_btn.setEnabled(True)
            self._copy_btn.setEnabled(True)
    
    def _refresh_suggestions(self) -> None:
        """Request a refresh of the current suggestions."""
        # This will be connected to the LLM manager
        pass
    
    def _execute_suggestion(self) -> None:
        """Execute the selected command."""
        current_row = self._suggestions_list.currentRow()
        if 0 <= current_row < len(self._current_suggestions):
            suggestion = self._current_suggestions[current_row]
            self.execute_command.emit(suggestion['command'])
    
    def _copy_suggestion(self) -> None:
        """Copy selected suggestion to clipboard."""
        current_row = self._suggestions_list.currentRow()
        if 0 <= current_row < len(self._current_suggestions):
            suggestion = self._current_suggestions[current_row]
            self._suggestions_list.setFocus()
            self._suggestions_list.currentItem().setSelected(True)
            clipboard = QApplication.clipboard()
            clipboard.setText(suggestion['command']) 