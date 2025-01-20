"""
Tests for SSH connection functionality.
"""

import pytest
from unittest.mock import Mock, patch
from paramiko import SSHException

from src.app.core.ssh_connection import SSHConnection, SSHCredentials

def test_ssh_credentials_encryption():
    """Test that credentials are properly encrypted and decrypted."""
    creds = SSHCredentials(
        username="testuser",
        password="testpass123",
        hostname="localhost",
        port=22
    )
    
    # Test that password is not stored in plaintext
    assert creds.password != "testpass123"
    assert creds.get_password() == "testpass123"

@pytest.fixture
def mock_ssh_client():
    """Create a mock SSH client for testing."""
    with patch('paramiko.SSHClient') as mock_client:
        client = Mock()
        mock_client.return_value = client
        yield client

def test_ssh_connection_success(mock_ssh_client):
    """Test successful SSH connection."""
    creds = SSHCredentials(
        username="testuser",
        password="testpass123",
        hostname="localhost",
        port=22
    )
    
    connection = SSHConnection()
    connection.connect(creds)
    
    # Verify that connect was called with correct arguments
    mock_ssh_client.connect.assert_called_once_with(
        hostname="localhost",
        port=22,
        username="testuser",
        password="testpass123"
    )
    
    assert connection.is_connected()

def test_ssh_connection_failure(mock_ssh_client):
    """Test SSH connection failure."""
    mock_ssh_client.connect.side_effect = SSHException("Connection failed")
    
    creds = SSHCredentials(
        username="testuser",
        password="testpass123",
        hostname="invalid-host",
        port=22
    )
    
    connection = SSHConnection()
    with pytest.raises(SSHException):
        connection.connect(creds)
    
    assert not connection.is_connected()

def test_ssh_execute_command(mock_ssh_client):
    """Test executing a command over SSH."""
    # Mock the SSH session and channel
    mock_channel = Mock()
    mock_channel.recv_exit_status.return_value = 0
    mock_channel.recv.side_effect = [b"test output", b""]
    mock_channel.recv_stderr.side_effect = [b""]
    
    mock_session = Mock()
    mock_session.get_transport.return_value.open_session.return_value = mock_channel
    mock_ssh_client.get_transport.return_value = mock_session
    
    connection = SSHConnection()
    connection._client = mock_ssh_client  # Set mock client
    
    exit_code, output, error = connection.execute_command("ls -la")
    
    assert exit_code == 0
    assert output == "test output"
    assert error == ""
    mock_channel.exec_command.assert_called_once_with("ls -la")

def test_ssh_connection_close(mock_ssh_client):
    """Test closing SSH connection."""
    connection = SSHConnection()
    connection._client = mock_ssh_client
    
    connection.close()
    mock_ssh_client.close.assert_called_once()
    assert not connection.is_connected() 