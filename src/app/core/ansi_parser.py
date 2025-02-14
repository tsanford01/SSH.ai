"""
ANSI escape sequence parser for terminal emulation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import re
from copy import deepcopy

@dataclass
class TextStyle:
    """Text style attributes."""
    foreground: Optional[str] = None
    background: Optional[str] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    reverse: bool = False

    def __eq__(self, other):
        if not isinstance(other, TextStyle):
            return False
        return (
            self.foreground == other.foreground and
            self.background == other.background and
            self.bold == other.bold and
            self.italic == other.italic and
            self.underline == other.underline and
            self.strike == other.strike and
            self.reverse == other.reverse
        )

class ANSIParser:
    """Parser for ANSI escape sequences."""
    
    # ANSI escape sequence patterns
    ESC = '\x1b'
    CSI = f'{ESC}['
    OSC = f'{ESC}]'
    
    # Basic color codes (0-7)
    BASIC_COLORS = {
        '30': '#000000',  # Black
        '31': '#CD0000',  # Red
        '32': '#00CD00',  # Green
        '33': '#CDCD00',  # Yellow
        '34': '#0000EE',  # Blue
        '35': '#CD00CD',  # Magenta
        '36': '#00CDCD',  # Cyan
        '37': '#E5E5E5',  # White
        '90': '#7F7F7F',  # Bright Black
        '91': '#FF0000',  # Bright Red
        '92': '#00FF00',  # Bright Green
        '93': '#FFFF00',  # Bright Yellow
        '94': '#5C5CFF',  # Bright Blue
        '95': '#FF00FF',  # Bright Magenta
        '96': '#00FFFF',  # Bright Cyan
        '97': '#FFFFFF',  # Bright White
    }
    
    # Background colors (40-47, add 10 to foreground code)
    BACKGROUND_COLORS = {
        str(int(k) + 10): v for k, v in BASIC_COLORS.items()
    }
    
    def __init__(self) -> None:
        """Initialize the ANSI parser."""
        self._current_style = TextStyle()
        self._style_stack: List[TextStyle] = []
        
        # Compile regex patterns
        self._csi_pattern = re.compile(
            rf'{re.escape(self.CSI)}([0-9;]*)([A-Za-z])'
        )
    
    def parse(self, text: str) -> List[Tuple[str, TextStyle]]:
        """
        Parse text containing ANSI escape sequences.
        
        Args:
            text: Text to parse
            
        Returns:
            List of (text, style) tuples
        """
        result: List[Tuple[str, TextStyle]] = []
        current_text = ""
        i = 0
        
        # Start with default style
        self._current_style = TextStyle()
        
        while i < len(text):
            if text[i] == self.ESC and i + 1 < len(text):
                # Process accumulated text with current style
                if current_text:
                    result.append((current_text, deepcopy(self._current_style)))
                    current_text = ""
                
                # Handle escape sequence
                if text[i + 1] == '[':  # CSI
                    sequence_end = text.find('m', i)
                    if sequence_end != -1:
                        sequence = text[i:sequence_end + 1]
                        params = sequence[2:-1].split(';')
                        
                        # Store current style before processing
                        old_style = deepcopy(self._current_style)
                        
                        # Process the sequence
                        self._handle_sgr(sequence)
                        
                        # Handle reset sequence
                        if params and params[0] == '0':
                            if old_style != TextStyle():
                                result.append(("", TextStyle()))
                        
                        i = sequence_end + 1
                        continue
                    else:
                        # Incomplete sequence, treat as normal text
                        current_text += text[i:i+2]
                        i += 2
                        continue
                
                # Invalid sequence, treat as normal text
                current_text += text[i:i+2]
                i += 2
                continue
            
            current_text += text[i]
            i += 1
        
        # Add remaining text
        if current_text:
            result.append((current_text, deepcopy(self._current_style)))
        
        # Add final empty segment only if we end with a non-default style
        if result and result[-1][1] != TextStyle():
            result.append(("", TextStyle()))
        
        # Merge consecutive segments with same style
        merged_result: List[Tuple[str, TextStyle]] = []
        for text, style in result:
            if not merged_result:
                merged_result.append((text, style))
                continue
            
            # Don't merge if either segment is empty
            if text == "" or merged_result[-1][0] == "":
                # Only add empty reset segment if previous style was non-default
                if text == "" and style == TextStyle() and merged_result[-1][1] == TextStyle():
                    continue
                merged_result.append((text, style))
            # Otherwise merge if styles match
            elif merged_result[-1][1] == style:
                merged_result[-1] = (merged_result[-1][0] + text, style)
            else:
                merged_result.append((text, style))
        
        return merged_result
    
    def _handle_sgr(self, sequence: str) -> None:
        """
        Handle Select Graphic Rendition (SGR) sequences.
        
        Args:
            sequence: SGR sequence (e.g., '\x1b[1;31m')
        """
        # Extract parameters
        params = sequence[2:-1].split(';')
        if not params or params[0] == '':
            params = ['0']
        
        # Create new style for this sequence
        new_style = deepcopy(self._current_style)
        
        i = 0
        while i < len(params):
            param = params[i]
            
            # Reset all attributes if this is a reset sequence
            if param == '0':
                new_style = TextStyle()
                i += 1
                continue
            
            elif param == '1':
                new_style.bold = True
            elif param == '3':
                new_style.italic = True
            elif param == '4':
                new_style.underline = True
            elif param == '7':
                new_style.reverse = True
            elif param == '9':
                new_style.strike = True
            
            elif param in self.BASIC_COLORS:
                new_style.foreground = self.BASIC_COLORS[param]
            elif param in self.BACKGROUND_COLORS:
                new_style.background = self.BACKGROUND_COLORS[param]
            
            elif param == '38' and i + 2 < len(params):
                # 256 colors and RGB
                mode = params[i + 1]
                if mode == '5' and i + 2 < len(params):  # 256 colors
                    try:
                        color_code = int(params[i + 2])
                        if 0 <= color_code <= 255:
                            new_style.foreground = self._get_256_color(color_code)
                        i += 2
                    except (ValueError, IndexError):
                        pass
                elif mode == '2' and i + 4 < len(params):  # RGB
                    try:
                        r = int(params[i + 2])
                        g = int(params[i + 3])
                        b = int(params[i + 4])
                        if all(0 <= x <= 255 for x in (r, g, b)):
                            new_style.foreground = f'#{r:02x}{g:02x}{b:02x}'
                        i += 4
                    except (ValueError, IndexError):
                        pass
            
            elif param == '48' and i + 2 < len(params):
                # Background 256 colors and RGB
                mode = params[i + 1]
                if mode == '5' and i + 2 < len(params):  # 256 colors
                    try:
                        color_code = int(params[i + 2])
                        if 0 <= color_code <= 255:
                            new_style.background = self._get_256_color(color_code)
                        i += 2
                    except (ValueError, IndexError):
                        pass
                elif mode == '2' and i + 4 < len(params):  # RGB
                    try:
                        r = int(params[i + 2])
                        g = int(params[i + 3])
                        b = int(params[i + 4])
                        if all(0 <= x <= 255 for x in (r, g, b)):
                            new_style.background = f'#{r:02x}{g:02x}{b:02x}'
                        i += 4
                    except (ValueError, IndexError):
                        pass
            
            i += 1
        
        self._current_style = new_style
    
    def _get_256_color(self, code: int) -> str:
        """
        Get color for 256-color mode.
        
        Args:
            code: Color code (0-255)
            
        Returns:
            HTML color code
        """
        if code < 16:
            # System colors (0-15)
            if code < 8:
                return list(self.BASIC_COLORS.values())[code]
            else:
                return list(self.BASIC_COLORS.values())[code - 8 + 8]  # Adjust index for bright colors
        
        elif code < 232:
            # 216 colors (16-231)
            code -= 16
            r = (code // 36) * 51
            g = ((code % 36) // 6) * 51
            b = (code % 6) * 51
            return f'#{r:02x}{g:02x}{b:02x}'
        
        else:
            # Grayscale (232-255)
            gray = (code - 232) * 10 + 8
            return f'#{gray:02x}{gray:02x}{gray:02x}'