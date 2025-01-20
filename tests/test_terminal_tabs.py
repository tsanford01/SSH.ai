"""
Tests for terminal tabs functionality.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.app.ui.terminal_tabs import TerminalTabs
from src.app.core.session_manager import Session
from src.app.core.ssh_connection import SSHConnection, SSHCredentials

# Required for Qt widgets
app = QApplication([])

@pytest.fixture
def mock_session():
    """Create mock session."""
    mock_conn = Mock(spec=SSHConnection)
    mock_conn.credentials = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host",
        port=22
    )
    mock_conn.is_connected.return_value = True
    return Mock(spec=Session, connection=mock_conn)

@pytest.fixture
def tabs():
    """Create terminal tabs for testing."""
    return TerminalTabs()

def test_tabs_initialization(tabs):
    """Test tabs initialization."""
    # Check tab widget
    assert tabs.tab_widget is not None
    assert tabs.tab_widget.count() == 1  # Welcome tab
    assert tabs.tab_widget.tabText(0) == "Welcome"
    
    # Check welcome message
    welcome = tabs.tab_widget.widget(0)
    assert welcome is not None
    label = welcome.findChild(QLabel)
    assert label is not None
    assert "Welcome to SSH Copilot" in label.text()

def test_add_terminal(tabs, mock_session):
    """Test adding terminal tab."""
    with patch('src.app.ui.terminal_tabs.TerminalWidget') as mock_terminal_cls:
        # Create mock terminal
        mock_terminal = Mock()
        mock_terminal_cls.return_value = mock_terminal
        
        # Add terminal
        tabs.add_terminal(mock_session)
        
        # Check terminal was created
        mock_terminal_cls.assert_called_once_with(mock_session)
        
        # Check tab was added
        assert tabs.tab_widget.count() == 2  # Welcome + terminal
        assert tabs.tab_widget.widget(1) == mock_terminal
        assert tabs.tab_widget.tabText(1) == "testuser@test.host"
        
        # Check terminal was stored
        assert tabs.terminals[1] == mock_terminal
        
        # Check current tab
        assert tabs.tab_widget.currentIndex() == 1

def test_close_terminal_confirmed(tabs, mock_session):
    """Test closing terminal tab with confirmation."""
    with patch('src.app.ui.terminal_tabs.TerminalWidget') as mock_terminal_cls:
        # Create mock terminal
        mock_terminal = Mock()
        mock_terminal.session = mock_session
        mock_terminal_cls.return_value = mock_terminal
        
        # Add terminal
        tabs.add_terminal(mock_session)
        
        # Create signal spy
        spy = QSignalSpy(tabs.session_closed)
        
        # Mock message box
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            # Close terminal
            tabs._close_tab(1)
            
            # Check confirmation was shown
            mock_question.assert_called_once()
            
            # Check terminal was closed
            mock_terminal.close.assert_called_once()
            
            # Check tab was removed
            assert tabs.tab_widget.count() == 1  # Welcome tab
            assert 1 not in tabs.terminals
            
            # Check signal was emitted
            assert len(spy) == 1
            assert spy[0][0] == mock_session

def test_close_terminal_cancelled(tabs, mock_session):
    """Test cancelling terminal tab close."""
    with patch('src.app.ui.terminal_tabs.TerminalWidget') as mock_terminal_cls:
        # Create mock terminal
        mock_terminal = Mock()
        mock_terminal.session = mock_session
        mock_terminal_cls.return_value = mock_terminal
        
        # Add terminal
        tabs.add_terminal(mock_session)
        
        # Create signal spy
        spy = QSignalSpy(tabs.session_closed)
        
        # Mock message box
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.No
            
            # Close terminal
            tabs._close_tab(1)
            
            # Check confirmation was shown
            mock_question.assert_called_once()
            
            # Check terminal was not closed
            mock_terminal.close.assert_not_called()
            
            # Check tab was not removed
            assert tabs.tab_widget.count() == 2
            assert tabs.terminals[1] == mock_terminal
            
            # Check signal was not emitted
            assert len(spy) == 0

def test_close_welcome_tab(tabs):
    """Test closing welcome tab."""
    # Close welcome tab
    tabs._close_tab(0)
    
    # Check tab was removed
    assert tabs.tab_widget.count() == 0

def test_close_terminal_by_session(tabs, mock_session):
    """Test closing terminal by session."""
    with patch('src.app.ui.terminal_tabs.TerminalWidget') as mock_terminal_cls:
        # Create mock terminal
        mock_terminal = Mock()
        mock_terminal.session = mock_session
        mock_terminal_cls.return_value = mock_terminal
        
        # Add terminal
        tabs.add_terminal(mock_session)
        
        # Mock message box
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            # Close terminal
            tabs.close_terminal(mock_session)
            
            # Check terminal was closed
            mock_terminal.close.assert_called_once()
            
            # Check tab was removed
            assert tabs.tab_widget.count() == 1  # Welcome tab
            assert 1 not in tabs.terminals

def test_welcome_tab_restored(tabs, mock_session):
    """Test welcome tab is restored when last terminal is closed."""
    with patch('src.app.ui.terminal_tabs.TerminalWidget') as mock_terminal_cls:
        # Create mock terminal
        mock_terminal = Mock()
        mock_terminal.session = mock_session
        mock_terminal_cls.return_value = mock_terminal
        
        # Add terminal
        tabs.add_terminal(mock_session)
        
        # Mock message box
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            # Close terminal
            tabs._close_tab(1)
            
            # Check welcome tab was restored
            assert tabs.tab_widget.count() == 1
            assert tabs.tab_widget.tabText(0) == "Welcome" 