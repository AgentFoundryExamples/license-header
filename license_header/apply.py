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
Apply module for license-header tool.

Implements header insertion logic with idempotency, shebang preservation,
and atomic file writes. Supports multi-language comment wrapping and
header transition/upgrade functionality.
"""

import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .config import Config, get_header_content
from .languages import (
    CommentStyle,
    DEFAULT_FALLBACK_STYLE,
    get_comment_style_for_extension,
    wrap_header_with_comments,
    unwrap_header_comments,
    detect_header_comment_style,
    PYTHON_STYLE,
    C_STYLE,
)
from .scanner import scan_repository
from .utils import (
    extract_shebang,
    has_shebang,
    read_file_with_encoding,
    write_file_with_encoding,
)

logger = logging.getLogger(__name__)


# Fallback style mapping
FALLBACK_STYLES = {
    'hash': CommentStyle(line_prefix='# '),
    'slash': CommentStyle(line_prefix='// '),
    'none': None,
}


@dataclass
class ApplyResult:
    """Result of applying headers to files."""
    
    modified_files: List[Path] = field(default_factory=list)
    already_compliant: List[Path] = field(default_factory=list)
    skipped_files: List[Path] = field(default_factory=list)
    failed_files: List[Path] = field(default_factory=list)
    
    def total_processed(self) -> int:
        """Return total number of files processed."""
        return (
            len(self.modified_files)
            + len(self.already_compliant)
            + len(self.skipped_files)
            + len(self.failed_files)
        )


def normalize_header(header: str) -> str:
    """
    Normalize header text for comparison.
    
    Ensures header ends with exactly one newline for consistent comparison.
    
    Args:
        header: Header text to normalize
        
    Returns:
        Normalized header text with LF line endings
    """
    # Strip trailing whitespace and ensure exactly one trailing newline
    return header.rstrip() + '\n'


def detect_newline_style(content: str) -> str:
    """
    Detect the predominant newline style in content.
    
    Args:
        content: File content to analyze
        
    Returns:
        '\r\n' for CRLF, '\n' for LF
    """
    # Count occurrences of each newline style
    crlf_count = content.count('\r\n')
    lf_count = content.count('\n') - crlf_count  # Subtract CRLF to get pure LF count
    
    # Use CRLF if it's the predominant style
    if crlf_count > lf_count:
        return '\r\n'
    return '\n'


def convert_newlines(text: str, target_newline: str) -> str:
    """
    Convert text to use target newline style.
    
    Args:
        text: Text to convert
        target_newline: Target newline style ('\r\n' or '\n')
        
    Returns:
        Text with converted newlines
    """
    # First normalize to LF, then convert to target
    text = text.replace('\r\n', '\n')
    if target_newline == '\r\n':
        text = text.replace('\n', '\r\n')
    return text


def prepare_header_for_file(
    raw_header: str,
    file_path: Path,
    wrap_comments: bool = True,
    fallback_style_name: str = 'hash',
    use_block_comments: bool = False
) -> str:
    """
    Prepare header text for a specific file by wrapping with comments.
    
    If wrap_comments is True, the header will be wrapped with the appropriate
    comment syntax for the file's language (detected from extension).
    
    Args:
        raw_header: Raw header text without comment markers
        file_path: Path to the file (used to detect language)
        wrap_comments: If True, wrap header with comments; if False, use as-is
        fallback_style_name: Fallback comment style name ('hash', 'slash', 'none')
        use_block_comments: If True, use block comments instead of line comments
        
    Returns:
        Header text ready for insertion (with or without comment markers)
    """
    if not wrap_comments:
        # Return header as-is (legacy behavior)
        return raw_header
    
    # Get fallback style
    fallback_style = FALLBACK_STYLES.get(fallback_style_name, DEFAULT_FALLBACK_STYLE)
    
    # Get comment style for file extension
    extension = file_path.suffix
    comment_style = get_comment_style_for_extension(
        extension,
        fallback_style=fallback_style
    )
    
    if comment_style is None:
        # No comment style available (fallback was 'none')
        logger.debug(f"No comment style for {extension}, using raw header")
        return raw_header
    
    # Wrap header with comments
    wrapped = wrap_header_with_comments(
        raw_header,
        comment_style,
        use_block_comments=use_block_comments
    )
    
    logger.debug(f"Wrapped header for {extension}: {len(raw_header)} -> {len(wrapped)} chars")
    return wrapped


def has_header(content: str, header: str) -> bool:
    """
    Check if content already has the header.
    
    This performs an exact match check. The header must appear at the start
    of the file (after any shebang line).
    
    Args:
        content: File content to check
        header: Header text to look for
        
    Returns:
        True if content has the header, False otherwise
    """
    # Normalize header for comparison (convert to LF-only)
    normalized_header = normalize_header(header)
    
    # Extract shebang if present
    shebang, remaining = extract_shebang(content)
    
    # Normalize content to LF-only for comparison
    # This allows matching headers regardless of CRLF vs LF style
    normalized_remaining = remaining.replace('\r\n', '\n')
    
    # Check if remaining content starts with the header
    if normalized_remaining.startswith(normalized_header):
        return True
    
    # Also check with various whitespace variations around the header
    # to handle cases where there might be extra blank lines
    lines = normalized_remaining.split('\n')
    
    # Skip leading empty lines
    start_idx = 0
    while start_idx < len(lines) and lines[start_idx].strip() == '':
        start_idx += 1
    
    # Reconstruct content without leading whitespace
    if start_idx < len(lines):
        content_without_leading_ws = '\n'.join(lines[start_idx:])
        # Use exact match with the full normalized header (including trailing newline)
        if content_without_leading_ws.startswith(normalized_header):
            return True
    
    return False


def insert_header(content: str, header: str) -> str:
    """
    Insert header into file content.
    
    Preserves shebang lines if present. Inserts header immediately after
    shebang, or at the start of the file if no shebang.
    Preserves the newline style of the original content.
    
    Args:
        content: Original file content
        header: Header text to insert
        
    Returns:
        New file content with header inserted
    """
    # Detect the newline style of the content
    newline_style = detect_newline_style(content)
    
    # Normalize header to LF first, then convert to match content's newline style
    normalized_header = normalize_header(header)
    normalized_header = convert_newlines(normalized_header, newline_style)
    
    # Extract shebang if present
    shebang, remaining = extract_shebang(content)
    
    # Build new content
    if shebang:
        # Insert header after shebang
        # Ensure shebang ends with newline before adding header
        if not shebang.endswith('\n') and not shebang.endswith('\r\n'):
            shebang = shebang + newline_style
        new_content = shebang + normalized_header + remaining
    else:
        # Insert header at start
        new_content = normalized_header + remaining
    
    return new_content


def apply_header_to_file(
    file_path: Path,
    header: str,
    dry_run: bool = False,
    output_dir: Optional[Path] = None,
    scan_root: Optional[Path] = None
) -> bool:
    """
    Apply header to a single file.
    
    Writes changes atomically using a temporary file and rename.
    
    Args:
        file_path: Path to file to modify
        header: Header text to insert
        dry_run: If True, don't actually modify files
        output_dir: If provided, write to this directory instead of in-place
        scan_root: Root path used for scanning (needed to preserve relative paths in output_dir)
        
    Returns:
        True if file was modified, False if already compliant or skipped
        
    Raises:
        OSError: If file cannot be read or written
        PermissionError: If file cannot be accessed
    """
    try:
        # Read file with encoding detection
        content, bom, encoding = read_file_with_encoding(file_path)
        
        # Check if header already present
        if has_header(content, header):
            logger.debug(f"File already has header: {file_path}")
            return False
        
        # Insert header
        new_content = insert_header(content, header)
        
        if dry_run:
            logger.info(f"[DRY RUN] Would add header to: {file_path}")
            return True
        
        # Determine output path
        if output_dir:
            # Write to output directory, preserving relative directory structure
            if scan_root:
                try:
                    # Preserve relative path from scan root
                    rel_path = file_path.resolve().relative_to(scan_root.resolve())
                    output_path = output_dir / rel_path
                except ValueError:
                    # File is not relative to scan root, use basename as fallback
                    output_path = output_dir / file_path.name
            else:
                # No scan root provided, use basename
                output_path = output_dir / file_path.name
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = file_path
        
        # Write atomically using temporary file
        # Create temp file in same directory as target to ensure same filesystem
        temp_fd, temp_path = tempfile.mkstemp(
            dir=output_path.parent,
            prefix=f'.{output_path.name}.',
            suffix='.tmp'
        )
        
        try:
            # Close the fd, we'll use our own write function
            os.close(temp_fd)
            
            # Write new content to temp file
            write_file_with_encoding(Path(temp_path), new_content, bom, encoding)
            
            # Preserve file permissions if modifying in-place
            if not output_dir:
                try:
                    stat_info = os.stat(file_path)
                    os.chmod(temp_path, stat_info.st_mode)
                except (OSError, AttributeError):
                    # If we can't preserve permissions, continue anyway
                    pass
            
            # Atomic rename
            os.replace(temp_path, output_path)
            
            logger.info(f"Added header to: {file_path}")
            return True
            
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
    
    except PermissionError as e:
        logger.error(f"Permission denied accessing {file_path}: {e}")
        raise
    except (OSError, IOError) as e:
        logger.error(f"Error processing {file_path}: {e}")
        raise


def apply_headers(config: Config) -> ApplyResult:
    """
    Apply headers to all eligible files in the repository.
    
    Uses language-aware comment wrapping when wrap_comments is enabled.
    
    Args:
        config: Configuration object with header and scanning settings
        
    Returns:
        ApplyResult with statistics about modified files
    """
    result = ApplyResult()
    
    # Get raw header content
    raw_header = get_header_content(config)
    
    # Determine paths
    repo_root = config._repo_root
    scan_path = Path(config.path)
    if not scan_path.is_absolute():
        scan_path = repo_root / scan_path
    
    # Scan repository for eligible files
    logger.info(f"Scanning {scan_path} for eligible files...")
    scan_result = scan_repository(
        root_path=scan_path,
        include_extensions=config.include_extensions,
        exclude_patterns=config.exclude_paths,
        repo_root=repo_root,
    )
    
    logger.info(f"Found {len(scan_result.eligible_files)} eligible files")
    
    # Log comment wrapping configuration
    if config.wrap_comments:
        logger.info(f"Comment wrapping enabled (fallback: {config.fallback_comment_style}, "
                    f"block: {config.use_block_comments})")
    else:
        logger.info("Comment wrapping disabled - using header as-is")
    
    # Apply header to each eligible file (always in-place, never copying to output dir)
    for file_path in scan_result.eligible_files:
        try:
            # Prepare header for this specific file (wrap with comments if enabled)
            header = prepare_header_for_file(
                raw_header=raw_header,
                file_path=file_path,
                wrap_comments=config.wrap_comments,
                fallback_style_name=config.fallback_comment_style,
                use_block_comments=config.use_block_comments
            )
            
            was_modified = apply_header_to_file(
                file_path=file_path,
                header=header,
                dry_run=config.dry_run,
                output_dir=None,  # Always modify in-place
                scan_root=scan_path
            )
            
            if was_modified:
                result.modified_files.append(file_path)
            else:
                result.already_compliant.append(file_path)
                
        except (PermissionError, OSError, IOError, UnicodeDecodeError) as e:
            logger.error(f"Failed to process {file_path}: {e}")
            result.failed_files.append(file_path)
    
    # Track skipped files from scan
    result.skipped_files.extend(scan_result.skipped_binary)
    result.skipped_files.extend(scan_result.skipped_excluded)
    result.skipped_files.extend(scan_result.skipped_symlink)
    result.skipped_files.extend(scan_result.skipped_permission)
    result.skipped_files.extend(scan_result.skipped_extension)
    
    return result


# ============================================================
# Header Transition / Upgrade Functions
# ============================================================


@dataclass
class UpgradeResult:
    """Result of upgrading headers in files."""
    
    upgraded_files: List[Path] = field(default_factory=list)
    already_target: List[Path] = field(default_factory=list)
    no_source_header: List[Path] = field(default_factory=list)
    skipped_files: List[Path] = field(default_factory=list)
    failed_files: List[Path] = field(default_factory=list)
    error_messages: dict = field(default_factory=dict)  # Path -> error message
    
    def total_processed(self) -> int:
        """Return total number of files processed."""
        return (
            len(self.upgraded_files)
            + len(self.already_target)
            + len(self.no_source_header)
            + len(self.skipped_files)
            + len(self.failed_files)
        )


def strip_comment_markers(text: str) -> str:
    """
    Strip comment markers from header text to get raw body.
    
    This is used to compare header content regardless of comment style.
    Handles V1 headers (with embedded comment markers) and V2 headers.
    
    Args:
        text: Header text that may have comment markers
        
    Returns:
        Raw header text without comment markers
    """
    if not text:
        return ''
    
    lines = text.strip().splitlines()
    result_lines = []
    in_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Handle single-line block comments like `/* ... */`
        if not in_block and stripped.startswith('/*') and stripped.endswith('*/'):
            content = stripped[2:-2].strip()
            if content.startswith('*'):
                content = content[1:].strip()
            if content:
                result_lines.append(content)
            continue
        
        # Handle start of a multi-line block comment
        if not in_block and stripped.startswith('/*'):
            in_block = True
            content = stripped[2:].strip()
            if content:
                result_lines.append(content)
            continue
        
        # Handle end of a multi-line block comment
        if in_block and stripped.endswith('*/'):
            in_block = False
            content = stripped[:-2].strip()
            if content.startswith('*'):
                content = content[1:].strip()
            if content:
                result_lines.append(content)
            continue
        
        if in_block:
            # Handle lines inside a multi-line block comment
            content = stripped
            if content.startswith('*'):
                content = content[1:].lstrip()
            result_lines.append(content)
            continue
        
        # Handle line comment prefixes
        # Check for common prefixes in order of length (longer first to avoid partial matches)
        # We check both with and without trailing space variants
        prefixes = ['// ', '# ', '-- ', '; ', '//', '#', '--', ';']
        found_prefix = False
        for prefix in prefixes:
            if stripped.startswith(prefix):
                rest = stripped[len(prefix):]
                result_lines.append(rest)
                found_prefix = True
                break
        
        if not found_prefix:
            result_lines.append(stripped)
    
    return '\n'.join(result_lines).strip() + '\n' if result_lines else ''


def normalize_body_for_comparison(text: str) -> str:
    """
    Normalize header body text for comparison.
    
    Strips comment markers, normalizes whitespace, and lowercases for
    fuzzy matching during header detection.
    
    Args:
        text: Header text to normalize
        
    Returns:
        Normalized text for comparison
    """
    # Strip comment markers first
    stripped = strip_comment_markers(text)
    
    # Normalize whitespace, remove empty lines, lowercase in single pass
    result_lines = []
    for line in stripped.splitlines():
        normalized = ' '.join(line.split())
        if normalized:
            result_lines.append(normalized.lower())
    
    return '\n'.join(result_lines).strip()


def detect_header_in_content(
    content: str,
    header_text: str,
    file_extension: str = '.py'
) -> Tuple[bool, int, int]:
    """
    Detect if a header (or its body) is present in file content.
    
    This function can detect both V1 headers (with embedded comment markers)
    and V2 headers (wrapped using language-specific comments).
    
    Args:
        content: File content to search
        header_text: Header text to look for (may have comment markers or not)
        file_extension: File extension for determining expected comment style
        
    Returns:
        Tuple of (found, start_pos, end_pos) where start_pos and end_pos
        are character positions in content (0-indexed). Returns (False, -1, -1)
        if header not found.
    """
    if not content or not header_text:
        return (False, -1, -1)
    
    # Normalize header for comparison
    header_body = normalize_body_for_comparison(header_text)
    
    # Extract shebang if present
    shebang, remaining = extract_shebang(content)
    start_offset = len(shebang) if shebang else 0
    
    # Try to find where the header ends
    # Look for the first significant code line (not comment, not empty)
    lines = remaining.splitlines(keepends=True)
    header_end_idx = 0
    potential_header_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            header_end_idx += len(line)
            potential_header_lines.append(line)
            continue
        
        # Check if this looks like a comment
        is_comment = any(stripped.startswith(p) for p in ['#', '//', '/*', '*', '--', ';', '<!--'])
        
        if is_comment:
            header_end_idx += len(line)
            potential_header_lines.append(line)
        else:
            # First non-comment, non-empty line - end of potential header
            break
    
    # Extract potential header block
    potential_header = ''.join(potential_header_lines)
    
    if not potential_header.strip():
        return (False, -1, -1)
    
    # Normalize potential header
    content_body = normalize_body_for_comparison(potential_header)
    
    # Compare
    if header_body == content_body:
        return (True, start_offset, start_offset + header_end_idx)
    
    # Also try exact match (for V2 headers)
    normalized_header = normalize_header(header_text)
    normalized_remaining = remaining.replace('\r\n', '\n')
    
    if normalized_remaining.startswith(normalized_header):
        return (True, start_offset, start_offset + len(normalized_header))
    
    return (False, -1, -1)


def remove_header_from_content(
    content: str,
    header_text: str,
    file_extension: str = '.py'
) -> Tuple[str, bool]:
    """
    Remove a header from file content.
    
    Args:
        content: File content
        header_text: Header to remove
        file_extension: File extension for comment style detection
        
    Returns:
        Tuple of (new_content, was_removed)
    """
    found, start_pos, end_pos = detect_header_in_content(
        content, header_text, file_extension
    )
    
    if not found:
        return (content, False)
    
    # Reconstruct content by taking everything before and after the detected header
    new_content = content[:start_pos] + content[end_pos:]
    
    return (new_content, True)


def upgrade_header_in_content(
    content: str,
    from_header: str,
    to_header: str,
    file_extension: str = '.py'
) -> Tuple[str, str]:
    """
    Upgrade header in file content from source to target.
    
    Args:
        content: File content
        from_header: Source header to remove (may be V1 or V2)
        to_header: Target header to insert (should be V2 format)
        file_extension: File extension for comment style detection
        
    Returns:
        Tuple of (new_content, status) where status is one of:
        - 'upgraded': Header was replaced
        - 'already_target': File already has target header
        - 'no_source': Source header not found
        - 'error:message': An error occurred
    """
    # First check if file already has target header
    if has_header(content, to_header):
        return (content, 'already_target')
    
    # Try to find and remove source header
    found, start_pos, end_pos = detect_header_in_content(
        content, from_header, file_extension
    )
    
    if not found:
        return (content, 'no_source')
    
    # Remove source header
    content_without_header, removed = remove_header_from_content(
        content, from_header, file_extension
    )
    
    if not removed:
        return (content, 'error:Failed to remove source header')
    
    # Insert target header
    new_content = insert_header(content_without_header, to_header)
    
    return (new_content, 'upgraded')


def upgrade_header_in_file(
    file_path: Path,
    from_header: str,
    to_header: str,
    dry_run: bool = False
) -> str:
    """
    Upgrade header in a single file.
    
    Args:
        file_path: Path to file
        from_header: Source header to replace
        to_header: Target header to insert
        dry_run: If True, don't actually modify the file
        
    Returns:
        Status string: 'upgraded', 'already_target', 'no_source', or 'error:message'
        
    Raises:
        OSError: If file cannot be read or written
    """
    try:
        # Read file
        content, bom, encoding = read_file_with_encoding(file_path)
        
        # Perform upgrade
        new_content, status = upgrade_header_in_content(
            content, from_header, to_header, file_path.suffix
        )
        
        if status != 'upgraded':
            return status
        
        if dry_run:
            logger.info(f"[DRY RUN] Would upgrade header in: {file_path}")
            return 'upgraded'
        
        # Write atomically using temporary file
        temp_fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix=f'.{file_path.name}.',
            suffix='.tmp'
        )
        
        try:
            os.close(temp_fd)
            write_file_with_encoding(Path(temp_path), new_content, bom, encoding)
            
            # Preserve permissions
            try:
                stat_info = os.stat(file_path)
                os.chmod(temp_path, stat_info.st_mode)
            except (OSError, AttributeError):
                pass
            
            # Atomic rename
            os.replace(temp_path, file_path)
            logger.info(f"Upgraded header in: {file_path}")
            return 'upgraded'
            
        except Exception as e:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
            
    except (PermissionError, OSError, IOError, UnicodeDecodeError) as e:
        logger.error(f"Error upgrading {file_path}: {e}")
        return f'error:{e}'
