"""
Tests for session manager functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import json

from src.app.core.session_manager import Session, SessionManager
from src.app.core.ssh_connection import SSHCredentials
from src.app.core.llm_manager import LLMManager

@pytest.fixture
def mock_llm():
    """Create mock LLM manager."""
    return Mock(spec=LLMManager)

@pytest.fixture
def mock_ssh_client():
    """Create mock SSH client."""
    client = MagicMock()
    client.connect = MagicMock()  # Mock the connect method
    return client

@pytest.fixture
def mock_connection(mock_ssh_client):
    """Create mock SSH connection."""
    connection = Mock()
    connection.client = mock_ssh_client
    connection.credentials = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host",
        port=22
    )
    return connection

@pytest.fixture
def session_dir(tmp_path):
    """Create temporary session directory."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    return session_dir

@pytest.fixture
def session(mock_connection, mock_llm, session_dir):
    """Create test session."""
    return Session(mock_connection, mock_llm, session_dir)

@pytest.fixture
def manager(mock_llm, session_dir):
    """Create session manager for testing."""
    return SessionManager(mock_llm, session_dir)

def test_session_initialization(session):
    """Test session initialization."""
    assert session.connection is not None
    assert session.llm is not None
    assert session.command_history == []
    assert session.llm_interactions == []
    assert session.start_time is not None
    assert session.end_time is None

def test_add_successful_command(session):
    """Test adding successful command."""
    session.add_command("ls -l", "file1\nfile2", 0, 0.1)
    assert len(session.command_history) == 1
    cmd = session.command_history[0]
    assert cmd["command"] == "ls -l"
    assert cmd["exit_code"] == 0
    assert cmd["output"] == "file1\nfile2"
    assert cmd["duration"] == 0.1

def test_add_failed_command(session):
    """Test adding failed command."""
    session.add_command("invalid", "command not found", 1, 0.1)
    assert len(session.command_history) == 1
    cmd = session.command_history[0]
    assert cmd["command"] == "invalid"
    assert cmd["exit_code"] == 1
    assert cmd["output"] == "command not found"
    assert cmd["duration"] == 0.1

def test_add_llm_interaction(session):
    """Test adding LLM interaction."""
    session.add_llm_interaction(
        "What is the disk usage?",
        "The disk usage is 80%",
        1.5,
        True
    )
    assert len(session.llm_interactions) == 1
    interaction = session.llm_interactions[0]
    assert interaction["prompt"] == "What is the disk usage?"
    assert interaction["response"] == "The disk usage is 80%"
    assert interaction["duration"] == 1.5
    assert interaction["was_helpful"] is True

def test_session_end_and_save(session):
    """Test ending and saving session."""
    session.end()
    assert session.end_time is not None
    summary = session.get_summary()
    assert summary.hostname == "test.host"
    assert summary.username == "testuser"
    assert summary.command_count == 0

def test_session_summary(session):
    """Test session summary generation."""
    session.add_command("ls", "file1", 0, 0.1)
    session.add_command("pwd", "/home", 0, 0.1)
    session.add_llm_interaction("disk usage?", "80%", 1.0, True)
    session.end()
    
    summary = session.get_summary()
    assert summary.command_count == 2
    assert len(summary.key_insights) > 0
    assert summary.performance_metrics["successful_suggestions"] == 1

@patch('paramiko.SSHClient')
def test_manager_create_session(mock_ssh_client, manager):
    """Test creating new session."""
    # Configure mock
    mock_instance = mock_ssh_client.return_value
    mock_instance.connect = MagicMock()  # Mock the connect method
    
    credentials = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host",
        port=22
    )
    
    session = manager.create_session(credentials)
    assert session is not None
    assert session.connection.credentials == credentials
    assert len(manager.active_sessions) == 1
    mock_instance.connect.assert_called_once()

@patch('paramiko.SSHClient')
def test_manager_duplicate_session(mock_ssh_client, manager):
    """Test creating duplicate session."""
    # Configure mock
    mock_instance = mock_ssh_client.return_value
    mock_instance.connect = MagicMock()  # Mock the connect method
    
    credentials = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host",
        port=22
    )
    
    manager.create_session(credentials)
    with pytest.raises(RuntimeError):
        manager.create_session(credentials)

@patch('paramiko.SSHClient')
def test_manager_end_session(mock_ssh_client, manager):
    """Test ending session."""
    # Configure mock
    mock_instance = mock_ssh_client.return_value
    mock_instance.connect = MagicMock()  # Mock the connect method
    
    credentials = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host",
        port=22
    )
    
    manager.create_session(credentials)
    assert len(manager.active_sessions) == 1
    
    manager.end_session("test.host", "testuser")
    assert len(manager.active_sessions) == 0

@patch('paramiko.SSHClient')
def test_manager_list_sessions(mock_ssh_client, manager):
    """Test listing active sessions."""
    # Configure mock
    mock_instance = mock_ssh_client.return_value
    mock_instance.connect = MagicMock()  # Mock the connect method
    
    # Create two sessions
    credentials1 = SSHCredentials(
        username="user1",
        password="pass1",
        hostname="host1",
        port=22
    )
    credentials2 = SSHCredentials(
        username="user2",
        password="pass2",
        hostname="host2",
        port=22
    )
    
    session1 = manager.create_session(credentials1)
    session2 = manager.create_session(credentials2)
    
    sessions = manager.list_sessions()
    assert len(sessions) == 2
    assert session1 in sessions
    assert session2 in sessions

def test_load_session_history(manager):
    """Test loading session history."""
    # Create test session files
    session1 = {
        "start_time": "2024-01-01T00:00:00",
        "end_time": "2024-01-01T01:00:00",
        "hostname": "host1",
        "username": "user1",
        "command_history": [],
        "error_history": [],
        "llm_interactions": [],
        "performance_metrics": {},
        "summary": []
    }
    
    with open(manager.session_dir / "session_host1_20240101_000000.json", "w") as f:
        json.dump(session1, f)
    
    sessions = manager.load_session_history(hostname="host1")
    assert len(sessions) == 1
    assert sessions[0]["hostname"] == "host1" 