"""
Tests for connection sidebar functionality.
"""

import pytest
from unittest.mock import Mock, patch, call
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QPoint
from PyQt6.QtTest import QTest

from src.app.ui.connection_sidebar import ConnectionSidebar
from src.app.core.session_manager import Session, SessionManager
from src.app.core.ssh_connection import SSHConnection, SSHCredentials

# Required for Qt widgets
app = QApplication([])

class SignalSpy(QObject):
    """Helper class to spy on Qt signals."""
    signal = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.args = None
        self.signal.connect(self._slot)
    
    def _slot(self, *args):
        """Store signal arguments."""
        self.args = args[0] if len(args) == 1 else args
    
    def was_called(self):
        """Check if signal was emitted."""
        return self.args is not None

@pytest.fixture
def mock_session_manager():
    """Create mock session manager."""
    return Mock(spec=SessionManager)

@pytest.fixture
def mock_session():
    """Create mock session."""
    mock_conn = Mock(spec=SSHConnection)
    mock_conn.credentials = SSHCredentials(
        username="testuser",
        password="testpass",
        hostname="test.host",
        port=22
    )
    return Mock(spec=Session, connection=mock_conn)

@pytest.fixture
def sidebar(mock_session_manager):
    """Create connection sidebar for testing."""
    return ConnectionSidebar(mock_session_manager)

def test_sidebar_initialization(sidebar):
    """Test sidebar initialization."""
    # Check minimum width
    assert sidebar.minimumWidth() == 250
    
    # Check tree widget
    assert sidebar.connection_tree is not None
    assert sidebar.connection_tree.isHeaderHidden()
    
    # Check root items
    assert sidebar.active_root is not None
    assert sidebar.saved_root is not None
    assert sidebar.active_root.text(0) == "Active Sessions"
    assert sidebar.saved_root.text(0) == "Saved Connections"
    
    # Check roots are expanded
    assert sidebar.active_root.isExpanded()
    assert sidebar.saved_root.isExpanded()

def test_add_session(sidebar, mock_session):
    """Test adding active session."""
    sidebar.add_session(mock_session)
    
    # Check session was added
    assert sidebar.active_root.childCount() == 1
    item = sidebar.active_root.child(0)
    assert item.text(0) == "testuser@test.host"
    assert item.data(0, Qt.ItemDataRole.UserRole) == mock_session

def test_remove_session(sidebar, mock_session):
    """Test removing active session."""
    # Add session first
    sidebar.add_session(mock_session)
    assert sidebar.active_root.childCount() == 1
    
    # Remove session
    sidebar.remove_session(mock_session)
    assert sidebar.active_root.childCount() == 0

def test_add_saved_connection(sidebar):
    """Test adding saved connection."""
    sidebar.add_saved_connection(
        name="Test Server",
        hostname="test.host",
        username="testuser"
    )
    
    # Check connection was added
    assert sidebar.saved_root.childCount() == 1
    item = sidebar.saved_root.child(0)
    assert item.text(0) == "Test Server"
    assert item.toolTip(0) == "testuser@test.host"

def test_session_selection(sidebar, mock_session):
    """Test session selection signal."""
    # Add session
    sidebar.add_session(mock_session)
    item = sidebar.active_root.child(0)
    
    # Create signal spy
    spy = SignalSpy()
    sidebar.session_selected.connect(spy.signal)
    
    # Double click item
    sidebar.connection_tree.itemDoubleClicked.emit(item, 0)
    
    # Process events to ensure signal is delivered
    QApplication.processEvents()
    
    # Check signal was emitted
    assert spy.was_called()
    assert spy.args == mock_session

def test_session_disconnect(sidebar, mock_session, mock_session_manager):
    """Test session disconnection."""
    # Add session
    sidebar.add_session(mock_session)
    item = sidebar.active_root.child(0)
    
    # Create signal spy
    spy = SignalSpy()
    sidebar.session_closed.connect(spy.signal)
    
    # Call disconnect
    sidebar._disconnect_session(mock_session)
    
    # Process events to ensure signal is delivered
    QApplication.processEvents()
    
    # Check signal was emitted
    assert spy.was_called()
    assert spy.args == mock_session
    
    # Check session was ended
    mock_session_manager.end_session.assert_called_once_with(
        "test.host",
        "testuser"
    )
    
    # Check item was removed
    assert sidebar.active_root.childCount() == 0

def test_context_menu_active_session(sidebar, mock_session):
    """Test context menu for active session."""
    # Add session
    sidebar.add_session(mock_session)
    item = sidebar.active_root.child(0)
    
    # Create mock menu and action
    mock_action = Mock()
    mock_menu = Mock(spec=QMenu)
    mock_menu.addAction.return_value = mock_action
    mock_menu.exec.return_value = None
    
    with patch('src.app.ui.connection_sidebar.QMenu', return_value=mock_menu) as mock_menu_cls:
        # Show context menu
        pos = sidebar.connection_tree.visualItemRect(item).center()
        sidebar._show_context_menu(pos)
        
        # Check menu was created with parent
        mock_menu_cls.assert_called_once_with(sidebar)
        
        # Check disconnect action was added
        mock_menu.addAction.assert_called_once_with("Disconnect")
        
        # Check menu was shown
        mock_menu.exec.assert_called_once()

def test_context_menu_saved_connection(sidebar):
    """Test context menu for saved connection."""
    # Add saved connection
    sidebar.add_saved_connection("Test Server", "test.host", "testuser")
    item = sidebar.saved_root.child(0)
    
    # Create mock menu and actions
    mock_menu = Mock(spec=QMenu)
    mock_menu.exec.return_value = None
    
    with patch('src.app.ui.connection_sidebar.QMenu', return_value=mock_menu) as mock_menu_cls:
        # Show context menu
        pos = sidebar.connection_tree.visualItemRect(item).center()
        sidebar._show_context_menu(pos)
        
        # Check menu was created with parent
        mock_menu_cls.assert_called_once_with(sidebar)
        
        # Check actions were added in order
        assert len(mock_menu.mock_calls) == 5  # Two addAction calls, two signal connections, and exec
        assert mock_menu.mock_calls[0] == call.addAction("Connect")
        assert mock_menu.mock_calls[2] == call.addAction("Delete")
        assert str(mock_menu.mock_calls[-1]).startswith("call.exec(") 