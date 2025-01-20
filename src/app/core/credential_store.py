"""
Secure storage for SSH credentials.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import logging

from .ssh_connection import SSHCredentials

logger = logging.getLogger(__name__)

class CredentialStore:
    """Manages secure storage of SSH credentials."""
    
    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize credential store.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default path.
        """
        if db_path is None:
            db_path = Path.home() / ".ssh_copilot" / "credentials.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Generate or load encryption key
        self._load_or_create_key()
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS encryption_key (
                    id INTEGER PRIMARY KEY,
                    key BLOB NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    name TEXT PRIMARY KEY,
                    credentials BLOB NOT NULL
                )
            """)
            
            conn.commit()
    
    def _load_or_create_key(self) -> None:
        """Load existing encryption key or create a new one."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key FROM encryption_key WHERE id = 1")
            row = cursor.fetchone()
            
            if row is None:
                # Generate new key
                self._encryption_key = get_random_bytes(32)  # AES-256
                cursor.execute(
                    "INSERT INTO encryption_key (id, key) VALUES (1, ?)",
                    (self._encryption_key,)
                )
                conn.commit()
            else:
                self._encryption_key = row[0]
    
    def _encrypt_data(self, data: Dict) -> bytes:
        """
        Encrypt dictionary data.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Encrypted data as bytes
        """
        # Convert dict to JSON string
        json_data = json.dumps(data)
        
        # Encrypt
        cipher = AES.new(self._encryption_key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(json_data.encode())
        
        # Combine nonce, tag, and ciphertext
        encrypted = cipher.nonce + tag + ciphertext
        return encrypted
    
    def _decrypt_data(self, encrypted: bytes) -> Dict:
        """
        Decrypt data to dictionary.
        
        Args:
            encrypted: Encrypted data bytes
            
        Returns:
            Decrypted dictionary
        """
        # Split components
        nonce = encrypted[:16]
        tag = encrypted[16:32]
        ciphertext = encrypted[32:]
        
        # Decrypt
        cipher = AES.new(self._encryption_key, AES.MODE_GCM, nonce=nonce)
        json_data = cipher.decrypt_and_verify(ciphertext, tag)
        
        # Parse JSON
        return json.loads(json_data.decode())
    
    def save_credentials(self, name: str, credentials: SSHCredentials) -> None:
        """
        Save SSH credentials.
        
        Args:
            name: Profile name
            credentials: SSH credentials to save
        """
        # Convert credentials to dictionary
        creds_dict = {
            'username': credentials.username,
            'hostname': credentials.hostname,
            'port': credentials.port,
            'password': credentials.password,  # Already encrypted
            'key_filename': credentials.key_filename
        }
        
        # Encrypt credentials
        encrypted = self._encrypt_data(creds_dict)
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO profiles (name, credentials)
                VALUES (?, ?)
                """,
                (name, encrypted)
            )
            conn.commit()
            
        logger.info(f"Saved credentials for profile '{name}'")
    
    def get_credentials(self, name: str) -> Optional[SSHCredentials]:
        """
        Get SSH credentials by profile name.
        
        Args:
            name: Profile name
            
        Returns:
            SSHCredentials if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT credentials FROM profiles WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # Decrypt credentials
            creds_dict = self._decrypt_data(row[0])
            
            # Create SSHCredentials object
            return SSHCredentials(
                username=creds_dict['username'],
                hostname=creds_dict['hostname'],
                port=creds_dict['port'],
                password=creds_dict['password'],
                key_filename=creds_dict['key_filename']
            )
    
    def list_profiles(self) -> List[str]:
        """
        Get list of saved profile names.
        
        Returns:
            List of profile names
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM profiles")
            return [row[0] for row in cursor.fetchall()]
    
    def delete_profile(self, name: str) -> None:
        """
        Delete a profile.
        
        Args:
            name: Profile name to delete
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM profiles WHERE name = ?", (name,))
            conn.commit()
            
        logger.info(f"Deleted profile '{name}'") 