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
    QScrollBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.app.ui.suggestion_panel import SuggestionPanel

# Required for Qt widgets
app = QApplication([])

@pytest.fixture
def panel():
    """Create suggestion panel for testing."""
    return SuggestionPanel()

def test_initial_state(panel):
    """Test initial panel state."""
    assert panel._current_suggestion is None
    assert not panel._execute_btn.isEnabled()
    assert panel._content.toPlainText() == ""

def test_set_suggestion(panel):
    """Test setting suggestion text."""
    test_text = "Test suggestion"
    panel.set_suggestion(test_text)
    
    assert panel._current_suggestion == test_text
    assert panel._content.toPlainText() == test_text
    assert not panel._execute_btn.isEnabled()

def test_set_suggestion_with_command(panel):
    """Test setting suggestion with command."""
    test_text = "Test suggestion with command"
    panel.set_suggestion(test_text, has_command=True)
    
    assert panel._current_suggestion == test_text
    assert panel._content.toPlainText() == test_text
    assert panel._execute_btn.isEnabled()

def test_clear_suggestion(panel):
    """Test clearing suggestion."""
    # Set initial suggestion
    panel.set_suggestion("Test suggestion", has_command=True)
    
    # Clear it
    panel.clear()
    
    assert panel._current_suggestion is None
    assert panel._content.toPlainText() == ""
    assert not panel._execute_btn.isEnabled()

def test_execute_command_signal(panel):
    """Test execute command signal emission."""
    test_text = "Test command"
    received_commands = []
    
    # Connect to signal
    panel.execute_command.connect(lambda cmd: received_commands.append(cmd))
    
    # Set suggestion and click execute
    panel.set_suggestion(test_text, has_command=True)
    panel._execute_btn.click()
    
    assert len(received_commands) == 1
    assert received_commands[0] == test_text

def test_copy_suggestion(panel, monkeypatch):
    """Test copying suggestion to clipboard."""
    test_text = "Test suggestion"
    clipboard_text = None
    
    # Mock clipboard operations
    def mock_copy():
        nonlocal clipboard_text
        clipboard_text = panel._content.textCursor().selectedText()
    
    monkeypatch.setattr(panel._content, "copy", mock_copy)
    
    # Set suggestion and copy
    panel.set_suggestion(test_text)
    panel._copy_suggestion()
    
    assert clipboard_text == test_text

def test_refresh_button(panel):
    """Test refresh button click."""
    # For now, just verify it doesn't crash
    refresh_btn = panel.findChild(QPushButton, "refreshButton")
    assert refresh_btn is not None
    QTest.mouseClick(refresh_btn, Qt.MouseButton.LeftButton)

def test_widget_styling(panel):
    """Test widget styling and appearance."""
    # Verify object names are set
    assert panel.findChild(QWidget, "suggestionHeader") is not None
    assert panel.findChild(QLabel, "suggestionTitle") is not None
    assert panel.findChild(QPushButton, "refreshButton") is not None
    assert panel.findChild(QTextEdit, "suggestionContent") is not None
    assert panel.findChild(QWidget, "suggestionActions") is not None
    assert panel.findChild(QPushButton, "executeButton") is not None
    assert panel.findChild(QPushButton, "copyButton") is not None
    
    # Verify style sheet is applied
    style = panel.styleSheet()
    assert "#suggestionHeader" in style
    assert "#suggestionContent" in style
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