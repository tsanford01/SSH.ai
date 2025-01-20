"""
Tests for LLM manager functionality.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch
from pathlib import Path

from src.app.core.llm_manager import LLMManager, LLMConfig

@pytest.fixture
def config():
    """Create test LLM configuration."""
    return LLMConfig(
        max_memory_mb=1024,
        max_cpu_percent=30,
        context_length=512,
        temperature=0.5
    )

@pytest.fixture
def manager(config):
    """Create LLM manager with test configuration."""
    return LLMManager(config)

def test_init_default_config():
    """Test initialization with default config."""
    manager = LLMManager()
    assert manager.config.max_memory_mb == 2048
    assert manager.config.max_cpu_percent == 50
    assert manager.config.context_length == 1024
    assert manager.config.temperature == 0.7
    
    # Check initial state
    assert manager._command_history == []
    assert isinstance(manager._system_info, dict)
    assert isinstance(manager._connection_state, dict)
    assert "os" in manager._system_info
    assert "platform" in manager._system_info
    assert "python_version" in manager._system_info

def test_init_custom_config(config, manager):
    """Test initialization with custom config."""
    assert manager.config == config

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_check_resources_sufficient(mock_cpu, mock_memory, manager):
    """Test resource check with sufficient resources."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024  # 2GB
    mock_cpu.return_value = 50  # 50% CPU usage
    
    assert manager._check_resources() is True

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_check_resources_insufficient_memory(mock_cpu, mock_memory, manager):
    """Test resource check with insufficient memory."""
    # Mock insufficient memory
    mock_memory.return_value.available = 512 * 1024 * 1024  # 512MB
    mock_cpu.return_value = 50
    
    assert manager._check_resources() is False

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_check_resources_insufficient_cpu(mock_cpu, mock_memory, manager):
    """Test resource check with insufficient CPU."""
    # Mock insufficient CPU
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 90  # 90% CPU usage
    
    assert manager._check_resources() is False

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_analyze_command(mock_cpu, mock_memory, manager):
    """Test SSH command analysis."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Add some command history
    manager.add_command("ssh user@host")
    manager.add_command("scp file.txt user@host:")
    
    response = manager.analyze_command("ssh -p 2222 user@host")
    assert isinstance(response, str)
    assert len(response) > 0

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_analyze_command_insufficient_resources(mock_cpu, mock_memory, manager):
    """Test command analysis with insufficient resources."""
    # Mock insufficient resources
    mock_memory.return_value.available = 512 * 1024 * 1024
    mock_cpu.return_value = 90
    
    with pytest.raises(RuntimeError, match="Insufficient system resources"):
        manager.analyze_command("ssh -p 2222 user@host")

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_analyze_error(mock_cpu, mock_memory, manager):
    """Test SSH error analysis."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    response = manager.analyze_error(
        "Permission denied (publickey).",
        command="ssh user@host"
    )
    assert isinstance(response, str)
    assert len(response) > 0

def test_command_history_management(manager):
    """Test command history management."""
    # Add commands
    for i in range(110):
        manager.add_command(f"command{i}")
    
    # Check history limit
    assert len(manager._command_history) == 100
    assert manager._command_history[0] == "command10"
    assert manager._command_history[-1] == "command109"

def test_connection_state_update(manager):
    """Test connection state updates."""
    # Update state
    manager.update_connection_state({
        "authenticated": True,
        "key_type": "RSA",
        "cipher": "aes256-cbc"
    })
    
    assert manager._connection_state["authenticated"] is True
    assert manager._connection_state["key_type"] == "RSA"
    assert manager._connection_state["cipher"] == "aes256-cbc"
    
    # Update partial state
    manager.update_connection_state({"authenticated": False})
    assert manager._connection_state["authenticated"] is False
    assert manager._connection_state["key_type"] == "RSA"

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_security_check(mock_cpu, mock_memory, manager):
    """Test security analysis."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    response = manager.check_security("ssh -p 2222 user@host")
    assert isinstance(response, str)
    assert len(response) > 0

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_performance_optimization(mock_cpu, mock_memory, manager):
    """Test performance optimization analysis."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Set some connection state
    manager.update_connection_state({
        "compression": "none",
        "cipher": "aes128-ctr"
    })
    
    response = manager.optimize_performance()
    assert isinstance(response, str)
    assert len(response) > 0

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_connection_diagnosis(mock_cpu, mock_memory, manager):
    """Test connection issue diagnosis."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    response = manager.diagnose_connection(
        error="Connection timed out"
    )
    assert isinstance(response, str)
    assert len(response) > 0 