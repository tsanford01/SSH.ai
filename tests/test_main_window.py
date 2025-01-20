"""
Tests for main window functionality.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.app.main_window import MainWindow
from src.app.core.ssh_connection import SSHCredentials

# Required for Qt widgets
app = QApplication([])

@pytest.fixture
def window():
    """Create main window for testing."""
    return MainWindow()

def test_window_creation(window):
    """Test window initialization."""
    assert window.connection_sidebar is not None
    assert window.terminal_tabs is not None
    assert window.llm_panel is not None
    assert window.status_bar is not None

def test_new_connection_success(window, monkeypatch):
    """Test successful new connection creation."""
    # Mock ConnectionDialog
    mock_dialog = Mock()
    mock_dialog.exec.return_value = True
    mock_dialog.get_credentials.return_value = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host",
        port=22
    )
    monkeypatch.setattr(
        "src.app.ui.connection_dialog.ConnectionDialog",
        lambda *args: mock_dialog
    )
    
    # Mock terminal creation
    mock_terminal = Mock()
    window.terminal_tabs.add_terminal = Mock()
    
    # Test new connection
    window._new_connection()
    
    # Verify dialog was shown and terminal was created
    mock_dialog.exec.assert_called_once()
    window.terminal_tabs.add_terminal.assert_called_once()
    assert "test.host" in window.connection_sidebar.connection_tree.findItems(
        "test.host",
        Qt.MatchFlag.MatchExactly
    )[0].text(0)

def test_new_connection_failure(window, monkeypatch):
    """Test failed new connection creation."""
    # Mock ConnectionDialog
    mock_dialog = Mock()
    mock_dialog.exec.return_value = True
    mock_dialog.get_credentials.return_value = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="invalid.host",
        port=22
    )
    monkeypatch.setattr(
        "src.app.ui.connection_dialog.ConnectionDialog",
        lambda *args: mock_dialog
    )
    
    # Mock terminal creation to raise exception
    window.terminal_tabs.add_terminal = Mock(
        side_effect=Exception("Connection failed")
    )
    
    # Mock QMessageBox
    mock_message = Mock()
    monkeypatch.setattr(QMessageBox, "critical", mock_message)
    
    # Test new connection
    window._new_connection()
    
    # Verify error was shown
    mock_message.assert_called_once()
    assert "Connection failed" in mock_message.call_args[0][2]

def test_command_handling(window):
    """Test command execution handling."""
    # Setup spy for LLM panel
    window.llm_panel.add_suggestion = Mock()
    
    # Simulate command execution
    window._handle_command("test.host", "ls -la", "file1 file2")
    
    # Verify LLM panel was updated
    window.llm_panel.add_suggestion.assert_called_once()

def test_panel_toggling(window):
    """Test sidebar and LLM panel toggling."""
    # Test sidebar toggle
    assert window.connection_sidebar.isVisible()
    window._toggle_sidebar()
    assert not window.connection_sidebar.isVisible()
    window._toggle_sidebar()
    assert window.connection_sidebar.isVisible()
    
    # Test LLM panel toggle
    assert window.llm_panel.isVisible()
    window._toggle_llm_panel()
    assert not window.llm_panel.isVisible()
    window._toggle_llm_panel()
    assert window.llm_panel.isVisible()

def test_status_bar_updates(window):
    """Test status bar updates."""
    # Mock status bar
    window.status_bar.update_connection_status = Mock()
    
    # Create new connection
    mock_dialog = Mock()
    mock_dialog.exec.return_value = True
    mock_dialog.get_credentials.return_value = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host",
        port=22
    )
    
    with patch(
        "src.app.ui.connection_dialog.ConnectionDialog",
        return_value=mock_dialog
    ):
        window._new_connection()
    
    # Verify status bar was updated
    window.status_bar.update_connection_status.assert_called_with(
        "Connected",
        "test.host"
    ) 