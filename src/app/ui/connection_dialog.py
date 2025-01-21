"""
SSH connection dialog for creating new connections.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QDialogButtonBox,
    QFileDialog,
    QMessageBox,
    QFormLayout,
)
from PyQt6.QtCore import Qt
import logging
import socket

from ..core.ssh_connection import SSHCredentials

class ConnectionDialog(QDialog):
    """Dialog for creating new SSH connections."""
    
    def __init__(self, parent=None) -> None:
        """Initialize the connection dialog."""
        super().__init__(parent)
        
        logging.info("Initializing ConnectionDialog...")
        
        self.setWindowTitle("New SSH Connection")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout for inputs
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        
        # Hostname input
        self.hostname_edit = QLineEdit()
        self.hostname_edit.setPlaceholderText("e.g., example.com or 192.168.1.100")
        form_layout.addRow("Hostname:", self.hostname_edit)
        
        # Port input
        self.port_edit = QLineEdit("22")
        self.port_edit.setMaximumWidth(100)
        form_layout.addRow("Port:", self.port_edit)
        
        # Username input
        self.username_edit = QLineEdit()
        form_layout.addRow("Username:", self.username_edit)
        
        # Password input
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_edit)
        
        # Key file input
        key_file_layout = QHBoxLayout()
        self.key_file_edit = QLineEdit()
        self.key_file_edit.setPlaceholderText("Optional SSH key file")
        self.key_file_edit.setReadOnly(True)
        key_file_layout.addWidget(self.key_file_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_key_file)
        key_file_layout.addWidget(browse_button)
        
        form_layout.addRow("SSH Key:", key_file_layout)
        
        # Error labels
        self.hostname_error = QLabel()
        self.hostname_error.setStyleSheet("color: red;")
        form_layout.addRow("", self.hostname_error)

        self.port_error = QLabel()
        self.port_error.setStyleSheet("color: red;")
        form_layout.addRow("", self.port_error)

        self.username_error = QLabel()
        self.username_error.setStyleSheet("color: red;")
        form_layout.addRow("", self.username_error)
        
        # Add form to main layout
        layout.addLayout(form_layout)
        
        # Add buttons
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox.accepted.connect(self._handle_accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)
        
        logging.info("ConnectionDialog initialized.")
    
    def _browse_key_file(self) -> None:
        """Open file dialog to select SSH key file."""
        logging.info("Browsing for SSH key file...")
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select SSH Key File",
            "",
            "All Files (*.*)"
        )
        
        if file_name:
            self.key_file_edit.setText(file_name)
            logging.info(f"Selected SSH key file: {file_name}")
    
    def _validate_input(self) -> bool:
        """
        Validate form input.
        
        Returns:
            bool: True if input is valid, False otherwise
        """
        # Check required fields
        if not self.hostname_edit.text():
            self.hostname_error.setText("Hostname cannot be empty.")
            return False
        
        if not self.username_edit.text():
            self.username_error.setText("Username cannot be empty.")
            return False
        
        # Validate port
        try:
            port = int(self.port_edit.text())
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            self.port_error.setText("Port must be a number between 1 and 65535")
            return False
        
        # Check authentication method
        if not self.password_edit.text() and not self.key_file_edit.text():
            self._show_error(
                "Either password or SSH key file must be provided"
            )
            return False
        
        return True
    
    def _show_error(self, message: str) -> None:
        """Show error message box."""
        QMessageBox.critical(self, "Input Error", message)
    
    def _handle_accept(self) -> None:
        """Handle dialog acceptance with validation."""
        # Clear previous error messages
        self.hostname_error.clear()
        self.port_error.clear()
        self.username_error.clear()

        # Validate inputs
        if not self.hostname_edit.text():
            self.hostname_error.setText("Hostname cannot be empty.")
            return
        if not self.username_edit.text():
            self.username_error.setText("Username cannot be empty.")
            return
        try:
            port = int(self.port_edit.text())
            if port <= 0 or port > 65535:
                raise ValueError("Port must be between 1 and 65535.")
        except ValueError as ve:
            self.port_error.setText(str(ve))
            return

        # Attempt to resolve hostname to check for errors
        try:
            socket.gethostbyname(self.hostname_edit.text())
        except socket.gaierror as ge:
            self.hostname_error.setText(f"Failed to resolve hostname: {ge}")
            return

        # If all validations pass, accept the dialog
        self.accept()
    
    def get_credentials(self) -> SSHCredentials:
        """
        Get SSH credentials from dialog input.
        
        Returns:
            SSHCredentials object with connection details
        """
        return SSHCredentials(
            hostname=self.hostname_edit.text(),
            port=int(self.port_edit.text()),
            username=self.username_edit.text(),
            password=self.password_edit.text() or None,
            key_filename=self.key_file_edit.text() or None
        ) 