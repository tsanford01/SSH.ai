"""
Command explanation and analysis module.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .command_parser import CommandParser, ParsedCommand
from .command_history import CommandHistory

@dataclass
class CommandExplanation:
    """Detailed explanation of a command."""
    command: str
    description: str
    flags_explained: Dict[str, str]
    args_explained: List[str]
    risks: List[str]
    alternatives: List[str]
    examples: List[str]
    expected_output: str
    side_effects: List[str]

# Common command descriptions and flag explanations
COMMAND_INFO = {
    'ls': {
        'description': 'List directory contents',
        'flags': {
            '-l': 'Use a long listing format',
            '-a': 'Show hidden files (starting with .)',
            '-h': 'Show sizes in human readable format',
            '-r': 'Reverse order while sorting',
            '-t': 'Sort by modification time',
            '--color': 'Colorize the output'
        },
        'examples': [
            'ls -l /home',
            'ls -la',
            'ls -lh'
        ],
        'output': 'List of files and directories with requested details',
        'side_effects': []
    },
    'cd': {
        'description': 'Change the current working directory',
        'flags': {},
        'examples': [
            'cd /home',
            'cd ..',
            'cd ~'
        ],
        'output': 'No output on success',
        'side_effects': [
            'Changes current working directory'
        ]
    },
    'rm': {
        'description': 'Delete files or directories permanently',
        'flags': {
            '-r': 'Remove directories and their contents recursively',
            '-f': 'Force removal without confirmation',
            '-i': 'Prompt before every removal'
        },
        'examples': [
            'rm file.txt',
            'rm -r directory',
            'rm -rf directory'
        ],
        'output': 'No output on success',
        'side_effects': [
            'Permanently deletes files/directories',
            'Cannot be undone'
        ]
    },
    'git': {
        'description': 'Version control system',
        'flags': {
            'status': 'Show working tree status',
            'add': 'Add file contents to the index',
            'commit': 'Record changes to the repository',
            'push': 'Update remote refs along with associated objects',
            'pull': 'Fetch from and integrate with another repository',
            '-m': 'Use the given message as the commit message'
        },
        'examples': [
            'git status',
            'git add .',
            'git commit -m "message"'
        ],
        'output': 'Repository state changes will be displayed',
        'side_effects': [
            'May modify repository state',
            'May modify working directory'
        ]
    },
    'echo': {
        'description': 'Display a line of text',
        'flags': {
            '-n': 'Do not output trailing newline',
            '-e': 'Enable interpretation of backslash escapes'
        },
        'examples': [
            'echo "Hello"',
            'echo -n "No newline"',
            'echo "test" > file.txt'
        ],
        'output': 'Displays the provided text',
        'side_effects': []
    }
}

class CommandExplainer:
    """Analyzes and explains shell commands."""

    def __init__(self, command_history: CommandHistory):
        """
        Initialize command explainer.

        Args:
            command_history: Command history for context
        """
        self._history = command_history
        self._parser = CommandParser()

    def explain_command(self, command: str) -> CommandExplanation:
        """
        Generate detailed explanation of a command.

        Args:
            command: Command to explain

        Returns:
            Detailed command explanation
        """
        if not command:
            raise ValueError("Command cannot be empty")
        
        parsed = self._parser.parse_command(command)
        base_info = self._get_base_command_info(parsed.base_command)
        
        # Get flag explanations
        flags_explained = {}
        # Check for combined flags (e.g. -rf)
        for flag in parsed.flags:
            if len(flag) > 2 and flag.startswith('-') and not flag.startswith('--'):
                # Split combined flags
                for f in flag[1:]:
                    flags_explained[f'-{f}'] = self._get_flag_explanation(parsed.base_command, f'-{f}')
            else:
                explanation = self._get_flag_explanation(parsed.base_command, flag)
                if explanation:
                    flags_explained[flag] = explanation
        
        # Get argument explanations
        args_explained = self._explain_arguments(parsed)
        
        # Get risk analysis
        risks = self._analyze_risks(parsed)
        
        # Find alternatives
        alternatives = self._find_alternatives(parsed)
        
        # Get relevant examples
        examples = self._get_relevant_examples(parsed)
        
        # Predict output and side effects
        expected_output = self._predict_output(parsed)
        side_effects = self._predict_side_effects(parsed)
        
        return CommandExplanation(
            command=command,
            description=base_info.get('description', 'No description available'),
            flags_explained=flags_explained,
            args_explained=args_explained,
            risks=risks,
            alternatives=alternatives,
            examples=examples,
            expected_output=expected_output,
            side_effects=side_effects
        )

    def _get_base_command_info(self, command: str) -> Dict[str, Any]:
        """Get base information about a command."""
        # Check for git subcommands
        if command == 'git' and len(command.split()) > 1:
            return COMMAND_INFO.get('git', {})
        return COMMAND_INFO.get(command, {
            'description': 'No description available',
            'flags': {},
            'examples': [],
            'output': 'Unknown',
            'side_effects': []
        })

    def _get_flag_explanation(self, command: str, flag: str) -> Optional[str]:
        """Get explanation for a command flag."""
        command_info = self._get_base_command_info(command)
        return command_info.get('flags', {}).get(flag)

    def _explain_arguments(self, command: ParsedCommand) -> List[str]:
        """Generate explanations for command arguments."""
        explanations = []
        
        # First process the raw command to extract the actual arguments
        raw_args = command.raw_command.split()[1:]  # Skip the command itself
        
        for arg in raw_args:
            if arg.startswith('-'):
                continue  # Skip flags
            elif arg.startswith('/') or arg.startswith('~'):
                explanations.append(f"Path: {arg}")
            elif '*' in arg or '?' in arg:
                explanations.append(f"Pattern: {arg}")
            else:
                # Check if it looks like a path
                if '/' in arg or '\\' in arg:
                    explanations.append(f"Path: {arg}")
                else:
                    explanations.append(f"Argument: {arg}")
        
        return explanations

    def _analyze_risks(self, command: ParsedCommand) -> List[str]:
        """Analyze potential risks of the command."""
        risks = []
        
        # Check for destructive operations
        if command.base_command in {'rm', 'mv', 'dd'}:
            risks.append("This command can permanently delete or modify files")
            
            # Handle combined flags (e.g. -rf)
            all_flags = set()
            for flag in command.flags:
                if len(flag) > 2 and flag.startswith('-') and not flag.startswith('--'):
                    # Split combined flags
                    all_flags.update(f'-{f}' for f in flag[1:])
                else:
                    all_flags.add(flag)
            
            if '-f' in all_flags:
                risks.append("Force flag (-f) bypasses confirmation prompts")
            if '-r' in all_flags or '-R' in all_flags:
                risks.append("Recursive operation affects all subdirectories")
            if command.base_command == 'rm' and ('-r' in all_flags or '-R' in all_flags) and '-f' in all_flags:
                risks.append("Combination of -rf flags is extremely dangerous")
        
        # Check for elevated privileges
        if command.is_sudo:
            risks.append("Command runs with elevated privileges (sudo)")
        
        # Check for network operations
        if command.base_command in {'curl', 'wget', 'ssh', 'scp'}:
            risks.append("Command performs network operations")
        
        # Check for system modifications
        if command.base_command in {'chmod', 'chown', 'mount'}:
            risks.append("Command modifies system settings or permissions")
        
        return risks

    def _find_alternatives(self, command: ParsedCommand) -> List[str]:
        """Find alternative commands with similar functionality."""
        alternatives = []
        
        # Common alternative mappings
        alt_map = {
            'rm': ['trash-put', 'shred'],
            'cp': ['rsync'],
            'mv': ['rsync --remove-source-files'],
            'cat': ['less', 'more', 'bat'],
            'ls': ['exa', 'tree'],
            'grep': ['rg', 'ag'],
            'find': ['fd'],
            'top': ['htop', 'btop'],
            'vim': ['nano', 'emacs'],
            'wget': ['curl'],
            'netstat': ['ss']
        }
        
        base_alternatives = alt_map.get(command.base_command, [])
        for alt in base_alternatives:
            if command.args:
                alternatives.append(f"{alt} {' '.join(command.args)}")
            else:
                alternatives.append(alt)
        
        return alternatives

    def _get_relevant_examples(self, command: ParsedCommand) -> List[str]:
        """Get relevant command examples."""
        # Start with built-in examples
        examples = self._get_base_command_info(command.base_command).get('examples', [])
        
        # Add examples from history
        patterns = self._history.get_command_patterns(command.base_command)
        if patterns and patterns.success_rate > 0.8:  # Only use successful commands
            for cmd in [e['command'] for e in self._history._history if e['exit_code'] == 0]:
                if cmd.startswith(command.base_command) and cmd not in examples:
                    examples.append(cmd)
        
        return examples[:5]  # Return top 5 examples

    def _predict_output(self, command: ParsedCommand) -> str:
        """Predict command output format."""
        return self._get_base_command_info(command.base_command).get('output', 'Unknown output format')

    def _predict_side_effects(self, command: ParsedCommand) -> List[str]:
        """Predict command side effects."""
        base_effects = self._get_base_command_info(command.base_command).get('side_effects', [])
        effects = base_effects.copy()  # Create a copy to avoid modifying the original
        
        # Add context-specific side effects
        if command.is_sudo:
            effects.append("May modify system files or settings")
        
        # Check for redirections in the raw command since the parser might not catch all cases
        if '>' in command.raw_command or '>>' in command.raw_command:
            effects.append("Will modify output files")
        
        if command.base_command == 'git' and 'commit' in command.args:
            effects.append("Will create a new commit in the repository")
        
        return effects 