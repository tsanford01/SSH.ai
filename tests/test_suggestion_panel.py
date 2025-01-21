"""
Tests for suggestion panel functionality.
"""

import pytest
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QTextEdit,
    QScrollBar,
    QListWidget,
    QListWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QColor

from src.app.ui.suggestion_panel import SuggestionPanel

# Required for Qt widgets
app = QApplication([])

@pytest.fixture
def panel():
    """Create suggestion panel for testing."""
    return SuggestionPanel()

def test_initial_state(panel):
    """Test initial panel state."""
    assert panel._current_suggestions == []
    assert not panel._execute_btn.isEnabled()
    assert not panel._copy_btn.isEnabled()
    assert panel._suggestions_list.count() == 0

def test_set_suggestions(panel):
    """Test setting suggestions."""
    test_suggestions = [
        {
            "command": "git status",
            "description": "Used 5 times with 100% success rate",
            "confidence": 0.9
        },
        {
            "command": "git add .",
            "description": "Frequently follows your recent commands",
            "confidence": 0.7
        }
    ]
    
    panel.set_suggestions(test_suggestions)
    
    assert panel._current_suggestions == test_suggestions
    assert panel._suggestions_list.count() == 2
    assert panel._execute_btn.isEnabled()
    assert panel._copy_btn.isEnabled()
    
    # Check first item is selected by default
    assert panel._suggestions_list.currentRow() == 0
    
    # Verify item text
    first_item = panel._suggestions_list.item(0)
    assert "git status" in first_item.text()
    assert "Used 5 times" in first_item.text()

def test_suggestion_selection(panel):
    """Test suggestion selection behavior."""
    test_suggestions = [
        {
            "command": "ls -l",
            "description": "List files",
            "confidence": 0.8
        }
    ]
    
    panel.set_suggestions(test_suggestions)
    
    # Click first item
    item = panel._suggestions_list.item(0)
    panel._suggestions_list.setCurrentItem(item)
    panel._suggestion_selected(item)
    
    assert panel._execute_btn.isEnabled()
    assert panel._copy_btn.isEnabled()

def test_clear_suggestions(panel):
    """Test clearing suggestions."""
    # Set initial suggestions
    test_suggestions = [
        {
            "command": "pwd",
            "description": "Show current directory",
            "confidence": 0.8
        }
    ]
    panel.set_suggestions(test_suggestions)
    
    # Clear them
    panel.clear()
    
    assert panel._current_suggestions == []
    assert panel._suggestions_list.count() == 0
    assert not panel._execute_btn.isEnabled()
    assert not panel._copy_btn.isEnabled()

def test_execute_command_signal(panel):
    """Test execute command signal emission."""
    test_suggestions = [
        {
            "command": "test command",
            "description": "Test description",
            "confidence": 0.8
        }
    ]
    received_commands = []
    
    # Connect to signal
    panel.execute_command.connect(lambda cmd: received_commands.append(cmd))
    
    # Set suggestion and click execute
    panel.set_suggestions(test_suggestions)
    panel._execute_suggestion()
    
    assert len(received_commands) == 1
    assert received_commands[0] == "test command"

def test_copy_suggestion(panel, monkeypatch):
    """Test copying suggestion to clipboard."""
    test_suggestions = [
        {
            "command": "test command",
            "description": "Test description",
            "confidence": 0.8
        }
    ]
    clipboard_text = None
    
    # Mock clipboard operations
    def mock_set_text(text):
        nonlocal clipboard_text
        clipboard_text = text
    
    monkeypatch.setattr(QApplication.clipboard(), "setText", mock_set_text)
    
    # Set suggestion and copy
    panel.set_suggestions(test_suggestions)
    panel._copy_suggestion()
    
    assert clipboard_text == "test command"

def test_suggestion_confidence_colors(panel):
    """Test suggestion background colors based on confidence."""
    test_suggestions = [
        {
            "command": "high confidence",
            "description": "Test",
            "confidence": 0.9
        },
        {
            "command": "medium confidence",
            "description": "Test",
            "confidence": 0.7
        },
        {
            "command": "low confidence",
            "description": "Test",
            "confidence": 0.5
        }
    ]
    
    panel.set_suggestions(test_suggestions)
    
    # Check background colors
    high_item = panel._suggestions_list.item(0)
    medium_item = panel._suggestions_list.item(1)
    low_item = panel._suggestions_list.item(2)
    
    assert high_item.background().color().name() == QColor("#e3f2fd").name()
    assert medium_item.background().color().name() == QColor("#f1f8e9").name()
    assert low_item.background().color().name() == QColor("#fff3e0").name()

def test_refresh_button(panel):
    """Test refresh button click."""
    refresh_btn = panel.findChild(QPushButton, "refreshButton")
    assert refresh_btn is not None
    QTest.mouseClick(refresh_btn, Qt.MouseButton.LeftButton)

def test_widget_styling(panel):
    """Test widget styling and appearance."""
    # Verify object names are set
    assert panel.findChild(QWidget, "suggestionHeader") is not None
    assert panel.findChild(QLabel, "suggestionTitle") is not None
    assert panel.findChild(QPushButton, "refreshButton") is not None
    assert panel.findChild(QListWidget, "suggestionsList") is not None
    assert panel.findChild(QWidget, "suggestionActions") is not None
    assert panel.findChild(QPushButton, "executeButton") is not None
    assert panel.findChild(QPushButton, "copyButton") is not None
    
    # Verify style sheet is applied
    style = panel.styleSheet()
    assert "#suggestionHeader" in style
    assert "#suggestionsList" in style
    assert "#suggestionActions" in style
    assert "QPushButton" in style

def test_content_scroll_position(panel):
    """Test content scroll position after setting suggestion."""
    # Create long text that requires scrolling
    long_text = "\n".join(f"Line {i}" for i in range(100))
    
    # Set suggestion
    panel.set_suggestion(long_text)
    
    # Verify scroll position is at top
    assert panel._content.verticalScrollBar().value() == 0 