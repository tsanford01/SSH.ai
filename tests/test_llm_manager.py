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
    assert manager.config.max_memory_mb == 4096
    assert manager.config.max_cpu_percent == 50
    assert manager.config.context_length == 4096
    assert manager.config.temperature == 0.7
    assert manager.config.use_gpu is True
    assert manager.config.gpu_layers == 9999
    assert manager.config.batch_size == 512
    assert manager.config.threads == 7
    
    # Check initial state
    assert manager._command_history == []
    assert isinstance(manager._system_info, dict)
    assert isinstance(manager._connection_state, dict)
    assert "os" in manager._system_info
    assert "platform" in manager._system_info
    assert "python_version" in manager._system_info

def test_init_custom_config():
    """Test initialization with custom config."""
    config = LLMConfig(
        max_memory_mb=8192,
        max_cpu_percent=75,
        context_length=8192,
        temperature=0.8,
        use_gpu=False,
        gpu_layers=0,
        batch_size=256,
        threads=4
    )
    manager = LLMManager(config=config)
    assert manager.config.max_memory_mb == 8192
    assert manager.config.max_cpu_percent == 75
    assert manager.config.context_length == 8192
    assert manager.config.temperature == 0.8
    assert manager.config.use_gpu is False
    assert manager.config.gpu_layers == 0
    assert manager.config.batch_size == 256
    assert manager.config.threads == 4

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

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_context_aware_command_analysis(mock_cpu, mock_memory, manager):
    """Test context-aware command analysis."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Set up test environment
    manager._connection_state = {
        'hostname': 'test.host',
        'username': 'testuser',
        'connected': True,
        'cwd': '/home/testuser',
        'env': {
            'PATH': '/usr/bin:/usr/local/bin',
            'HOME': '/home/testuser'
        }
    }
    
    # Add some command history
    manager._command_history = [
        'cd /home/testuser',
        'ls -l',
        'mkdir test_dir'
    ]
    
    # Test file operation analysis
    result = manager.analyze_command(
        'rm -rf test_dir',
        working_dir='/home/testuser',
        environment={'DEBUG': 'true'}
    )
    
    assert result['command'].base_command == 'rm'
    assert result['type'] == 'file_operation'
    assert result['risks']['level'] == 'medium'
    assert 'destructive' in result['risks']['factors'][0].lower()
    assert 'working_dir' in result['context']
    assert result['context']['recent_commands'] == manager._command_history[-5:]
    
    # Test network operation analysis
    result = manager.analyze_command(
        'ssh -p 2222 user@remote.host',
        environment={'SSH_AUTH_SOCK': '/tmp/ssh-agent.socket'}
    )
    
    assert result['command'].base_command == 'ssh'
    assert result['type'] == 'network_operation'
    assert result['risks']['level'] == 'low'
    assert 'environment' in result['context']
    assert 'SSH_AUTH_SOCK' in result['context']['environment']
    
    # Test system operation with sudo
    result = manager.analyze_command('sudo systemctl restart nginx')
    
    assert result['command'].base_command == 'systemctl'
    assert result['type'] == 'system_operation'
    assert result['risks']['level'] == 'high'
    assert 'elevated privileges' in result['risks']['factors'][0].lower()
    assert result['context']['connection']['hostname'] == 'test.host'

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_command_analysis_with_pipeline(mock_cpu, mock_memory, manager):
    """Test analysis of pipeline commands."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    result = manager.analyze_command('ps aux | grep python | sort -k2')
    
    assert result['command'].is_pipeline
    assert len(result['command'].pipeline_commands) == 3
    assert result['type'] == 'system_operation'
    assert result['risks']['level'] == 'low'
    assert 'suggestions' in result

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_command_analysis_with_insufficient_resources(mock_cpu, mock_memory, manager):
    """Test command analysis with insufficient resources."""
    # Mock insufficient resources
    mock_memory.return_value.available = 100 * 1024 * 1024  # 100MB
    mock_cpu.return_value = 95
    
    with pytest.raises(RuntimeError, match="Insufficient system resources"):
        manager.analyze_command('find / -type f -name "*.log"')

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_command_analysis_error_handling(mock_cpu, mock_memory, manager):
    """Test error handling in command analysis."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Test with empty command
    with pytest.raises(RuntimeError, match="Failed to analyze command"):
        manager.analyze_command('')
    
    # Test with invalid working directory
    with pytest.raises(RuntimeError):
        manager.analyze_command('ls', working_dir='/nonexistent/path')

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_command_history_integration(mock_cpu, mock_memory, manager):
    """Test integration with command history analysis."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Record some command executions
    manager.record_command_execution(
        "git status",
        0,
        0.1,
        "/project",
        {"GIT_DIR": "/project/.git"}
    )
    manager.record_command_execution(
        "git add file.txt",
        0,
        0.2,
        "/project"
    )
    manager.record_command_execution(
        "git commit -m 'update'",
        0,
        0.3,
        "/project"
    )
    
    # Test command analysis with history
    result = manager.analyze_command(
        "git push",
        working_dir="/project"
    )
    
    assert result['patterns'] is not None
    assert 'commit' in result['patterns'].related_commands
    assert result['context']['patterns']['success_rate'] > 0
    assert 'git' in result['context']['recent_commands'][-1]

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_command_analysis_with_history_patterns(mock_cpu, mock_memory, manager):
    """Test command analysis using historical patterns."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Record commands with common pattern
    manager.record_command_execution(
        "ls -l",
        0,
        0.1,
        "/home/user"
    )
    manager.record_command_execution(
        "ls -l",
        0,
        0.1,
        "/home/user/docs"
    )
    manager.record_command_execution(
        "ls -la",
        0,
        0.1,
        "/home/user"
    )
    
    # Analyze command
    result = manager.analyze_command("ls")
    
    assert result['patterns'] is not None
    assert result['patterns'].frequency >= 3
    assert "-l" in result['patterns'].common_flags
    assert result['context']['patterns']['success_rate'] == 1.0

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_command_analysis_with_failed_commands(mock_cpu, mock_memory, manager):
    """Test command analysis with failed command history."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Record some failed commands
    manager.record_command_execution(
        "invalid_cmd",
        1,
        0.1
    )
    manager.record_command_execution(
        "invalid_cmd arg",
        1,
        0.1
    )
    
    # Analyze command
    result = manager.analyze_command("invalid_cmd")
    
    assert result['patterns'] is not None
    assert result['patterns'].success_rate == 0.0
    assert result['context']['patterns']['frequency'] == 2

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
def test_command_suggestions_from_history(mock_cpu, mock_memory, manager):
    """Test command suggestions based on history."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Record command sequence
    commands = [
        ("cd /project", 0, 0.1),
        ("git status", 0, 0.1),
        ("git add .", 0, 0.2),
        ("git commit -m 'test'", 0, 0.3),
        ("git push", 0, 0.2)
    ]
    
    for cmd, exit_code, duration in commands:
        manager.record_command_execution(cmd, exit_code, duration)
    
    # Test suggestions after git commands
    result = manager.analyze_command("git")
    
    assert result['patterns'] is not None
    assert len(result['patterns'].related_commands) > 0
    assert any('push' in cmd for cmd in result['patterns'].related_commands)
    assert any('commit' in cmd for cmd in result['patterns'].related_commands)

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
async def test_intelligent_suggestions(mock_cpu, mock_memory, manager):
    """Test intelligent command suggestions."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Record some command history
    manager.record_command_execution("cd /project", 0, 0.1)
    manager.record_command_execution("git status", 0, 0.2)
    manager.record_command_execution("git add .", 0, 0.3)
    manager.record_command_execution("git commit -m 'test'", 0, 0.4)
    
    # Test with partial command
    suggestions = await manager.get_intelligent_suggestions(
        partial_command="git",
        working_dir="/project"
    )
    
    assert len(suggestions) > 0
    assert all(isinstance(s, dict) for s in suggestions)
    assert all(
        all(k in s for k in ['command', 'description', 'confidence'])
        for s in suggestions
    )
    
    # Verify history-based suggestions
    history_suggestions = [s for s in suggestions if 'Used' in s['description']]
    assert len(history_suggestions) > 0
    assert any('git status' in s['command'] for s in history_suggestions)
    
    # Verify context-based suggestions
    context_suggestions = [s for s in suggestions if 'follows' in s['description']]
    assert len(context_suggestions) > 0
    assert any('push' in s['command'] for s in context_suggestions)
    
    # Test with no partial command
    suggestions = await manager.get_intelligent_suggestions(
        working_dir="/project"
    )
    assert len(suggestions) > 0
    
    # Test with no history
    manager._command_history = CommandHistory()
    suggestions = await manager.get_intelligent_suggestions(
        partial_command="ls"
    )
    assert len(suggestions) <= 1  # Only LLM suggestion possible
    
    # Test with server not ready
    manager.server_ready = False
    suggestions = await manager.get_intelligent_suggestions(
        partial_command="git"
    )
    assert all(s['description'] != "AI suggested based on your context" 
              for s in suggestions)

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
async def test_intelligent_suggestions_sorting(mock_cpu, mock_memory, manager):
    """Test sorting and deduplication of suggestions."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Add commands with varying success rates
    manager.record_command_execution("ls -l", 0, 0.1)  # Success
    manager.record_command_execution("ls -l", 0, 0.1)  # Success
    manager.record_command_execution("ls -la", 1, 0.1)  # Failure
    manager.record_command_execution("ls -la", 1, 0.1)  # Failure
    
    suggestions = await manager.get_intelligent_suggestions(
        partial_command="ls"
    )
    
    # Check sorting by confidence
    confidences = [s['confidence'] for s in suggestions]
    assert confidences == sorted(confidences, reverse=True)
    
    # Check deduplication
    commands = [s['command'] for s in suggestions]
    assert len(commands) == len(set(commands))
    
    # Verify successful command has higher confidence
    ls_l_conf = next(s['confidence'] for s in suggestions if s['command'] == 'ls -l')
    ls_la_conf = next(s['confidence'] for s in suggestions if s['command'] == 'ls -la')
    assert ls_l_conf > ls_la_conf

@patch("psutil.virtual_memory")
@patch("psutil.cpu_percent")
async def test_intelligent_suggestions_limit(mock_cpu, mock_memory, manager):
    """Test suggestion limit enforcement."""
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024
    mock_cpu.return_value = 50
    
    # Add many commands
    for i in range(10):
        manager.record_command_execution(f"cmd{i}", 0, 0.1)
    
    suggestions = await manager.get_intelligent_suggestions(
        partial_command="cmd"
    )
    
    assert len(suggestions) <= 5  # Maximum 5 suggestions 