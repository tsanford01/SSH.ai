"""
Tests for command optimization functionality.
"""

import pytest
from src.app.core.command_optimizer import CommandOptimizer, OptimizationSuggestion
from src.app.core.command_history import CommandHistory

def test_performance_optimizations():
    """Test performance optimization suggestions."""
    history = CommandHistory()
    optimizer = CommandOptimizer(history)
    
    # Test file operation optimization
    suggestions = optimizer.get_optimizations("cp *.txt /backup/")
    assert len(suggestions) > 0
    assert any(s.improvement_type == "performance" and "parallel" in s.optimized_command for s in suggestions)
    
    # Test network operation optimization
    suggestions = optimizer.get_optimizations("scp large_file.dat server:/path/")
    assert len(suggestions) > 0
    assert any(s.improvement_type == "performance" and "-C" in s.optimized_command for s in suggestions)
    
    # Test search operation optimization
    suggestions = optimizer.get_optimizations("grep -r pattern .")
    assert len(suggestions) > 0
    assert any(s.improvement_type == "performance" and "rg" in s.optimized_command for s in suggestions)

def test_safety_improvements():
    """Test safety improvement suggestions."""
    history = CommandHistory()
    optimizer = CommandOptimizer(history)

    # Test rm safety suggestions for trash-put
    suggestions = optimizer.get_optimizations("rm -rf /path")
    assert any(s.improvement_type == "safety" and "trash-put" in s.optimized_command for s in suggestions)

    # Test rm safety suggestions for interactive mode
    suggestions = optimizer.get_optimizations("rm -rf /path")
    assert any(s.improvement_type == "safety" and "-i" in s.optimized_command for s in suggestions)

    # Test sudo safety suggestions
    suggestions = optimizer.get_optimizations("sudo apt update")
    assert len(suggestions) > 0
    assert any(s.improvement_type == "safety" and "$(which" in s.optimized_command for s in suggestions)

def test_readability_improvements():
    """Test readability improvement suggestions."""
    history = CommandHistory()
    optimizer = CommandOptimizer(history)

    # Test flag combination suggestions
    suggestions = optimizer.get_optimizations("ls -l -a -h")
    assert any(s.improvement_type == "readability" and "-lah" in s.optimized_command for s in suggestions)

def test_command_specific_optimizations():
    """Test command-specific optimization suggestions."""
    history = CommandHistory()
    optimizer = CommandOptimizer(history)
    
    # Test git optimizations
    suggestions = optimizer.get_optimizations("git status")
    assert len(suggestions) > 0
    assert any(s.improvement_type == "performance" and "-sb" in s.optimized_command for s in suggestions)
    
    suggestions = optimizer.get_optimizations("git clone https://github.com/user/repo.git")
    assert len(suggestions) > 0
    assert any(s.improvement_type == "performance" and "--depth" in s.optimized_command for s in suggestions)
    
    # Test tar optimizations
    suggestions = optimizer.get_optimizations("tar -czf archive.tar.gz files/")
    assert len(suggestions) > 0
    assert any(s.improvement_type == "performance" and "--threads" in s.optimized_command for s in suggestions)

def test_multiple_suggestions():
    """Test that multiple relevant suggestions are returned."""
    history = CommandHistory()
    optimizer = CommandOptimizer(history)

    # Command that should trigger multiple suggestions
    suggestions = optimizer.get_optimizations("rm -rf /path/*.txt")

    # Should have at least safety and alternative suggestions
    assert len({s.improvement_type for s in suggestions}) >= 2  # At least 2 different types

def test_estimated_speedup():
    """Test that performance suggestions include estimated speedup."""
    history = CommandHistory()
    optimizer = CommandOptimizer(history)
    
    suggestions = optimizer.get_optimizations("grep -r pattern .")
    performance_suggestions = [s for s in suggestions if s.improvement_type == "performance"]
    
    assert len(performance_suggestions) > 0
    assert all(s.estimated_speedup is not None and s.estimated_speedup > 1.0 
              for s in performance_suggestions)

def test_empty_input():
    """Test handling of empty input."""
    history = CommandHistory()
    optimizer = CommandOptimizer(history)
    
    with pytest.raises(ValueError):
        optimizer.get_optimizations("")

def test_unknown_command():
    """Test handling of unknown commands."""
    history = CommandHistory()
    optimizer = CommandOptimizer(history)
    
    suggestions = optimizer.get_optimizations("unknown_cmd")
    assert len(suggestions) == 0  # No suggestions for unknown commands 

def test_core_functionality():
    """Test core functionality of CommandOptimizer for various command types."""
    history = CommandHistory()
    optimizer = CommandOptimizer(history)

    # Test a variety of commands
    commands = [
        "rm -rf /path",  # Safety
        "ls -l -a -h",  # Readability
        "cp *.txt /backup/",  # Performance
        "git status",  # Command-specific
        "tar -czf archive.tar.gz files/"  # Performance
    ]

    for command in commands:
        suggestions = optimizer.get_optimizations(command)
        assert len(suggestions) > 0, f"No suggestions for command: {command}"
        assert any(isinstance(s, OptimizationSuggestion) for s in suggestions), f"Invalid suggestion type for command: {command}"

    # Ensure multiple suggestion types are generated
    suggestions = optimizer.get_optimizations("rm -rf /path/*.txt")
    assert len({s.improvement_type for s in suggestions}) >= 2, "Expected multiple suggestion types" 