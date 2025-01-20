"""
Connection sidebar for managing SSH sessions.
"""

from typing import Optional, cast
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QAction, QIcon

from ..core.session_manager import SessionManager, Session

class ConnectionSidebar(QWidget):
    """Sidebar for managing SSH connections."""
    
    # Signals
    session_selected = pyqtSignal(object)  # Session object
    session_closed = pyqtSignal(object)  # Session object
    
    def __init__(self, session_manager: SessionManager) -> None:
        """
        Initialize connection sidebar.
        
        Args:
            session_manager: Session manager instance
        """
        super().__init__()
        
        self.session_manager = session_manager
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add header
        header = QLabel("Connections")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            "background-color: #2b2b2b;"
            "color: white;"
            "padding: 8px;"
            "font-weight: bold;"
        )
        layout.addWidget(header)
        
        # Add new connection button
        self.new_button = QPushButton("New Connection")
        self.new_button.setStyleSheet(
            "QPushButton {"
            "   background-color: #0d6efd;"
            "   color: white;"
            "   border: none;"
            "   padding: 8px;"
            "   margin: 8px;"
            "   border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "   background-color: #0b5ed7;"
            "}"
        )
        layout.addWidget(self.new_button)
        
        # Add connection tree
        self.connection_tree = QTreeWidget()
        self.connection_tree.setHeaderHidden(True)
        self.connection_tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.connection_tree.customContextMenuRequested.connect(
            self._show_context_menu
        )
        layout.addWidget(self.connection_tree)
        
        # Create root items
        self.active_root = QTreeWidgetItem(["Active Sessions"])
        self.saved_root = QTreeWidgetItem(["Saved Connections"])
        self.connection_tree.addTopLevelItem(self.active_root)
        self.connection_tree.addTopLevelItem(self.saved_root)
        
        # Expand roots
        self.active_root.setExpanded(True)
        self.saved_root.setExpanded(True)
        
        # Set minimum width
        self.setMinimumWidth(250)
        
        # Connect signals
        self.new_button.clicked.connect(self._new_connection)
        self.connection_tree.itemDoubleClicked.connect(
            self._handle_item_double_click
        )
    
    def add_session(self, session: Session) -> None:
        """
        Add active session to tree.
        
        Args:
            session: Session to add
        """
        item = QTreeWidgetItem([
            f"{session.connection.credentials.username}@"
            f"{session.connection.credentials.hostname}"
        ])
        item.setData(0, Qt.ItemDataRole.UserRole, session)
        self.active_root.addChild(item)
    
    def remove_session(self, session: Session) -> None:
        """
        Remove session from tree.
        
        Args:
            session: Session to remove
        """
        for i in range(self.active_root.childCount()):
            item = self.active_root.child(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == session:
                self.active_root.removeChild(item)
                break
    
    def add_saved_connection(
        self,
        name: str,
        hostname: str,
        username: str
    ) -> None:
        """
        Add saved connection to tree.
        
        Args:
            name: Connection name
            hostname: SSH hostname
            username: SSH username
        """
        item = QTreeWidgetItem([name])
        item.setToolTip(0, f"{username}@{hostname}")
        self.saved_root.addChild(item)
    
    def _new_connection(self) -> None:
        """Show new connection dialog."""
        # TODO: Implement connection dialog
        pass
    
    def _handle_item_double_click(self, item: QTreeWidgetItem) -> None:
        """
        Handle double click on tree item.
        
        Args:
            item: Clicked item
        """
        # Check if active session
        session = item.data(0, Qt.ItemDataRole.UserRole)
        if session:
            self.session_selected.emit(session)
    
    def _show_context_menu(self, position: QPoint) -> None:
        """
        Show context menu for tree item.
        
        Args:
            position: Menu position
        """
        item = self.connection_tree.itemAt(position)
        if not item:
            return
            
        menu = QMenu(self)
        
        # Check if active session
        session = item.data(0, Qt.ItemDataRole.UserRole)
        if session:
            # Active session menu
            disconnect = menu.addAction("Disconnect")
            disconnect.triggered.connect(
                lambda: self._disconnect_session(session)
            )
        else:
            # Saved connection menu
            connect = menu.addAction("Connect")
            connect.triggered.connect(
                lambda: self._connect_saved(item.text(0))
            )
            
            delete = menu.addAction("Delete")
            delete.triggered.connect(
                lambda: self._delete_saved(item.text(0))
            )
        
        menu.exec(self.connection_tree.mapToGlobal(position))
    
    def _disconnect_session(self, session: Session) -> None:
        """
        Disconnect active session.
        
        Args:
            session: Session to disconnect
        """
        self.session_closed.emit(session)
        self.session_manager.end_session(
            session.connection.credentials.hostname,
            session.connection.credentials.username
        )
        self.remove_session(session)
    
    def _connect_saved(self, name: str) -> None:
        """
        Connect to saved connection.
        
        Args:
            name: Connection name
        """
        # TODO: Implement loading saved connection
        pass
    
    def _delete_saved(self, name: str) -> None:
        """
        Delete saved connection.
        
        Args:
            name: Connection name
        """
        # TODO: Implement deleting saved connection
        pass 