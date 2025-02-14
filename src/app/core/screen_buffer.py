"""
Screen buffer and cursor management for terminal emulation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from .ansi_parser import TextStyle

@dataclass
class Cell:
    """A single character cell in the screen buffer."""
    char: str = " "
    style: TextStyle = field(default_factory=TextStyle)

class ScreenBuffer:
    """Manages terminal screen content and cursor operations."""
    
    def __init__(self, rows: int = 24, cols: int = 80):
        """
        Initialize screen buffer.
        
        Args:
            rows: Number of rows in the buffer
            cols: Number of columns in the buffer
        """
        self.rows = rows
        self.cols = cols
        self.cursor_x = 0
        self.cursor_y = 0
        self.saved_cursor: Optional[Tuple[int, int]] = None
        self.current_style = TextStyle()
        
        # Initialize buffer with empty cells
        self.buffer: List[List[Cell]] = [
            [Cell() for _ in range(cols)] for _ in range(rows)
        ]
        
        # Scroll region (default to entire screen)
        self.scroll_top = 0
        self.scroll_bottom = rows - 1
    
    def resize(self, new_rows: int, new_cols: int) -> None:
        """
        Resize the screen buffer.
        
        Args:
            new_rows: New number of rows
            new_cols: New number of columns
        """
        # Create new buffer with new dimensions
        new_buffer = [
            [Cell() for _ in range(new_cols)] for _ in range(new_rows)
        ]
        
        # Copy existing content
        for y in range(min(new_rows, self.rows)):
            for x in range(min(new_cols, self.cols)):
                new_buffer[y][x] = self.buffer[y][x]
        
        self.buffer = new_buffer
        self.rows = new_rows
        self.cols = new_cols
        
        # Adjust cursor position if needed
        self.cursor_x = min(self.cursor_x, new_cols - 1)
        self.cursor_y = min(self.cursor_y, new_rows - 1)
        
        # Adjust scroll region
        self.scroll_bottom = min(self.scroll_bottom, new_rows - 1)
    
    def write(self, text: str) -> None:
        """
        Write text at current cursor position.
        
        Args:
            text: Text to write
        """
        for char in text:
            if char == '\n':
                self._new_line()
            elif char == '\r':
                self.cursor_x = 0
            elif char == '\b':
                self.cursor_x = max(0, self.cursor_x - 1)
            elif char == '\t':
                # Move to next tab stop (every 8 columns)
                self.cursor_x = (self.cursor_x + 8) & ~7
                if self.cursor_x >= self.cols:
                    self._new_line()
            else:
                if self.cursor_x >= self.cols:
                    self._new_line()
                
                self.buffer[self.cursor_y][self.cursor_x] = Cell(
                    char=char,
                    style=self.current_style
                )
                self.cursor_x += 1
    
    def _new_line(self) -> None:
        """Handle new line: move cursor down and scroll if needed."""
        self.cursor_x = 0
        if self.cursor_y == self.scroll_bottom:
            self._scroll_up()
        else:
            self.cursor_y = min(self.cursor_y + 1, self.rows - 1)
    
    def _scroll_up(self) -> None:
        """Scroll the scroll region up one line."""
        # Move lines up
        for y in range(self.scroll_top, self.scroll_bottom):
            self.buffer[y] = self.buffer[y + 1]
        
        # Clear bottom line
        self.buffer[self.scroll_bottom] = [
            Cell() for _ in range(self.cols)
        ]
    
    def _scroll_down(self) -> None:
        """Scroll the scroll region down one line."""
        # Move lines down
        for y in range(self.scroll_bottom, self.scroll_top, -1):
            self.buffer[y] = self.buffer[y - 1]
        
        # Clear top line
        self.buffer[self.scroll_top] = [
            Cell() for _ in range(self.cols)
        ]
    
    def move_to(self, x: int, y: int) -> None:
        """
        Move cursor to absolute position.
        
        Args:
            x: Column (0-based)
            y: Row (0-based)
        """
        self.cursor_x = max(0, min(x, self.cols - 1))
        self.cursor_y = max(0, min(y, self.rows - 1))
    
    def move_relative(self, dx: int, dy: int) -> None:
        """
        Move cursor relative to current position.
        
        Args:
            dx: Horizontal movement (positive = right)
            dy: Vertical movement (positive = down)
        """
        self.move_to(self.cursor_x + dx, self.cursor_y + dy)
    
    def save_cursor(self) -> None:
        """Save current cursor position."""
        self.saved_cursor = (self.cursor_x, self.cursor_y)
    
    def restore_cursor(self) -> None:
        """Restore saved cursor position."""
        if self.saved_cursor:
            self.cursor_x, self.cursor_y = self.saved_cursor
    
    def set_scroll_region(self, top: int, bottom: int) -> None:
        """
        Set the scrolling region.
        
        Args:
            top: Top line number (0-based)
            bottom: Bottom line number (0-based)
        """
        if 0 <= top < bottom < self.rows:
            self.scroll_top = top
            self.scroll_bottom = bottom
    
    def clear_line(self, mode: int = 0) -> None:
        """
        Clear current line.
        
        Args:
            mode: 0=cursor to end, 1=start to cursor, 2=entire line
        """
        if mode == 0:
            for x in range(self.cursor_x, self.cols):
                self.buffer[self.cursor_y][x] = Cell()
        elif mode == 1:
            for x in range(self.cursor_x + 1):
                self.buffer[self.cursor_y][x] = Cell()
        elif mode == 2:
            self.buffer[self.cursor_y] = [Cell() for _ in range(self.cols)]
    
    def clear_screen(self, mode: int = 0) -> None:
        """
        Clear screen.
        
        Args:
            mode: 0=cursor to end, 1=start to cursor, 2=entire screen
        """
        if mode == 0:
            # Clear from cursor to end of screen
            self.clear_line(0)
            for y in range(self.cursor_y + 1, self.rows):
                self.buffer[y] = [Cell() for _ in range(self.cols)]
        elif mode == 1:
            # Clear from start to cursor
            self.clear_line(1)
            for y in range(self.cursor_y):
                self.buffer[y] = [Cell() for _ in range(self.cols)]
        elif mode == 2:
            # Clear entire screen
            self.buffer = [
                [Cell() for _ in range(self.cols)] for _ in range(self.rows)
            ] 