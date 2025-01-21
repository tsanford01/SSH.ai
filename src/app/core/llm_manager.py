"""
Local LLM manager for SSH assistance.
"""

import os
import psutil
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
import sys
import subprocess
from openai import OpenAI
import requests
import time
import json
import threading

from .prompt_templates import PromptTemplate, PromptType, Context
from .command_parser import CommandParser, ParsedCommand
from .command_history import CommandHistory, CommandPattern

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration for LLM usage."""
    max_memory_mb: int = 4096  # Increased to match test configuration
    max_cpu_percent: int = 50   # Keep moderate CPU usage
    context_length: int = 4096  # Increased from 1024 for better performance
    temperature: float = 0.7    # Keep default temperature
    use_gpu: bool = True        # Keep GPU enabled
    gpu_layers: int = 9999      # Full GPU layer offloading
    batch_size: int = 512       # Keep optimal batch size
    threads: Optional[int] = None  # Will be set to (cpu_count - 1) in __init__

class LLMManager:
    """Manages local LLM interactions using llamafile."""
    
    def __init__(self) -> None:
        """Initialize the LLM manager."""
        self.base_url = "http://127.0.0.1:8080"
        self.client = None
        self.llamafile_path = Path("models/llava-v1.5-7b-q4.exe") if os.name == 'nt' else Path("models/llava-v1.5-7b-q4.llamafile")
        self.process = None
        self.logger = logging.getLogger(__name__)
        self.server_ready = False
        self._process = psutil.Process(os.getpid())
        self._command_history = CommandHistory()
        self._system_info: Dict[str, Any] = {
            "os": os.name,
            "platform": sys.platform,
            "python_version": sys.version,
            "cpu_count": os.cpu_count() or 1
        }
        self._connection_state: Dict[str, Any] = {}
        self.config = LLMConfig()
        self._command_parser = CommandParser()
        
        # Check GPU support and optimize settings
        self.gpu_info = self._check_gpu_support()
        if self.gpu_info["available"]:
            self.config.gpu_layers = self._optimize_gpu_layers(self.gpu_info)
        
        # Set optimal thread count if not specified
        if self.config.threads is None:
            self.config.threads = max(1, (os.cpu_count() or 2) - 1)  # Leave one core free
        
        # Check GPU support on initialization
        self.gpu_available = self._check_gpu_support()
        if self.config.use_gpu and not self.gpu_available:
            self.logger.warning(
                "GPU acceleration requested but no GPU support detected. "
                "Falling back to CPU-only mode."
            )
    
    def _check_gpu_support(self) -> Dict[str, Any]:
        """
        Check if GPU acceleration is available and get GPU capabilities.
        
        Returns:
            Dict with keys:
                available (bool): True if GPU support is available
                type (str): 'cuda' or 'rocm' or 'none'
                memory_mb (int): Available GPU memory in MB
                compute_capability (Optional[str]): CUDA compute capability if available
        """
        result = {
            "available": False,
            "type": "none",
            "memory_mb": 0,
            "compute_capability": None
        }

        # Check CUDA libraries
        cuda_libs = [
            "libcuda.so", "libcuda.so.1",  # Linux
            "nvcuda.dll",                   # Windows
            "libcuda.dylib"                 # MacOS
        ]
        
        cuda_paths = [
            os.environ.get("CUDA_PATH", ""),
            "/usr/local/cuda",
            "/opt/cuda",
            "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA",
            "/usr/lib64",
            "/usr/lib",
            "C:\\Windows\\System32"
        ]

        # Check for CUDA
        for path in cuda_paths:
            if not path:
                continue
            
            # Check for NVCC compiler
            nvcc_path = Path(path) / "bin" / ("nvcc.exe" if os.name == 'nt' else "nvcc")
            if nvcc_path.exists():
                # Try to get GPU info using nvidia-smi
                try:
                    nvidia_smi = subprocess.run(
                        ["nvidia-smi", "--query-gpu=memory.total,compute_cap", "--format=csv,noheader,nounits"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    if nvidia_smi.returncode == 0:
                        memory, compute_cap = nvidia_smi.stdout.strip().split(",")
                        result.update({
                            "available": True,
                            "type": "cuda",
                            "memory_mb": int(float(memory.strip())),
                            "compute_capability": compute_cap.strip()
                        })
                        self.logger.info(f"CUDA support detected: {result['memory_mb']}MB, Compute {result['compute_capability']}")
                        return result
                except (subprocess.SubprocessError, ValueError):
                    pass

            # Check for CUDA libraries
            for lib in cuda_libs:
                lib_path = Path(path) / lib
                if lib_path.exists():
                    result.update({
                        "available": True,
                        "type": "cuda",
                        "memory_mb": 4096  # Default assumption if nvidia-smi fails
                    })
                    self.logger.info("CUDA libraries detected")
                    return result

        # Check for ROCm
        rocm_libs = [
            "librocm_smi64.so", "libhip_hcc.so",  # Linux
            "rocm_smi64.dll",                      # Windows
        ]
        
        rocm_paths = [
            os.environ.get("HIP_PATH", ""),
            "/opt/rocm",
            "C:\\Program Files\\AMD\\ROCm",
            "/usr/lib64",
            "/usr/lib",
            "C:\\Windows\\System32"
        ]

        for path in rocm_paths:
            if not path:
                continue
            
            # Check for ROCm compiler
            compiler_path = Path(path) / "bin" / ("amdclang++.exe" if os.name == 'nt' else "amdclang++")
            if compiler_path.exists():
                # Try to get GPU info using rocm-smi
                try:
                    rocm_smi = subprocess.run(
                        ["rocm-smi", "--showmeminfo", "vram"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    if rocm_smi.returncode == 0:
                        # Parse memory info from rocm-smi output
                        memory_line = [line for line in rocm_smi.stdout.split('\n') if 'Total' in line]
                        if memory_line:
                            memory = int(memory_line[0].split()[-1])
                            result.update({
                                "available": True,
                                "type": "rocm",
                                "memory_mb": memory
                            })
                            self.logger.info(f"ROCm support detected: {memory}MB")
                            return result
                except (subprocess.SubprocessError, ValueError):
                    pass

            # Check for ROCm libraries
            for lib in rocm_libs:
                lib_path = Path(path) / lib
                if lib_path.exists():
                    result.update({
                        "available": True,
                        "type": "rocm",
                        "memory_mb": 4096  # Default assumption if rocm-smi fails
                    })
                    self.logger.info("ROCm libraries detected")
                    return result

        self.logger.warning("No GPU support detected. Falling back to CPU-only mode")
        return result

    def _optimize_gpu_layers(self, gpu_info: Dict[str, Any]) -> int:
        """
        Optimize number of GPU layers based on available memory.
        
        Args:
            gpu_info: GPU information from _check_gpu_support
            
        Returns:
            int: Recommended number of layers to offload to GPU
        """
        if not gpu_info["available"]:
            return 0
            
        # Model size approximation (7B parameters)
        model_size_mb = 3800  # ~3.8GB for 7B model
        
        # Reserve 20% of GPU memory for overhead
        available_memory = gpu_info["memory_mb"] * 0.8
        
        # Calculate maximum layers based on memory
        max_layers = int((available_memory / model_size_mb) * 32)  # 32 is total layers
        
        # Ensure at least 1 layer if GPU is available
        return max(1, min(max_layers, 9999))

    def _monitor_output(self, pipe, prefix=''):
        """Monitor subprocess output in a separate thread."""
        for line in iter(pipe.readline, ''):
            print(f"{prefix}{line.strip()}")
            if "error" in line.lower():
                print(f"Error detected: {line.strip()}")
            if "listening" in line.lower():
                print("Server is listening for connections")
                self.server_ready = True

    def start_server(self, no_browser: bool = False) -> bool:
        """
        Start the LLM server.
        
        Args:
            no_browser: If True, prevents browser from opening automatically
        
        Returns:
            bool: True if server started successfully
        """
        if not self.llamafile_path.exists():
            self.logger.error(f"Model file not found: {self.llamafile_path}")
            return False
            
        # Build command with optimizations
        cmd = [
            str(self.llamafile_path),
            "-c", str(self.config.context_length),
            "-t", str(self.config.threads),
            "-b", str(self.config.batch_size),
            "--port", "8080",
            "--host", "127.0.0.1",
            "--nobrowser"  # Always prevent browser from opening
        ]
        
        # Add GPU settings only if GPU is available
        if self.config.use_gpu and self.gpu_info["available"]:
            cmd.extend(["-ngl", str(self.config.gpu_layers)])
            if self.gpu_info["type"] == "cuda":
                cmd.append("--cuda")
            elif self.gpu_info["type"] == "rocm":
                cmd.append("--rocm")
        elif self.config.use_gpu:
            self.logger.warning("GPU acceleration requested but no GPU support detected. Using CPU-only mode")
        
        try:
            # Start server process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Monitor output in separate threads
            threading.Thread(
                target=self._monitor_output,
                args=(self.process.stdout, "OUT: "),
                daemon=True
            ).start()
            
            threading.Thread(
                target=self._monitor_output,
                args=(self.process.stderr, "ERR: "),
                daemon=True
            ).start()
            
            # Wait for server to be ready
            start_time = time.time()
            while not self.server_ready and time.time() - start_time < 30:
                if self.process.poll() is not None:
                    error_output = self.process.stderr.read() if self.process.stderr else "No error output available"
                    self.logger.error(f"Server process terminated unexpectedly. Error: {error_output}")
                    return False
                time.sleep(0.1)
            
            if not self.server_ready:
                self.logger.error("Server failed to start within timeout")
                self.stop_server()
                return False
            
            # Initialize OpenAI client
            self.client = OpenAI(
                base_url=f"{self.base_url}/v1",
                api_key="not-needed"
            )
            
            # Log final configuration
            self.logger.info(f"Server started successfully with configuration:")
            self.logger.info(f"  GPU: {self.gpu_info['type'].upper() if self.gpu_info['available'] else 'Disabled'}")
            if self.gpu_info['available']:
                self.logger.info(f"  GPU Memory: {self.gpu_info['memory_mb']}MB")
                self.logger.info(f"  GPU Layers: {self.config.gpu_layers}")
                if self.gpu_info['compute_capability']:
                    self.logger.info(f"  Compute Capability: {self.gpu_info['compute_capability']}")
            self.logger.info(f"  Threads: {self.config.threads}")
            self.logger.info(f"  Batch Size: {self.config.batch_size}")
            self.logger.info(f"  Context Length: {self.config.context_length}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test if the LLM server is responding."""
        if not self.server_ready:
            return False
            
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"Health check response: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"Health data: {health_data}")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Connection test error: {e}")
            return False

    async def get_intelligent_suggestions(
        self,
        partial_command: Optional[str] = None,
        working_dir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """
        Get intelligent command suggestions based on history and context.
        
        Args:
            partial_command: Partial command to get suggestions for
            working_dir: Current working directory
            environment: Current environment variables
            
        Returns:
            List of suggestions, each containing:
                command: The suggested command
                description: Why this command is suggested
                confidence: Confidence score (0-1)
        """
        suggestions = []
        
        # Get history-based suggestions
        if partial_command:
            history_suggestions = self._command_history.get_command_suggestions(partial_command)
            for cmd in history_suggestions:
                pattern = self._command_history.get_command_patterns(cmd)
                if pattern:
                    suggestions.append({
                        "command": cmd,
                        "description": f"Used {pattern.frequency} times with {pattern.success_rate:.0%} success rate",
                        "confidence": min(0.9, (pattern.success_rate * pattern.frequency / 10))
                    })
        
        # Get context-based suggestions
        recent_commands = list(self._command_history._history.keys())[-5:]
        if recent_commands:
            analysis = self._command_history.analyze_command_sequence(recent_commands)
            for suggestion in analysis['suggestions']:
                if suggestion not in [s['command'] for s in suggestions]:
                    pattern = self._command_history.get_command_patterns(suggestion)
                    if pattern:
                        suggestions.append({
                            "command": suggestion,
                            "description": f"Frequently follows your recent commands",
                            "confidence": 0.7
                        })
        
        # Get LLM-based suggestions if server is ready
        if self.server_ready and (partial_command or working_dir):
            context = f"Current directory: {working_dir or 'unknown'}\n"
            if recent_commands:
                context += f"Recent commands: {', '.join(recent_commands)}\n"
            if partial_command:
                context += f"Partial command: {partial_command}"
            
            try:
                llm_suggestion = await self.get_command_suggestion(context)
                if llm_suggestion and not llm_suggestion.startswith("Error"):
                    suggestions.append({
                        "command": llm_suggestion,
                        "description": "AI suggested based on your context",
                        "confidence": 0.8
                    })
            except Exception as e:
                self.logger.warning(f"Failed to get LLM suggestion: {e}")
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Remove duplicates, keeping highest confidence
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s['command'] not in seen:
                seen.add(s['command'])
                unique_suggestions.append(s)
        
        return unique_suggestions[:5]  # Return top 5 suggestions

    async def get_command_suggestion(self, context: str) -> str:
        """Get command suggestions based on context."""
        if not self.server_ready:
            return "Error: Server not ready"
            
        try:
            # Create a focused prompt for command generation
            prompt = """You are a command line expert. Respond with ONLY the exact command, no explanation.

Examples:
Q: What command to list all files with details?
A: ls -la

Q: What command to show current directory?
A: pwd

Q: What command to create a new directory?
A: mkdir newfolder

Context:
{context}

Suggest a relevant command:"""
            
            response = requests.post(
                f"{self.base_url}/completion",
                json={
                    "prompt": prompt.format(context=context),
                    "n_predict": 10,
                    "temperature": 0.1,
                    "top_k": 5,
                    "top_p": 0.9,
                    "stop": ["\n", "Q:", "A:", "</s>", "OUT:", "{"],
                    "repeat_penalty": 1.1,
                    "presence_penalty": 0.1,
                    "frequency_penalty": 0.1,
                    "cache_prompt": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                command = result.get("content", "").strip()
                
                # More aggressive cleanup
                command = command.split('\n')[0]  # Take only first line
                command = command.split('OUT:')[0]  # Remove OUT: messages
                command = command.split('{')[0]  # Remove JSON output
                command = command.strip('`').strip()  # Remove backticks and whitespace
                
                # Remove any remaining JSON or log artifacts
                command = ''.join(c for c in command if not any(x in c for x in ['{', '}', '"']))
                
                if len(command) > 0 and not any(x in command for x in ["Error", "Sorry", "I apologize"]):
                    return command
                
                return "Error: Invalid command generated"
            else:
                return f"Error: Server returned {response.status_code}"
            
        except Exception as e:
            return f"Error: {str(e)}"

    def stop_server(self) -> None:
        """Stop the llamafile server."""
        if self.process:
            self.process.terminate()
            self.process = None
            self.server_ready = False
            self.client = None
            print("Server stopped")

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.stop_server()

    def analyze_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze command with context awareness.
        
        Args:
            command: Command to analyze
            working_dir: Current working directory
            environment: Current environment variables
            
        Returns:
            Analysis results including suggestions and risks
            
        Raises:
            RuntimeError: If analysis fails
        """
        try:
            # Parse command
            parsed = self._command_parser.parse_command(
                command,
                working_dir=working_dir,
                environment=environment
            )
            
            # Get command type and context requirements
            cmd_type = self._command_parser.get_command_type(parsed)
            context = self._command_parser.get_context_requirements(parsed)
            
            # Analyze risks
            risks = self._command_parser.analyze_risk(parsed)
            
            # Get command patterns from history
            patterns = self._command_history.get_command_patterns(command)
            
            # Build analysis context
            analysis_context = self._build_analysis_context(
                parsed,
                context,
                patterns
            )
            
            # Generate LLM prompt
            prompt = self._build_command_prompt(
                parsed,
                cmd_type,
                risks,
                analysis_context,
                patterns
            )
            
            # Get LLM response
            response = self._generate_response(prompt)
            
            return {
                'command': parsed,
                'type': cmd_type,
                'risks': risks,
                'suggestions': response,
                'context': analysis_context,
                'patterns': patterns
            }
            
        except Exception as e:
            self.logger.error(f"Command analysis failed: {e}")
            raise RuntimeError(f"Failed to analyze command: {e}") from e
    
    def _build_analysis_context(
        self,
        command: ParsedCommand,
        context_requirements: Dict[str, bool],
        patterns: Optional[CommandPattern] = None
    ) -> Dict[str, Any]:
        """
        Build context information for command analysis.
        
        Args:
            command: Parsed command
            context_requirements: Required context flags
            patterns: Command patterns from history
            
        Returns:
            Context information dictionary
        """
        context = {}
        
        # Add working directory context if required
        if context_requirements['working_dir']:
            context['working_dir'] = command.working_dir or self._connection_state.get('cwd')
        
        # Add environment variables if required
        if context_requirements['env_vars']:
            context['environment'] = {
                **self._connection_state.get('env', {}),
                **(command.environment or {})
            }
        
        # Add command history context
        context['recent_commands'] = self._command_history[-5:] if self._command_history else []
        
        # Add connection state
        context['connection'] = {
            'hostname': self._connection_state.get('hostname'),
            'username': self._connection_state.get('username'),
            'connected': self._connection_state.get('connected', False)
        }
        
        # Add pattern information if available
        if patterns:
            context['patterns'] = {
                'frequency': patterns.frequency,
                'success_rate': patterns.success_rate,
                'avg_duration': patterns.avg_duration,
                'common_args': patterns.common_args,
                'common_flags': patterns.common_flags,
                'related_commands': patterns.related_commands
            }
        
        return context
    
    def _build_command_prompt(
        self,
        command: ParsedCommand,
        cmd_type: str,
        risks: Dict[str, Any],
        context: Dict[str, Any],
        patterns: Optional[CommandPattern] = None
    ) -> str:
        """
        Build prompt for LLM analysis.
        
        Args:
            command: Parsed command
            cmd_type: Command type
            risks: Risk analysis results
            context: Command context
            patterns: Command patterns from history
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"Analyze the following command: {command.raw_command}\n",
            f"Command type: {cmd_type}\n",
            "\nContext:",
            f"- Working directory: {context.get('working_dir', 'unknown')}",
            f"- Recent commands: {', '.join(context.get('recent_commands', []))}"
        ]
        
        # Add risk information
        if risks['level'] != 'low':
            prompt_parts.extend([
                "\nRisk Analysis:",
                f"- Risk level: {risks['level']}",
                f"- Risk factors: {', '.join(risks['factors'])}"
            ])
        
        # Add pattern information if available
        if patterns:
            prompt_parts.extend([
                "\nCommand History Analysis:",
                f"- Usage frequency: {patterns.frequency} times",
                f"- Success rate: {patterns.success_rate:.1%}",
                f"- Average duration: {patterns.avg_duration:.2f}s",
                f"- Common arguments: {', '.join(patterns.common_args)}",
                f"- Related commands: {', '.join(patterns.related_commands)}"
            ])
        
        # Add specific prompts based on command type
        if cmd_type == 'file_operation':
            prompt_parts.append("\nAnalyze file operation safety and efficiency")
        elif cmd_type == 'system_operation':
            prompt_parts.append("\nCheck system impact and resource usage")
        elif cmd_type == 'network_operation':
            prompt_parts.append("\nVerify network security and performance")
        
        return "\n".join(prompt_parts)
    
    def analyze_error(self, error: str, command: Optional[str] = None) -> str:
        """
        Analyze an SSH error.
        
        Args:
            error: Error message to analyze
            command: Related command that caused the error
            
        Returns:
            Error analysis and solutions
        """
        context = Context(
            command_history=self._command_history,
            current_command=command,
            error_message=error,
            system_info=self._system_info,
            connection_state=self._connection_state
        )
        
        prompt = PromptTemplate.generate(PromptType.ERROR_ANALYSIS, context)
        return self._generate_response(prompt)
    
    def check_security(self, command: Optional[str] = None) -> str:
        """
        Perform security analysis.
        
        Args:
            command: Command to analyze for security
            
        Returns:
            Security analysis and recommendations
        """
        context = Context(
            command_history=self._command_history,
            current_command=command,
            system_info=self._system_info,
            connection_state=self._connection_state
        )
        
        prompt = PromptTemplate.generate(PromptType.SECURITY_CHECK, context)
        return self._generate_response(prompt)
    
    def optimize_performance(self) -> str:
        """
        Analyze and suggest performance optimizations.
        
        Returns:
            Performance analysis and recommendations
        """
        context = Context(
            command_history=self._command_history,
            system_info=self._system_info,
            connection_state=self._connection_state
        )
        
        prompt = PromptTemplate.generate(PromptType.PERFORMANCE_OPTIMIZATION, context)
        return self._generate_response(prompt)
    
    def diagnose_connection(self, error: Optional[str] = None) -> str:
        """
        Diagnose connection issues.
        
        Args:
            error: Connection error message if any
            
        Returns:
            Connection diagnosis and solutions
        """
        context = Context(
            command_history=self._command_history,
            error_message=error,
            system_info=self._system_info,
            connection_state=self._connection_state
        )
        
        prompt = PromptTemplate.generate(PromptType.CONNECTION_ISSUE, context)
        return self._generate_response(prompt)
    
    def update_connection_state(self, state: Dict[str, Any]) -> None:
        """
        Update SSH connection state.
        
        Args:
            state: New connection state information
        """
        self._connection_state.update(state)
    
    def add_command(self, command: str) -> None:
        """
        Add command to history.
        
        Args:
            command: Command to add to history
        """
        self._command_history.add_command(command)
        # Keep only last 100 commands
        if len(self._command_history) > 100:
            self._command_history = self._command_history[-100:]
    
    def _generate_response(self, prompt: str) -> str:
        """
        Generate response from the model.
        
        Args:
            prompt: Input prompt for the model
            
        Returns:
            Generated response text
            
        Raises:
            RuntimeError: If generation fails
        """
        # Check system resources
        if not self._check_resources():
            raise RuntimeError(
                f"Insufficient system resources. Need at least "
                f"{self.config.max_memory_mb}MB RAM and "
                f"{self.config.max_cpu_percent}% CPU available."
            )
        
        try:
            # For now, return a simple response
            # This will be replaced with actual LLM integration
            return "I understand your SSH command. Let me help you with that."
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise RuntimeError(f"Failed to generate response: {e}") from e
    
    def _check_resources(self) -> bool:
        """
        Check if system has sufficient resources.
        
        Returns:
            True if resources are sufficient, False otherwise
        """
        # Check available memory
        memory = psutil.virtual_memory()
        memory_available_mb = memory.available / (1024 * 1024)
        if memory_available_mb < self.config.max_memory_mb:
            logger.warning(
                f"Insufficient memory: {memory_available_mb:.0f}MB available, "
                f"need {self.config.max_memory_mb}MB"
            )
            return False
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > (100 - self.config.max_cpu_percent):
            logger.warning(
                f"High CPU usage: {cpu_percent:.0f}% used, "
                f"need {self.config.max_cpu_percent}% available"
            )
            return False
        
        return True

    def record_command_execution(
        self,
        command: str,
        exit_code: int,
        duration: float,
        working_dir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record command execution in history.
        
        Args:
            command: Executed command
            exit_code: Command exit code
            duration: Execution duration in seconds
            working_dir: Working directory
            environment: Environment variables
        """
        self._command_history.add_command(
            command,
            exit_code,
            duration,
            working_dir,
            environment
        ) 