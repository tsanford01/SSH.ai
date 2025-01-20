"""
Tests for terminal widget functionality.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from src.app.ui.terminal_widget import TerminalWidget, TerminalDisplay
from src.app.core.ssh_connection import SSHCredentials

# Required for Qt widgets
app = QApplication([])

@pytest.fixture
def credentials():
    """Create test credentials."""
    return SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="localhost",
        port=22
    )

@pytest.fixture
def mock_ssh_connection():
    """Create mock SSH connection."""
    with patch('src.app.core.ssh_connection.SSHConnection') as mock:
        yield mock

def test_terminal_widget_creation(credentials, mock_ssh_connection):
    """Test terminal widget initialization."""
    widget = TerminalWidget(credentials)
    assert widget.credentials == credentials
    assert widget.ssh is not None
    assert isinstance(widget.display, TerminalDisplay)

def test_terminal_widget_command_execution(credentials, mock_ssh_connection):
    """Test command execution in terminal widget."""
    # Setup mock
    mock_instance = Mock()
    mock_instance.execute_command.return_value = (0, "test output", "")
    mock_ssh_connection.return_value = mock_instance
    
    # Create widget
    widget = TerminalWidget(credentials)
    
    # Setup signal spy
    command_spy = Mock()
    widget.command_executed.connect(command_spy)
    
    # Simulate command execution
    widget._handle_command("ls -la")
    
    # Verify command was executed
    mock_instance.execute_command.assert_called_once_with("ls -la")
    command_spy.assert_called_once_with("ls -la", "test output")

def test_terminal_display_key_events(credentials):
    """Test key event handling in terminal display."""
    display = TerminalDisplay()
    
    # Test character input
    QTest.keyClicks(display, "ls -la")
    assert display.current_command == "ls -la"
    
    # Test enter key
    command_spy = Mock()
    display.command_entered.connect(command_spy)
    QTest.keyClick(display, Qt.Key.Key_Return)
    command_spy.assert_called_once_with("ls -la")
    assert display.current_command == ""
    
    # Test command history
    QTest.keyClicks(display, "pwd")
    QTest.keyClick(display, Qt.Key.Key_Return)
    assert len(display.command_history) == 2
    assert display.command_history == ["ls -la", "pwd"]
    
    # Test up arrow (command history navigation)
    QTest.keyClick(display, Qt.Key.Key_Up)
    assert display.current_command == "pwd"
    QTest.keyClick(display, Qt.Key.Key_Up)
    assert display.current_command == "ls -la"

def test_terminal_display_output(credentials):
    """Test terminal display output handling."""
    display = TerminalDisplay()
    
    # Test normal output
    display.append_output("test output\n")
    assert "test output" in display.toPlainText()
    
    # Test error output
    display.append_output("error message\n", error=True)
    assert "error message" in display.toPlainText()

def test_terminal_widget_connection_close(credentials, mock_ssh_connection):
    """Test terminal connection closing."""
    # Setup mock
    mock_instance = Mock()
    mock_ssh_connection.return_value = mock_instance
    
    # Create widget
    widget = TerminalWidget(credentials)
    
    # Setup signal spy
    close_spy = Mock()
    widget.connection_closed.connect(close_spy)
    
    # Close connection
    widget.close_connection()
    
    # Verify connection was closed
    mock_instance.close.assert_called_once()
    close_spy.assert_called_once() 