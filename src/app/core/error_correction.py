"""
Error correction and suggestion generation for failed commands.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import difflib
import os
from .command_parser import CommandParser, ParsedCommand
from .command_history import CommandHistory

# Common Unix commands and their packages
COMMON_PACKAGES = {
    'git': 'git',
    'python3': 'python3',
    'pip': 'python3-pip',
    'node': 'nodejs',
    'npm': 'npm',
    'docker': 'docker.io',
    'kubectl': 'kubectl',
    'vim': 'vim',
    'nano': 'nano',
    'gcc': 'build-essential',
    'make': 'build-essential',
    'curl': 'curl',
    'wget': 'wget',
    'ssh': 'openssh-client',
    'scp': 'openssh-client',
    'rsync': 'rsync',
    'tar': 'tar',
    'zip': 'zip',
    'unzip': 'unzip',
    'htop': 'htop',
    'top': 'procps',
    'ps': 'procps',
    'netstat': 'net-tools',
    'ifconfig': 'net-tools',
    'ping': 'iputils-ping'
}

@dataclass
class ErrorCorrection:
    """Represents a suggested correction for a failed command."""
    original_command: str
    suggested_command: str
    confidence: float
    explanation: str
    error_type: str

class ErrorCorrector:
    """Analyzes failed commands and generates correction suggestions."""

    def __init__(self, command_history: CommandHistory):
        """
        Initialize error corrector.

        Args:
            command_history: Command history for pattern analysis
        """
        self._history = command_history
        self._parser = CommandParser()
        self._common_commands = list(COMMON_PACKAGES.keys())

    def get_correction(self, failed_command: str, error_output: str) -> List[ErrorCorrection]:
        """
        Generate correction suggestions for a failed command.

        Args:
            failed_command: The command that failed
            error_output: Error message from the failed command

        Returns:
            List of possible corrections
        """
        corrections = []
        parsed_cmd = self._parser.parse_command(failed_command)
        
        # Check for common error patterns
        if "command not found" in error_output.lower():
            corrections.extend(self._handle_command_not_found(parsed_cmd))
        elif "permission denied" in error_output.lower():
            corrections.extend(self._handle_permission_denied(parsed_cmd))
        elif "no such file or directory" in error_output.lower():
            corrections.extend(self._handle_no_such_file(parsed_cmd))
        elif "invalid option" in error_output.lower() or "unknown option" in error_output.lower():
            corrections.extend(self._handle_invalid_option(parsed_cmd))
        
        # Add history-based suggestions
        corrections.extend(self._get_history_based_corrections(parsed_cmd))
        
        # Sort by confidence and return top suggestions
        corrections.sort(key=lambda x: x.confidence, reverse=True)
        return corrections[:3]  # Return top 3 suggestions

    def _handle_command_not_found(self, command: ParsedCommand) -> List[ErrorCorrection]:
        """Handle 'command not found' errors."""
        corrections = []
        
        # Check for common typos
        similar_commands = self._find_similar_commands(command.base_command)
        for cmd, similarity in similar_commands:
            corrections.append(ErrorCorrection(
                original_command=command.raw_command,
                suggested_command=command.raw_command.replace(command.base_command, cmd),
                confidence=similarity,
                explanation=f"Did you mean '{cmd}'?",
                error_type="command_not_found"
            ))
        
        # Check if command needs to be installed
        if self._is_common_package(command.base_command):
            package_name = self._get_package_name(command.base_command)
            corrections.append(ErrorCorrection(
                original_command=command.raw_command,
                suggested_command=f"sudo apt install {package_name}",
                confidence=0.8,
                explanation=f"Command '{command.base_command}' is available in package '{package_name}'",
                error_type="package_missing"
            ))
        
        return corrections

    def _handle_permission_denied(self, command: ParsedCommand) -> List[ErrorCorrection]:
        """Handle permission denied errors."""
        corrections = []
        
        # Suggest using sudo
        if not command.is_sudo:
            corrections.append(ErrorCorrection(
                original_command=command.raw_command,
                suggested_command=f"sudo {command.raw_command}",
                confidence=0.9,
                explanation="This command requires elevated privileges",
                error_type="permission_denied"
            ))
        
        # Suggest checking file permissions
        if command.args:
            corrections.append(ErrorCorrection(
                original_command=command.raw_command,
                suggested_command=f"ls -l {command.args[0]}",
                confidence=0.7,
                explanation="Check file permissions first",
                error_type="permission_denied"
            ))
        
        return corrections

    def _handle_no_such_file(self, command: ParsedCommand) -> List[ErrorCorrection]:
        """Handle 'no such file or directory' errors."""
        corrections = []
        
        # Suggest listing directory contents
        corrections.append(ErrorCorrection(
            original_command=command.raw_command,
            suggested_command="ls",
            confidence=0.7,
            explanation="List directory contents to verify file existence",
            error_type="no_such_file"
        ))
        
        # Check for similar filenames in history
        similar_files = self._find_similar_files(command.args[0] if command.args else "")
        for file, similarity in similar_files:
            new_cmd = command.raw_command.replace(command.args[0], file)
            corrections.append(ErrorCorrection(
                original_command=command.raw_command,
                suggested_command=new_cmd,
                confidence=similarity,
                explanation=f"Did you mean '{file}'?",
                error_type="no_such_file"
            ))
        
        return corrections

    def _handle_invalid_option(self, command: ParsedCommand) -> List[ErrorCorrection]:
        """Handle invalid option errors."""
        corrections = []
        
        # Check command history for correct flag usage
        patterns = self._history.get_command_patterns(command.base_command)
        if patterns and patterns.common_flags:
            for flag in command.flags:
                if flag not in patterns.common_flags:
                    # Find similar valid flags
                    similar_flags = self._find_similar_flags(flag, list(patterns.common_flags.keys()))
                    for valid_flag, similarity in similar_flags:
                        new_cmd = command.raw_command.replace(flag, valid_flag)
                        corrections.append(ErrorCorrection(
                            original_command=command.raw_command,
                            suggested_command=new_cmd,
                            confidence=similarity,
                            explanation=f"Flag '{flag}' might be '{valid_flag}'",
                            error_type="invalid_option"
                        ))
        
        # Suggest checking help
        corrections.append(ErrorCorrection(
            original_command=command.raw_command,
            suggested_command=f"{command.base_command} --help",
            confidence=0.6,
            explanation="Check command help for valid options",
            error_type="invalid_option"
        ))
        
        return corrections

    def _get_history_based_corrections(self, command: ParsedCommand) -> List[ErrorCorrection]:
        """Get correction suggestions based on command history."""
        corrections = []
        
        # Find similar successful commands from history
        patterns = self._history.get_command_patterns(command.base_command)
        if patterns and patterns.success_rate > 0:
            # Suggest common flags
            for flag in patterns.common_flags:
                if flag not in command.flags:
                    new_cmd = f"{command.raw_command} {flag}"
                    corrections.append(ErrorCorrection(
                        original_command=command.raw_command,
                        suggested_command=new_cmd,
                        confidence=0.7,
                        explanation=f"Common flag '{flag}' might be helpful",
                        error_type="missing_flag"
                    ))
        
        return corrections

    def _find_similar_commands(self, command: str) -> List[tuple[str, float]]:
        """Find similar commands using Levenshtein distance."""
        similar = []
        
        # Get list of commands from history
        history_commands = {
            entry['command'].split()[0]
            for entry in self._history._history
            if entry['exit_code'] == 0
        }
        
        # Combine with common commands
        all_commands = list(set(history_commands) | set(self._common_commands))
        
        # Find similar commands
        for cmd in all_commands:
            ratio = difflib.SequenceMatcher(None, command, cmd).ratio()
            if ratio > 0.6:  # Only include if similarity > 60%
                similar.append((cmd, ratio))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)

    def _find_similar_files(self, filename: str) -> List[tuple[str, float]]:
        """Find similar filenames in current directory."""
        similar = []
        
        try:
            # Get list of files in current directory
            files = os.listdir('.')
            
            # Find similar filenames
            for file in files:
                ratio = difflib.SequenceMatcher(None, filename, file).ratio()
                if ratio > 0.6:  # Only include if similarity > 60%
                    similar.append((file, ratio))
        except OSError:
            pass  # Ignore filesystem errors
        
        return sorted(similar, key=lambda x: x[1], reverse=True)

    def _find_similar_flags(self, flag: str, valid_flags: List[str]) -> List[tuple[str, float]]:
        """Find similar valid flags using string comparison."""
        similar = []
        
        for valid_flag in valid_flags:
            ratio = difflib.SequenceMatcher(None, flag, valid_flag).ratio()
            if ratio > 0.6:  # Only include if similarity > 60%
                similar.append((valid_flag, ratio))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)

    def _is_common_package(self, command: str) -> bool:
        """Check if command is from a common package."""
        return command in COMMON_PACKAGES

    def _get_package_name(self, command: str) -> str:
        """Get package name for a command."""
        return COMMON_PACKAGES.get(command, command) 