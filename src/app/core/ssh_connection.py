"""
SSH connection management module.
"""

import os
import base64
from dataclasses import dataclass
from typing import Optional, Tuple
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import paramiko
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass

@dataclass
class SSHCredentials:
    """SSH connection credentials."""
    
    username: str
    hostname: str
    port: int = 22
    password: Optional[str] = None
    key_filename: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Encrypt sensitive data after initialization."""
        if self.password:
            # Generate random key for this instance
            self._key = get_random_bytes(32)
            cipher = AES.new(self._key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(
                self.password.encode()
            )
            # Store encrypted password
            self.password = base64.b64encode(
                cipher.nonce + tag + ciphertext
            ).decode()
    
    def get_password(self) -> Optional[str]:
        """
        Get decrypted password.
        
        Returns:
            Decrypted password or None if not set
        """
        if not self.password:
            return None
            
        # Decode and split components
        data = base64.b64decode(self.password)
        nonce = data[:16]
        tag = data[16:32]
        ciphertext = data[32:]
        
        # Decrypt
        cipher = AES.new(self._key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode()

class SSHConnection:
    """Manages SSH connection and operations."""
    
    def __init__(self, credentials: SSHCredentials) -> None:
        """
        Initialize SSH connection.
        
        Args:
            credentials: SSH credentials
        """
        self.credentials = credentials
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )
        
        # Connect using provided credentials
        connect_kwargs = {
            "username": credentials.username,
            "hostname": credentials.hostname,
            "port": credentials.port
        }
        
        if credentials.password:
            connect_kwargs["password"] = credentials.get_password()
        elif credentials.key_filename:
            connect_kwargs["key_filename"] = credentials.key_filename
        else:
            raise ValueError(
                "Either password or key_filename must be provided"
            )
        
        try:
            self.client.connect(**connect_kwargs)
            logger.info(
                f"Connected to {credentials.hostname} as {credentials.username}"
            )
        except Exception as e:
            logger.error(
                f"Failed to connect to {credentials.hostname}: {e}"
            )
            raise
    
    def execute(self, command: str) -> tuple[int, str]:
        """
        Execute command over SSH.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (exit_code, output)
        """
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            
            output = ""
            if exit_code == 0:
                output = stdout.read().decode().strip()
            else:
                output = stderr.read().decode().strip()
            
            return exit_code, output
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return 1, str(e)
    
    def close(self) -> None:
        """Close SSH connection."""
        try:
            self.client.close()
            logger.info(
                f"Closed connection to {self.credentials.hostname}"
            )
        except Exception as e:
            logger.error(
                f"Error closing connection to {self.credentials.hostname}: {e}"
            ) 