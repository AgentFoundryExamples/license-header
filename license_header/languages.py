# ============================================================
# SPDX-License-Identifier: GPL-3.0-or-later
# This program was generated as part of the AgentFoundry project.
# Copyright (C) 2025  John Brosnihan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ============================================================
"""
Language metadata module for license-header tool.

Provides extension-to-language mapping and comment style descriptors
for multi-language header wrapping support.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CommentStyle:
    """Describes comment syntax for a programming language.
    
    Attributes:
        line_prefix: Prefix for line comments (e.g., '# ' for Python, '// ' for C)
        block_start: Start marker for block comments (e.g., '/*' for C)
        block_end: End marker for block comments (e.g., '*/' for C)
        block_line_prefix: Prefix for lines within block comments (e.g., ' * ')
        doc_start: Start marker for doc comments (optional)
        doc_end: End marker for doc comments (optional)
        doc_line_prefix: Prefix for lines within doc comments (optional)
    """
    line_prefix: Optional[str] = None
    block_start: Optional[str] = None
    block_end: Optional[str] = None
    block_line_prefix: Optional[str] = None
    doc_start: Optional[str] = None
    doc_end: Optional[str] = None
    doc_line_prefix: Optional[str] = None
    
    def supports_line_comments(self) -> bool:
        """Check if this style supports line comments."""
        return self.line_prefix is not None
    
    def supports_block_comments(self) -> bool:
        """Check if this style supports block comments."""
        return self.block_start is not None and self.block_end is not None


@dataclass
class LanguageInfo:
    """Information about a programming language.
    
    Attributes:
        name: Human-readable language name
        extensions: File extensions associated with this language
        comment_style: Comment style descriptor
        preferred_style: Preferred comment style ('line' or 'block')
    """
    name: str
    extensions: List[str]
    comment_style: CommentStyle
    preferred_style: str = 'line'


# Default comment styles for supported languages
PYTHON_STYLE = CommentStyle(
    line_prefix='# ',
)

C_STYLE = CommentStyle(
    line_prefix='// ',
    block_start='/*',
    block_end=' */',
    block_line_prefix=' * ',
)

RUST_STYLE = CommentStyle(
    line_prefix='// ',
    block_start='/*',
    block_end=' */',
    block_line_prefix=' * ',
    doc_start='///',
    doc_line_prefix='/// ',
)

# Default language definitions
DEFAULT_LANGUAGES: Dict[str, LanguageInfo] = {
    'python': LanguageInfo(
        name='Python',
        extensions=['.py', '.pyi', '.pyw'],
        comment_style=PYTHON_STYLE,
        preferred_style='line',
    ),
    'c': LanguageInfo(
        name='C',
        extensions=['.c', '.h'],
        comment_style=C_STYLE,
        preferred_style='line',
    ),
    'cpp': LanguageInfo(
        name='C++',
        extensions=['.cpp', '.hpp', '.cc', '.hh', '.cxx', '.hxx'],
        comment_style=C_STYLE,
        preferred_style='line',
    ),
    'csharp': LanguageInfo(
        name='C#',
        extensions=['.cs'],
        comment_style=C_STYLE,
        preferred_style='line',
    ),
    'java': LanguageInfo(
        name='Java',
        extensions=['.java'],
        comment_style=C_STYLE,
        preferred_style='line',
    ),
    'javascript': LanguageInfo(
        name='JavaScript',
        extensions=['.js', '.mjs', '.cjs'],
        comment_style=C_STYLE,
        preferred_style='line',
    ),
    'typescript': LanguageInfo(
        name='TypeScript',
        extensions=['.ts', '.mts', '.cts', '.tsx'],
        comment_style=C_STYLE,
        preferred_style='line',
    ),
    'rust': LanguageInfo(
        name='Rust',
        extensions=['.rs'],
        comment_style=RUST_STYLE,
        preferred_style='line',
    ),
}

# Default fallback comment style (hash-style line comments)
DEFAULT_FALLBACK_STYLE = CommentStyle(line_prefix='# ')


def build_extension_map(languages: Dict[str, LanguageInfo]) -> Dict[str, str]:
    """
    Build a mapping from file extensions to language names.
    
    Args:
        languages: Dictionary of language definitions
        
    Returns:
        Dictionary mapping lowercase extensions to language names
    """
    ext_map: Dict[str, str] = {}
    for lang_name, lang_info in languages.items():
        for ext in lang_info.extensions:
            ext_lower = ext.lower()
            if ext_lower in ext_map:
                logger.warning(
                    f"Extension '{ext}' is mapped to multiple languages: "
                    f"'{ext_map[ext_lower]}' and '{lang_name}'. Using '{lang_name}'."
                )
            ext_map[ext_lower] = lang_name
    return ext_map


# Default extension-to-language mapping
DEFAULT_EXTENSION_MAP = build_extension_map(DEFAULT_LANGUAGES)


def get_language_for_extension(
    extension: str,
    extension_map: Optional[Dict[str, str]] = None,
    languages: Optional[Dict[str, LanguageInfo]] = None
) -> Optional[LanguageInfo]:
    """
    Get language information for a file extension.
    
    Args:
        extension: File extension (with or without leading dot)
        extension_map: Custom extension map (uses default if None)
        languages: Custom language definitions (uses default if None)
        
    Returns:
        LanguageInfo for the extension, or None if not found
    """
    if extension_map is None:
        extension_map = DEFAULT_EXTENSION_MAP
    if languages is None:
        languages = DEFAULT_LANGUAGES
    
    # Ensure extension has leading dot and is lowercase
    ext = extension.lower()
    if not ext.startswith('.'):
        ext = '.' + ext
    
    lang_name = extension_map.get(ext)
    if lang_name is None:
        return None
    
    return languages.get(lang_name)


# Sentinel value to indicate "use default fallback"
_USE_DEFAULT_FALLBACK = object()


def get_comment_style_for_extension(
    extension: str,
    extension_map: Optional[Dict[str, str]] = None,
    languages: Optional[Dict[str, LanguageInfo]] = None,
    fallback_style: Optional[CommentStyle] = _USE_DEFAULT_FALLBACK
) -> Optional[CommentStyle]:
    """
    Get the comment style for a file extension.
    
    Args:
        extension: File extension (with or without leading dot)
        extension_map: Custom extension map (uses default if None)
        languages: Custom language definitions (uses default if None)
        fallback_style: Fallback style for unknown extensions. Pass None explicitly
            to get None for unknown extensions, or omit to use DEFAULT_FALLBACK_STYLE.
        
    Returns:
        CommentStyle for the extension, fallback style if not found, or None
        if fallback_style was explicitly set to None
    """
    # Use default fallback if not specified (using sentinel)
    if fallback_style is _USE_DEFAULT_FALLBACK:
        fallback_style = DEFAULT_FALLBACK_STYLE
    
    lang_info = get_language_for_extension(extension, extension_map, languages)
    if lang_info is None:
        logger.debug(f"Using fallback comment style for extension '{extension}'")
        return fallback_style
    
    return lang_info.comment_style


def is_header_already_wrapped(header_text: str) -> bool:
    """
    Detect if a header already has comment markers.
    
    This checks if all non-empty lines start with a consistent comment prefix,
    which indicates it was already wrapped and should not be wrapped again.
    
    Args:
        header_text: Header text to check
        
    Returns:
        True if header appears to already have comment markers
    """
    if not header_text:
        return False
    
    lines = header_text.strip().splitlines()
    if not lines:
        return False
    
    # Find first non-empty line to determine the potential comment prefix
    first_line_stripped = ''
    for line in lines:
        if line.strip():
            first_line_stripped = line.lstrip()
            break
    
    if not first_line_stripped:
        return False  # Header is all whitespace
    
    # Common comment prefixes
    comment_prefixes = ['#', '//', '/*', '*', '<!--', '"""', "'''", ';', '--']
    
    # Find which prefix the first line uses
    detected_prefix = None
    for prefix in comment_prefixes:
        if first_line_stripped.startswith(prefix):
            detected_prefix = prefix
            break
    
    if detected_prefix is None:
        return False  # First line doesn't start with a comment prefix
    
    # Check that all non-empty lines start with the same prefix
    for line in lines:
        stripped = line.strip()
        if stripped:
            # For block comment style, allow lines starting with * or the detected prefix
            if detected_prefix == '/*':
                # Block comment start - check if other lines start with * or */
                if not (stripped.startswith('*') or stripped.startswith('/*')):
                    return False
            elif detected_prefix == '*':
                # Inside block comment - allow * and */
                if not stripped.startswith('*'):
                    return False
            else:
                # Line comment - all lines must start with same prefix
                if not stripped.startswith(detected_prefix):
                    return False
    
    return True


