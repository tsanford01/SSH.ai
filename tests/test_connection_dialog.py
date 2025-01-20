"""
Tests for SSH connection dialog.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication, QDialogButtonBox
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.app.ui.connection_dialog import ConnectionDialog
from src.app.core.ssh_connection import SSHCredentials

# Required for Qt widgets
app = QApplication([])

@pytest.fixture
def dialog():
    """Create connection dialog for testing."""
    return ConnectionDialog()

def test_dialog_creation(dialog):
    """Test dialog initialization."""
    assert dialog.hostname_edit is not None
    assert dialog.port_edit is not None
    assert dialog.username_edit is not None
    assert dialog.password_edit is not None
    assert dialog.key_file_edit is not None

def test_dialog_default_values(dialog):
    """Test default field values."""
    assert dialog.port_edit.text() == "22"
    assert dialog.hostname_edit.text() == ""
    assert dialog.username_edit.text() == ""
    assert dialog.password_edit.text() == ""
    assert dialog.key_file_edit.text() == ""

def test_dialog_validation(dialog):
    """Test input validation."""
    # Test empty fields
    assert not dialog._validate_input()
    
    # Test invalid port
    dialog.hostname_edit.setText("localhost")
    dialog.username_edit.setText("user")
    dialog.port_edit.setText("invalid")
    assert not dialog._validate_input()
    
    # Test valid input with password
    dialog.port_edit.setText("22")
    dialog.password_edit.setText("pass123")
    assert dialog._validate_input()
    
    # Test valid input with key file
    dialog.password_edit.clear()
    dialog.key_file_edit.setText("/path/to/key.pem")
    assert dialog._validate_input()

def test_dialog_get_credentials(dialog):
    """Test credentials creation."""
    # Set test values
    dialog.hostname_edit.setText("test.host")
    dialog.port_edit.setText("2222")
    dialog.username_edit.setText("testuser")
    dialog.password_edit.setText("testpass")
    
    # Get credentials
    creds = dialog.get_credentials()
    
    assert isinstance(creds, SSHCredentials)
    assert creds.hostname == "test.host"
    assert creds.port == 2222
    assert creds.username == "testuser"
    assert creds.get_password() == "testpass"
    assert creds.key_filename is None

@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
def test_dialog_key_file_selection(mock_file_dialog, dialog):
    """Test SSH key file selection."""
    # Setup mock
    mock_file_dialog.return_value = ("/path/to/key.pem", "")
    
    # Click browse button
    dialog._browse_key_file()
    
    # Verify file was selected
    assert dialog.key_file_edit.text() == "/path/to/key.pem"

def test_dialog_accept_reject(dialog):
    """Test dialog accept/reject functionality."""
    # Setup signal spies
    accepted_spy = Mock()
    rejected_spy = Mock()
    dialog.accepted.connect(accepted_spy)
    dialog.rejected.connect(rejected_spy)
    
    # Test reject
    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).click()
    rejected_spy.assert_called_once()
    
    # Test accept with invalid input
    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok).click()
    assert not accepted_spy.called
    
    # Test accept with valid input
    dialog.hostname_edit.setText("localhost")
    dialog.username_edit.setText("user")
    dialog.password_edit.setText("pass")
    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok).click()
    accepted_spy.assert_called_once() 