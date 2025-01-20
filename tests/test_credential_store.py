"""
Tests for credential storage functionality.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from src.app.core.credential_store import CredentialStore
from src.app.core.ssh_connection import SSHCredentials

@pytest.fixture
def store():
    """Create a test credential store."""
    # Use a temporary file for testing
    test_file = Path("test_credentials.db")
    store = CredentialStore(test_file)
    yield store
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()

def test_store_creation(store):
    """Test credential store initialization."""
    assert store.db_path.name == "test_credentials.db"
    assert store.db_path.exists()

def test_save_credentials(store):
    """Test saving credentials."""
    creds = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host",
        port=22
    )
    
    # Save credentials
    store.save_credentials("Test Server", creds)
    
    # Verify credentials were saved
    saved_creds = store.get_credentials("Test Server")
    assert saved_creds is not None
    assert saved_creds.username == "testuser"
    assert saved_creds.hostname == "test.host"
    assert saved_creds.port == 22
    assert saved_creds.get_password() == "testpass"

def test_save_credentials_with_key(store):
    """Test saving credentials with SSH key."""
    creds = SSHCredentials(
        username="testuser",
        hostname="test.host",
        port=22,
        key_filename="/path/to/key.pem"
    )
    
    store.save_credentials("Key Server", creds)
    saved_creds = store.get_credentials("Key Server")
    assert saved_creds.key_filename == "/path/to/key.pem"
    assert saved_creds.password is None

def test_list_profiles(store):
    """Test listing saved profiles."""
    # Add some test profiles
    creds1 = SSHCredentials(
        username="user1",
        password="pass1",
        hostname="host1"
    )
    creds2 = SSHCredentials(
        username="user2",
        password="pass2",
        hostname="host2"
    )
    
    store.save_credentials("Server 1", creds1)
    store.save_credentials("Server 2", creds2)
    
    profiles = store.list_profiles()
    assert len(profiles) == 2
    assert "Server 1" in profiles
    assert "Server 2" in profiles

def test_delete_profile(store):
    """Test deleting a profile."""
    creds = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host"
    )
    
    store.save_credentials("Test Server", creds)
    assert store.get_credentials("Test Server") is not None
    
    store.delete_profile("Test Server")
    assert store.get_credentials("Test Server") is None

def test_update_credentials(store):
    """Test updating existing credentials."""
    # Initial credentials
    creds = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host"
    )
    store.save_credentials("Test Server", creds)
    
    # Updated credentials
    new_creds = SSHCredentials(
        username="newuser",
        password="newpass",
        hostname="new.host"
    )
    store.save_credentials("Test Server", new_creds)
    
    # Verify update
    saved_creds = store.get_credentials("Test Server")
    assert saved_creds.username == "newuser"
    assert saved_creds.hostname == "new.host"
    assert saved_creds.get_password() == "newpass"

def test_invalid_profile(store):
    """Test getting non-existent profile."""
    assert store.get_credentials("NonExistent") is None

def test_encryption(store):
    """Test that credentials are stored encrypted."""
    creds = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host"
    )
    store.save_credentials("Test Server", creds)
    
    # Read raw database file
    with open(store.db_path, 'rb') as f:
        raw_data = f.read()
    
    # Verify password is not stored in plaintext
    assert b"testpass" not in raw_data 