# Copyright 2025 John Brosnihan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Check module for license-header tool.

Implements header compliance checking without modifying files.
Supports multi-language comment wrapping detection.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .config import Config, get_header_content
from .scanner import scan_repository
from .apply import has_header, prepare_header_for_file
from .utils import read_file_with_encoding

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Result of checking files for license headers."""
    
    compliant_files: List[Path] = field(default_factory=list)
    non_compliant_files: List[Path] = field(default_factory=list)
    skipped_files: List[Path] = field(default_factory=list)
    failed_files: List[Path] = field(default_factory=list)
    
    def total_eligible(self) -> int:
        """Return total number of eligible files checked."""
        return len(self.compliant_files) + len(self.non_compliant_files) + len(self.failed_files)
    
    def total_scanned(self) -> int:
        """Return total number of files scanned."""
        return (
            len(self.compliant_files)
            + len(self.non_compliant_files)
            + len(self.skipped_files)
            + len(self.failed_files)
        )
    
    def is_compliant(self) -> bool:
        """Return True if all eligible files are compliant."""
        return len(self.non_compliant_files) == 0 and len(self.failed_files) == 0


def check_file_header(file_path: Path, header: str) -> bool:
    """
    Check if a file has the required header.
    
    Args:
        file_path: Path to file to check
        header: Expected header text
        
    Returns:
        True if file has the header, False otherwise
        
    Raises:
        OSError: If file cannot be read
        UnicodeDecodeError: If file encoding cannot be determined
    """
    try:
        # Read file with encoding detection
        content, bom, encoding = read_file_with_encoding(file_path)
        
        # Check if header is present
        return has_header(content, header)
        
    except (OSError, IOError, UnicodeDecodeError) as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def check_headers(config: Config) -> CheckResult:
    """
    Check all eligible files for required license headers.
    
    Does not modify any files. Scans repository and checks each eligible
    file for the presence of the required header. Uses language-aware
    comment wrapping when wrap_comments is enabled.
    
    Args:
        config: Configuration object with header and scanning settings
        
    Returns:
        CheckResult with statistics about compliant and non-compliant files
    """
    result = CheckResult()
    
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
        logger.info("Comment wrapping disabled - checking for raw header")
    
    # Check header in each eligible file
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
            
            has_required_header = check_file_header(file_path, header)
            
            if has_required_header:
                result.compliant_files.append(file_path)
                logger.debug(f"File is compliant: {file_path}")
            else:
                result.non_compliant_files.append(file_path)
                logger.info(f"File is missing header: {file_path}")
                
        except (PermissionError, OSError, IOError, UnicodeDecodeError) as e:
            logger.error(f"Failed to check {file_path}: {e}")
            result.failed_files.append(file_path)
    
    # Track skipped files from scan
    result.skipped_files.extend(scan_result.skipped_binary)
    result.skipped_files.extend(scan_result.skipped_excluded)
    result.skipped_files.extend(scan_result.skipped_symlink)
    result.skipped_files.extend(scan_result.skipped_permission)
    result.skipped_files.extend(scan_result.skipped_extension)
    
    return result