def wrap_header_with_comments(
    header_text: str,
    comment_style: CommentStyle,
    use_block_comments: bool = False
) -> str:
    """
    Wrap raw header text with comment syntax.
    
    If the header already appears to have comment markers, it is returned
    unchanged to prevent double-wrapping.
    
    Args:
        header_text: Raw header text without comment markers
        comment_style: Comment style to use
        use_block_comments: If True, use block comments instead of line comments
        
    Returns:
        Header text wrapped with appropriate comment syntax
        
    Raises:
        ValueError: If comment_style is None
    """
    # Validate comment_style parameter
    if comment_style is None:
        raise ValueError("comment_style parameter cannot be None")
    
    # Check if header already has comment markers
    if is_header_already_wrapped(header_text):
        logger.debug("Header already has comment markers, skipping wrapping")
        return header_text.rstrip() + '\n' if header_text else ''
    
    # Normalize header text - ensure no trailing whitespace but preserve content
    lines = header_text.rstrip().splitlines()
    
    if use_block_comments and comment_style.supports_block_comments():
        # Use block comment style
        result_lines = [comment_style.block_start]
        line_prefix = comment_style.block_line_prefix or ' * '
        for line in lines:
            if line.strip():
                result_lines.append(f"{line_prefix}{line}")
            else:
                # Empty lines in block comments just get the prefix stripped
                result_lines.append(line_prefix.rstrip())
        result_lines.append(comment_style.block_end)
        return '\n'.join(result_lines) + '\n'
    
    elif comment_style.supports_line_comments():
        # Use line comment style
        result_lines = []
        for line in lines:
            if line.strip():
                result_lines.append(f"{comment_style.line_prefix}{line}")
            else:
                # Empty lines just get the comment prefix (stripped of trailing space)
                result_lines.append(comment_style.line_prefix.rstrip())
        return '\n'.join(result_lines) + '\n'
    
    else:
        # No comment style available, return header as-is
        logger.warning("No comment style available, returning header unchanged")
        return header_text.rstrip() + '\n'


