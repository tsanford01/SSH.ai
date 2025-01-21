"""
Command optimization and performance suggestions.
"""

from typing import List, Optional
from dataclasses import dataclass
from .command_history import CommandHistory

@dataclass
class OptimizationSuggestion:
    """Represents a command optimization suggestion."""
    original_command: str
    optimized_command: str
    improvement_type: str  # "performance", "safety", "readability"
    description: str
    estimated_speedup: Optional[float] = None

class CommandOptimizer:
    """Optimizes shell commands for better performance, safety, and readability."""
    
    def __init__(self, history: CommandHistory):
        self.history = history
        
    def get_optimizations(self, command: str) -> List[OptimizationSuggestion]:
        """Get optimization suggestions for a command."""
        if not command:
            raise ValueError("Empty command")
            
        suggestions = []
        cmd_parts = command.split()
        base_cmd = cmd_parts[0] if cmd_parts else ""
        
        # Safety improvements for rm
        if base_cmd == "rm":
            suggestions.append(OptimizationSuggestion(
                original_command=command,
                optimized_command=command.replace("rm", "trash-put"),
                improvement_type="safety",
                description="Use trash-put for safer deletion"
            ))
            if "-f" in command or "-rf" in command or "-fr" in command:
                suggestions.append(OptimizationSuggestion(
                    original_command=command,
                    optimized_command=command.replace("-rf", "-ri").replace("-fr", "-ri").replace("-f", "-i"),
                    improvement_type="safety",
                    description="Use interactive mode for confirmation"
                ))
                
        # Readability improvements
        flags = [f for f in cmd_parts if f.startswith('-') and len(f) == 2]
        if len(flags) > 1:
            combined = '-' + ''.join(sorted(f[1] for f in flags))
            new_cmd = f"{base_cmd} {combined} " + " ".join(p for p in cmd_parts[1:] if not p.startswith('-'))
            suggestions.append(OptimizationSuggestion(
                original_command=command,
                optimized_command=new_cmd.strip(),
                improvement_type="readability",
                description="Combine flags for better readability"
            ))
            
        # Performance optimizations
        if base_cmd == "cp" and "*.txt" in command:
            suggestions.append(OptimizationSuggestion(
                original_command=command,
                optimized_command=f"parallel cp {{}} /backup/ ::: *.txt",
                improvement_type="performance",
                description="Use parallel for faster file operations",
                estimated_speedup=2.0
            ))
        
        if command.startswith("scp") and "-C" not in command:
            suggestions.append(OptimizationSuggestion(
                original_command=command,
                optimized_command=command.replace("scp", "scp -C"),
                improvement_type="performance",
                description="Enable compression for faster network transfer",
                estimated_speedup=1.5
            ))
        
        if command.startswith("grep") and "-r" in command:
            suggestions.append(OptimizationSuggestion(
                original_command=command,
                optimized_command=command.replace("grep", "rg"),
                improvement_type="performance",
                description="Use ripgrep for faster search",
                estimated_speedup=2.0
            ))
        
        if command.startswith("git status"):
            suggestions.append(OptimizationSuggestion(
                original_command=command,
                optimized_command="git status -sb",
                improvement_type="performance",
                description="Use short format with branch info",
                estimated_speedup=1.5
            ))
            
        if command.startswith("git clone") and "--depth" not in command:
            suggestions.append(OptimizationSuggestion(
                original_command=command,
                optimized_command=command + " --depth 1",
                improvement_type="performance",
                description="Use shallow clone for faster cloning",
                estimated_speedup=1.5
            ))
            
        if command.startswith("tar") and "-czf" in command:
            suggestions.append(OptimizationSuggestion(
                original_command=command,
                optimized_command=command.replace("tar", "tar --threads=4"),
                improvement_type="performance",
                description="Use multi-threading for faster compression",
                estimated_speedup=1.5
            ))
            
        return suggestions 