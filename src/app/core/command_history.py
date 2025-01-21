"""
Command history analysis and pattern recognition.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import re
from .command_parser import CommandParser
from collections import defaultdict, Counter

@dataclass
class CommandMetadata:
    """Metadata for a command execution."""
    timestamp: datetime
    exit_code: int
    duration: float
    working_dir: Optional[str] = None
    environment: Optional[Dict[str, str]] = None

@dataclass
class CommandPattern:
    """Pattern information for a command."""
    frequency: int = 0
    success_rate: float = 0.0
    avg_duration: float = 0.0
    common_args: List[str] = field(default_factory=list)
    common_flags: Dict[str, Optional[str]] = field(default_factory=dict)
    related_commands: List[str] = field(default_factory=list)

class CommandHistory:
    """Tracks and analyzes command execution history."""

    def __init__(self, max_history: int = 1000) -> None:
        """
        Initialize command history.

        Args:
            max_history: Maximum number of commands to store
        """
        self._history: List[Dict[str, Any]] = []
        self._max_history = max_history
        self._parser = CommandParser()

    def add_command(self, command: str, exit_code: int, duration: float, working_dir: Optional[str] = None) -> None:
        """
        Add command execution to history.

        Args:
            command: Executed command
            exit_code: Command exit code
            duration: Execution duration in seconds
            working_dir: Working directory when command was executed
        """
        entry = {
            'command': command,
            'exit_code': exit_code,
            'duration': duration,
            'working_dir': working_dir,
            'timestamp': datetime.now()
        }
        
        self._history.append(entry)
        
        # Maintain history size limit
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def get_command_patterns(self, command: str) -> Optional[CommandPattern]:
        """
        Get pattern information for a command.

        Args:
            command: Command to analyze

        Returns:
            Command pattern information or None if no history
        """
        # Find matches for the base command
        base_cmd = command.split()[0]
        matches = [
            entry for entry in self._history 
            if entry['command'].split()[0] == base_cmd
        ]
        
        if not matches:
            return None
            
        # Calculate metrics
        frequency = len(matches)
        success_count = sum(1 for m in matches if m['exit_code'] == 0)
        success_rate = success_count / frequency if frequency > 0 else 0.0
        avg_duration = sum(m['duration'] for m in matches) / frequency
        
        # Find common flags and arguments
        flag_counter = Counter()
        arg_counter = Counter()
        
        for entry in matches:
            cmd = self._parser.parse_command(entry['command'])
            for flag in cmd.flags:
                flag_counter[flag] += 1
            for arg in cmd.args:
                arg_counter[arg] += 1
        
        # Get most common flags and args
        common_flags = {
            flag: None
            for flag, _ in flag_counter.most_common(5)
        }
        
        common_args = [
            arg for arg, _ in arg_counter.most_common(5)
        ]
        
        # Find related commands
        related = []
        for i, entry in enumerate(self._history[:-1]):
            if entry['command'].split()[0] == base_cmd:
                next_cmd = self._history[i + 1]['command'].split()[0]
                if next_cmd not in related:
                    related.append(next_cmd)
        
        return CommandPattern(
            frequency=frequency,
            success_rate=success_rate,
            avg_duration=avg_duration,
            common_args=common_args,
            common_flags=common_flags,
            related_commands=related
        )

    def analyze_command_sequence(self, commands: List[str]) -> Dict[str, Any]:
        """
        Analyze a sequence of commands.

        Args:
            commands: List of commands to analyze

        Returns:
            Analysis results
        """
        if not commands:
            return {
                'success_rate': 0.0,
                'total_duration': 0.0,
                'common_patterns': [],
                'suggestions': []
            }

        # Find matching sequences
        matches = []
        for i in range(len(self._history) - len(commands) + 1):
            sequence = [e['command'] for e in self._history[i:i + len(commands)]]
            if sequence == commands:
                matches.append(self._history[i:i + len(commands)])

        if not matches:
            return {
                'success_rate': 0.0,
                'total_duration': 0.0,
                'common_patterns': [],
                'suggestions': []
            }

        # Calculate metrics
        success_rate = sum(
            1 for seq in matches 
            if all(e['exit_code'] == 0 for e in seq)
        ) / len(matches)

        total_duration = sum(
            sum(e['duration'] for e in seq)
            for seq in matches
        ) / len(matches)

        # Find common patterns
        patterns = []
        for cmd in commands:
            pattern = self.get_command_patterns(cmd)
            if pattern and pattern.frequency > 1:
                patterns.append(pattern)

        return {
            'success_rate': success_rate,
            'total_duration': total_duration,
            'common_patterns': patterns,
            'suggestions': self._get_suggestions_for_sequence(commands)
        }

    def _get_suggestions_for_sequence(self, commands: List[str]) -> List[str]:
        """Get command suggestions based on sequence."""
        suggestions = []
        if not commands:
            return suggestions

        last_command = commands[-1]
        for i, entry in enumerate(self._history[:-1]):
            if entry['command'] == last_command:
                next_cmd = self._history[i + 1]['command']
                if next_cmd not in suggestions:
                    suggestions.append(next_cmd)

        return suggestions[:5]  # Return top 5 suggestions 