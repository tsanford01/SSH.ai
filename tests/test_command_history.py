"""
Tests for command history analysis functionality.
"""

import pytest
from datetime import datetime, timedelta
from src.app.core.command_history import CommandHistory, CommandPattern
from src.app.core.command_parser import CommandParser

def test_add_command():
    """Test adding commands to history."""
    history = CommandHistory(max_history=3)
    
    # Add commands
    history.add_command("ls -l", 0, 0.1, "/home")
    history.add_command("cd /project", 0, 0.05, "/home")
    history.add_command("git status", 0, 0.2, "/project")
    
    # Test history limit
    history.add_command("git diff", 0, 0.15, "/project")
    
    # First command should be removed
    pattern = history.get_command_patterns("ls -l")
    assert pattern is None

def test_command_patterns():
    """Test command pattern recognition."""
    history = CommandHistory()
    
    # Add same command twice
    history.add_command("ls -l /home", 0, 0.1, "/home")
    history.add_command("ls -l /home", 0, 0.1, "/home")
    
    pattern = history.get_command_patterns("ls -l /home")
    assert pattern is not None
    assert pattern.frequency == 2  # Only count exact matches
    assert pattern.success_rate == 1.0
    assert abs(pattern.avg_duration - 0.1) < 0.001

def test_command_relationships():
    """Test tracking of command relationships."""
    history = CommandHistory()
    
    # Add sequence of commands
    history.add_command("cd /project", 0, 0.05, "/home")
    history.add_command("git status", 0, 0.2, "/project")
    history.add_command("git diff", 0, 0.15, "/project")
    
    pattern = history.get_command_patterns("cd /project")
    assert pattern is not None
    assert "git" in pattern.related_commands

def test_sequence_analysis():
    """Test analysis of command sequences."""
    history = CommandHistory()
    
    # Add sequence of commands
    history.add_command("cd /project", 0, 0.05, "/home")
    history.add_command("git status", 0, 0.2, "/project")
    history.add_command("git diff", 1, 0.15, "/project")  # Failed command
    
    analysis = history.analyze_command_sequence(["cd /project", "git status", "git diff"])
    assert analysis["success_rate"] == 0.0  # One command failed
    assert abs(analysis["total_duration"] - 0.4) < 0.001
    assert len(analysis["suggestions"]) <= 5

def test_empty_history():
    """Test behavior with empty history."""
    history = CommandHistory()
    
    pattern = history.get_command_patterns("ls")
    assert pattern is None
    
    analysis = history.analyze_command_sequence(["ls"])
    assert analysis["success_rate"] == 0.0
    assert analysis["total_duration"] == 0.0
    assert len(analysis["suggestions"]) == 0

def test_command_suggestions():
    """Test command suggestions."""
    history = CommandHistory()
    
    # Add sequence of commands
    history.add_command("cd /project", 0, 0.05, "/home")
    history.add_command("git status", 0, 0.2, "/project")
    history.add_command("git diff", 0, 0.15, "/project")
    history.add_command("git commit", 0, 0.3, "/project")
    
    # Get suggestions after git status
    analysis = history.analyze_command_sequence(["cd /project", "git status"])
    assert "git diff" in analysis["suggestions"]

def test_working_directory_tracking():
    """Test tracking of working directories."""
    history = CommandHistory()
    
    history.add_command("ls -l", 0, 0.1, "/home")
    history.add_command("cd /project", 0, 0.05, "/home")
    history.add_command("git status", 0, 0.2, "/project")
    
    pattern = history.get_command_patterns("ls -l")
    assert pattern is not None
    assert pattern.frequency == 1
    assert pattern.success_rate == 1.0

def test_history_limit():
    """Test history size limit."""
    history = CommandHistory(max_history=2)
    
    # Add more commands than the limit
    history.add_command("cmd1", 0, 0.1)
    history.add_command("cmd2", 0, 0.1)
    history.add_command("cmd3", 0, 0.1)
    
    # First command should be removed
    pattern = history.get_command_patterns("cmd1")
    assert pattern is None
    
    # Later commands should still be present
    pattern = history.get_command_patterns("cmd3")
    assert pattern is not None

def test_error_handling():
    """Test error handling in command history."""
    history = CommandHistory()
    
    # Add failed command
    history.add_command("invalid_cmd", 1, 0.1)
    
    pattern = history.get_command_patterns("invalid_cmd")
    assert pattern is not None
    assert pattern.success_rate == 0.0

def test_environment_tracking():
    """Test tracking of environment variables."""
    history = CommandHistory()
    
    # Add command with environment
    history.add_command("echo $PATH", 0, 0.1, "/home")
    
    pattern = history.get_command_patterns("echo $PATH")
    assert pattern is not None
    assert pattern.frequency == 1
    assert pattern.success_rate == 1.0 