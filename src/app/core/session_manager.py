"""
Session manager for handling SSH sessions and LLM interactions.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path

from .ssh_connection import SSHConnection, SSHCredentials
from .llm_manager import LLMManager
from .terminal_sanitizer import TerminalSanitizer

logger = logging.getLogger(__name__)

@dataclass
class SessionSummary:
    """Summary of a session's activity."""
    
    start_time: datetime
    end_time: Optional[datetime]
    hostname: str
    username: str
    command_count: int
    error_count: int
    key_insights: List[str]
    performance_metrics: Dict[str, Any]

class Session:
    """Represents an active SSH session with associated LLM analysis."""
    
    def __init__(
        self,
        connection: SSHConnection,
        llm: LLMManager,
        session_dir: Optional[Path] = None
    ) -> None:
        """
        Initialize session.
        
        Args:
            connection: Active SSH connection
            llm: LLM manager instance
            session_dir: Directory for session storage
        """
        self.connection = connection
        self.llm = llm
        self.session_dir = session_dir or Path.home() / ".ssh_copilot" / "sessions"
        
        # Create session directory
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize session state
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.command_history: List[Dict[str, Any]] = []
        self.error_history: List[Dict[str, Any]] = []
        self.llm_interactions: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {
            "avg_response_time": 0.0,
            "error_rate": 0.0,
            "successful_suggestions": 0
        }
        
        # Initialize sanitizer
        self._sanitizer = TerminalSanitizer()
        
        logger.info(
            f"Started session for {connection.credentials.username}@"
            f"{connection.credentials.hostname}"
        )
    
    def add_command(
        self,
        command: str,
        output: str,
        exit_code: int,
        duration: float
    ) -> None:
        """
        Add executed command to history.
        
        Args:
            command: Executed command
            output: Command output
            exit_code: Command exit code
            duration: Command execution duration in seconds
        """
        # Sanitize sensitive information
        safe_output = self._sanitizer.sanitize(output)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "output": safe_output,
            "exit_code": exit_code,
            "duration": duration
        }
        
        self.command_history.append(entry)
        
        if exit_code != 0:
            self.error_history.append(entry)
        
        # Update metrics
        total_commands = len(self.command_history)
        self.performance_metrics["error_rate"] = (
            len(self.error_history) / total_commands
            if total_commands > 0 else 0.0
        )
    
    def add_llm_interaction(
        self,
        prompt: str,
        response: str,
        duration: float,
        was_helpful: bool
    ) -> None:
        """
        Add LLM interaction to history.
        
        Args:
            prompt: Input prompt
            response: LLM response
            duration: Response generation time in seconds
            was_helpful: Whether the response was helpful
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "duration": duration,
            "was_helpful": was_helpful
        }
        
        self.llm_interactions.append(entry)
        
        # Update metrics
        if was_helpful:
            self.performance_metrics["successful_suggestions"] += 1
        
        total_interactions = len(self.llm_interactions)
        total_duration = sum(
            interaction["duration"]
            for interaction in self.llm_interactions
        )
        self.performance_metrics["avg_response_time"] = (
            total_duration / total_interactions
            if total_interactions > 0 else 0.0
        )
    
    def end(self) -> None:
        """End the session and save final state."""
        self.end_time = datetime.now()
        self._save_session()
        
        logger.info(
            f"Ended session for {self.connection.credentials.username}@"
            f"{self.connection.credentials.hostname}"
        )
    
    def get_summary(self) -> SessionSummary:
        """
        Get session summary.
        
        Returns:
            Session summary object
        """
        # Generate key insights
        key_insights = self._generate_insights()
        
        return SessionSummary(
            start_time=self.start_time,
            end_time=self.end_time,
            hostname=self.connection.credentials.hostname,
            username=self.connection.credentials.username,
            command_count=len(self.command_history),
            error_count=len(self.error_history),
            key_insights=key_insights,
            performance_metrics=self.performance_metrics
        )
    
    def _generate_insights(self) -> List[str]:
        """
        Generate key insights from session history.
        
        Returns:
            List of insight strings
        """
        insights = []
        
        # Analyze command patterns
        if self.command_history:
            # Most used commands
            command_counts: Dict[str, int] = {}
            for entry in self.command_history:
                cmd = entry["command"].split()[0]  # Get base command
                command_counts[cmd] = command_counts.get(cmd, 0) + 1
            
            most_used = max(command_counts.items(), key=lambda x: x[1])
            insights.append(
                f"Most used command: '{most_used[0]}' "
                f"({most_used[1]} times)"
            )
        
        # Analyze errors
        if self.error_history:
            error_types: Dict[str, int] = {}
            for entry in self.error_history:
                # Simple error categorization
                if "permission denied" in entry["output"].lower():
                    error_type = "Permission Issues"
                elif "command not found" in entry["output"].lower():
                    error_type = "Missing Commands"
                else:
                    error_type = "Other Errors"
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            most_common_error = max(error_types.items(), key=lambda x: x[1])
            insights.append(
                f"Most common error type: {most_common_error[0]} "
                f"({most_common_error[1]} occurrences)"
            )
        
        # Analyze LLM effectiveness
        if self.llm_interactions:
            success_rate = (
                self.performance_metrics["successful_suggestions"] /
                len(self.llm_interactions)
            )
            insights.append(
                f"LLM suggestion success rate: "
                f"{success_rate:.1%}"
            )
        
        return insights
    
    def _save_session(self) -> None:
        """Save session state to disk."""
        if not self.end_time:
            return
        
        # Create session filename
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = (
            f"session_{self.connection.credentials.hostname}_"
            f"{timestamp}.json"
        )
        
        # Prepare session data
        session_data = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "hostname": self.connection.credentials.hostname,
            "username": self.connection.credentials.username,
            "command_history": self.command_history,
            "error_history": self.error_history,
            "llm_interactions": self.llm_interactions,
            "performance_metrics": self.performance_metrics,
            "summary": self._generate_insights()
        }
        
        # Save to file
        session_file = self.session_dir / filename
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"Saved session data to {session_file}")

class SessionManager:
    """Manages multiple SSH sessions."""
    
    def __init__(
        self,
        llm: LLMManager,
        session_dir: Optional[Path] = None
    ) -> None:
        """
        Initialize session manager.
        
        Args:
            llm: LLM manager instance
            session_dir: Directory for session storage
        """
        self.llm = llm
        self.session_dir = session_dir or Path.home() / ".ssh_copilot" / "sessions"
        self.active_sessions: Dict[str, Session] = {}
    
    def create_session(
        self,
        credentials: SSHCredentials
    ) -> Session:
        """
        Create new SSH session.
        
        Args:
            credentials: SSH credentials
            
        Returns:
            New session object
            
        Raises:
            RuntimeError: If session already exists
        """
        session_key = f"{credentials.username}@{credentials.hostname}"
        
        if session_key in self.active_sessions:
            raise RuntimeError(f"Session already exists for {session_key}")
        
        # Create SSH connection
        connection = SSHConnection(credentials)
        
        # Create and store session
        session = Session(connection, self.llm, self.session_dir)
        self.active_sessions[session_key] = session
        
        return session
    
    def get_session(
        self,
        hostname: str,
        username: str
    ) -> Optional[Session]:
        """
        Get active session.
        
        Args:
            hostname: SSH hostname
            username: SSH username
            
        Returns:
            Session object if found, None otherwise
        """
        session_key = f"{username}@{hostname}"
        return self.active_sessions.get(session_key)
    
    def end_session(
        self,
        hostname: str,
        username: str
    ) -> None:
        """
        End active session.
        
        Args:
            hostname: SSH hostname
            username: SSH username
        """
        session_key = f"{username}@{hostname}"
        if session := self.active_sessions.get(session_key):
            session.end()
            del self.active_sessions[session_key]
    
    def list_sessions(self) -> List[Session]:
        """
        Get list of active sessions.
        
        Returns:
            List of active session objects
        """
        return list(self.active_sessions.values())
    
    def load_session_history(
        self,
        hostname: Optional[str] = None,
        username: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Load historical session data.
        
        Args:
            hostname: Filter by hostname
            username: Filter by username
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of session data dictionaries
        """
        sessions = []
        
        # List all session files
        for session_file in self.session_dir.glob("session_*.json"):
            try:
                with open(session_file) as f:
                    session_data = json.load(f)
                
                # Apply filters
                if hostname and session_data["hostname"] != hostname:
                    continue
                    
                if username and session_data["username"] != username:
                    continue
                
                session_start = datetime.fromisoformat(
                    session_data["start_time"]
                )
                if start_date and session_start < start_date:
                    continue
                    
                if end_date and session_start > end_date:
                    continue
                
                sessions.append(session_data)
                
            except Exception as e:
                logger.error(f"Error loading session file {session_file}: {e}")
        
        return sessions 