def unwrap_header_comments(
    wrapped_header: str,
    comment_style: CommentStyle
) -> str:
    """
    Remove comment markers from a wrapped header to get the raw text.
    
    This is useful for detecting if an existing header matches the expected
    content regardless of comment style differences.
    
    Args:
        wrapped_header: Header text with comment markers
        comment_style: Comment style that was used
        
    Returns:
        Raw header text without comment markers
    """
    lines = wrapped_header.rstrip().splitlines()
    result_lines = []
    in_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check for block comment markers
        if comment_style.supports_block_comments():
            if stripped == comment_style.block_start.strip():
                in_block = True
                continue
            if stripped == comment_style.block_end.strip():
                in_block = False
                continue
            
            if in_block:
                # Remove block line prefix
                prefix = comment_style.block_line_prefix
                if prefix and line.startswith(prefix):
                    result_lines.append(line[len(prefix):])
                elif prefix and line.strip().startswith(prefix.strip()):
                    result_lines.append(line.strip()[len(prefix.strip()):].lstrip())
                else:
                    result_lines.append(line)
                continue
        
        # Check for line comment prefix
        if comment_style.supports_line_comments():
            prefix = comment_style.line_prefix
            if prefix:
                # Handle both with and without trailing space
                if line.startswith(prefix):
                    result_lines.append(line[len(prefix):])
                elif line.startswith(prefix.rstrip()):
                    # Empty comment line
                    result_lines.append('')
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
        else:
            result_lines.append(line)
    
    return '\n'.join(result_lines).rstrip() + '\n' if result_lines else ''


def detect_header_comment_style(
    content: str,
    known_styles: Optional[List[CommentStyle]] = None
) -> Optional[CommentStyle]:
    """
    Detect what comment style is used in existing file header.
    
    This is useful for checking if a file has an existing license header
    regardless of the comment style used.
    
    Args:
        content: File content to analyze
        known_styles: List of comment styles to check (uses defaults if None)
        
    Returns:
        Detected CommentStyle or None if no comments detected
    """
    if known_styles is None:
        known_styles = [PYTHON_STYLE, C_STYLE, RUST_STYLE]
    
    first_lines = content.lstrip().splitlines()[:10]  # Check first 10 lines
    if not first_lines:
        return None
    
    first_line = first_lines[0]
    
    for style in known_styles:
        # Check for block comment start (use full prefix for exact matching)
        if style.block_start and first_line.lstrip().startswith(style.block_start):
            return style
        
        # Check for line comment prefix (use full prefix to avoid false positives)
        if style.line_prefix and first_line.startswith(style.line_prefix):
            return style
        
        # Also check without leading space (for lines that just have the comment marker)
        if style.line_prefix and first_line.startswith(style.line_prefix.rstrip()):
            return style
    
    return None
