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
Configuration module for license-header tool.

Handles loading and merging configuration from CLI arguments and config files.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import click

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration schema for license-header tool."""
    
    # Required configuration
    header_file: str
    
    # Optional configuration with defaults
    include_extensions: List[str] = field(default_factory=lambda: ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.rs'])
    exclude_paths: List[str] = field(default_factory=lambda: ['node_modules', '.git', '__pycache__', 'venv', 'env', '.venv', 'dist', 'build'])
    output_dir: Optional[str] = None
    dry_run: bool = False
    mode: str = 'apply'  # 'apply' or 'check'
    path: str = '.'
    strict: bool = False
    
    # Multi-language comment wrapping configuration
    wrap_comments: bool = True  # Enable/disable comment wrapping
    fallback_comment_style: str = 'hash'  # 'hash' for #, 'slash' for //, 'none' for no wrapping
    use_block_comments: bool = False  # Use block comments instead of line comments
    
    # V2 header version configuration
    header_version: str = 'v2'  # 'v1' or 'v2' - only 'v2' allowed for regular runs
    
    # Upgrade configuration (only used in upgrade mode)
    upgrade_from_header: Optional[str] = None  # Path to source header for upgrade
    upgrade_to_header: Optional[str] = None  # Path to target header for upgrade
    
    # Per-language comment overrides (extension -> style)
    # Keys are file extensions (e.g., '.py'), values are style names ('hash', 'slash', 'block')
    language_comment_overrides: Dict[str, str] = field(default_factory=dict)
    
    # Resolved paths (computed after loading)
    _header_content: Optional[str] = field(default=None, init=False, repr=False)
    _repo_root: Optional[Path] = field(default=None, init=False, repr=False)


def find_repo_root(start_path: Path) -> Path:
    """
    Find the repository root by looking for .git directory.
    
    Args:
        start_path: Starting path to search from
        
    Returns:
        Path to repository root
        
    Raises:
        ValueError: If no repository root is found
    """
    current = start_path.resolve()
    
    # Check if we're already in a git repo
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    
    # If no .git found, use the current working directory
    return start_path.resolve()


def load_config_file(config_path: Path) -> dict:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration values
        
    Raises:
        click.ClickException: If the file cannot be read or parsed
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config_data
    except FileNotFoundError:
        raise click.ClickException(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in configuration file {config_path}: {e}")
    except Exception as e:
        raise click.ClickException(f"Error reading configuration file {config_path}: {e}")


def validate_path_in_repo(path: Path, repo_root: Path, path_description: str) -> None:
    """
    Validate that a path does not traverse above the repository root.
    
    Args:
        path: Path to validate
        repo_root: Repository root path
        path_description: Description of the path for error messages
        
    Raises:
        click.ClickException: If path traverses above repo root
    """
    try:
        resolved_path = path.resolve()
        # Check if the resolved path is within the repo root
        resolved_path.relative_to(repo_root)
    except (ValueError, RuntimeError):
        raise click.ClickException(
            f"{path_description} '{path}' traverses above repository root '{repo_root}'. "
            "This is not allowed for security reasons."
        )


def load_header_content(header_file: str, repo_root: Path) -> str:
    """
    Load and validate the header file content.
    
    Args:
        header_file: Path to the header file (relative to repo root or absolute)
        repo_root: Repository root path
        
    Returns:
        Content of the header file
        
    Raises:
        click.ClickException: If header file is invalid or cannot be read
    """
    # Convert to Path and make absolute if relative
    header_path = Path(header_file)
    if not header_path.is_absolute():
        header_path = repo_root / header_path
    
    # For relative paths, validate they don't traverse above repo root
    # Absolute paths are allowed since we're only reading the header file
    if not Path(header_file).is_absolute():
        validate_path_in_repo(header_path, repo_root, "Header file path")
    
    # Check file exists
    if not header_path.exists():
        raise click.ClickException(
            f"Header file not found: {header_file}\n"
            f"Resolved to: {header_path}\n"
            f"Please ensure the header file exists and the path is correct."
        )
    
    if not header_path.is_file():
        raise click.ClickException(f"Header path is not a file: {header_path}")
    
    # Read header content
    try:
        with open(header_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Loaded header content from {header_path}")
        return content
    except Exception as e:
        raise click.ClickException(f"Error reading header file {header_path}: {e}")


def validate_extensions(extensions: List[str]) -> None:
    """
    Validate file extensions format.
    
    Args:
        extensions: List of file extensions
        
    Note:
        Logs warnings for unusual extensions but does not fail
    """
    for ext in extensions:
        if not ext.startswith('.'):
            logger.warning(f"Extension '{ext}' does not start with '.'. This may not match files as expected.")


def validate_exclude_patterns(patterns: List[str]) -> None:
    """
    Validate exclude patterns.
    
    Args:
        patterns: List of exclude patterns/globs
        
    Note:
        Logs warnings for unusual patterns but does not fail
    """
    for pattern in patterns:
        if pattern.startswith('/') or pattern.startswith('\\'):
            logger.warning(
                f"Exclude pattern '{pattern}' starts with path separator. "
                "Patterns are matched against relative paths."
            )


# Valid header version strings
VALID_HEADER_VERSIONS = ['v1', 'v2']

# Valid comment override styles
VALID_COMMENT_OVERRIDE_STYLES = ['hash', 'slash', 'block', 'none']


def validate_header_version(version: str, mode: str) -> None:
    """
    Validate header version string.
    
    Args:
        version: Header version string
        mode: Current mode ('apply', 'check', or 'upgrade')
        
    Raises:
        click.ClickException: If version is invalid or V1 is used outside upgrade mode
    """
    if version not in VALID_HEADER_VERSIONS:
        raise click.ClickException(
            f"Invalid header_version '{version}'. "
            f"Valid options are: {VALID_HEADER_VERSIONS}"
        )
    
    # V1 headers are only allowed in upgrade mode
    if version == 'v1' and mode != 'upgrade':
        raise click.ClickException(
            f"Header version 'v1' is only allowed in upgrade mode. "
            f"For regular {mode} operations, use 'v2' headers. "
            "To migrate from V1 to V2, use the 'upgrade' command."
        )


def validate_upgrade_config(
    upgrade_from_header: Optional[str],
    upgrade_to_header: Optional[str],
    mode: str
) -> None:
    """
    Validate upgrade configuration.
    
    Args:
        upgrade_from_header: Path to source header for upgrade
        upgrade_to_header: Path to target header for upgrade
        mode: Current mode ('apply', 'check', or 'upgrade')
        
    Raises:
        click.ClickException: If upgrade fields are invalid
    """
    # In upgrade mode, both from and to headers are required
    if mode == 'upgrade':
        if not upgrade_from_header or not upgrade_to_header:
            raise click.ClickException(
                "Upgrade mode requires both 'upgrade_from_header' and 'upgrade_to_header' to be set. "
                "Specify them via:\n"
                "  - CLI flags: --from-header and --to-header\n"
                "  - Config file: 'upgrade_from_header' and 'upgrade_to_header' keys"
            )
    else:
        # Outside of upgrade mode, upgrade fields should not be set
        if upgrade_from_header or upgrade_to_header:
            logger.warning(
                f"'upgrade_from_header' and 'upgrade_to_header' are only used in upgrade mode. "
                f"They will be ignored in {mode} mode."
            )


def validate_language_comment_overrides(overrides: Dict[str, str]) -> None:
    """
    Validate language comment overrides.
    
    Args:
        overrides: Dictionary mapping extensions to comment styles
        
    Raises:
        click.ClickException: If any override value is invalid
    """
    if not isinstance(overrides, dict):
        raise click.ClickException(
            f"Invalid type for 'language_comment_overrides': expected a dictionary, but got {type(overrides).__name__}."
        )
    
    if not overrides:
        # Empty overrides are valid - fall back to built-in defaults
        return
    
    for extension, style in overrides.items():
        # Validate extension format
        if not extension.startswith('.'):
            raise click.ClickException(
                f"Invalid extension '{extension}' in language_comment_overrides. "
                "Extensions must start with '.' (e.g., '.py', '.js')."
            )
        
        # Validate style value
        if style not in VALID_COMMENT_OVERRIDE_STYLES:
            raise click.ClickException(
                f"Invalid comment style '{style}' for extension '{extension}' in language_comment_overrides. "
                f"Valid styles are: {VALID_COMMENT_OVERRIDE_STYLES}"
            )


def merge_config(
    cli_args: dict,
    config_file_path: Optional[str] = None,
    repo_root: Optional[Path] = None
) -> Config:
    """
    Merge CLI arguments with config file settings.
    
    CLI arguments take precedence over config file settings.
    
    Args:
        cli_args: Dictionary of CLI arguments
        config_file_path: Optional path to config file
        repo_root: Repository root path
        
    Returns:
        Merged Config object
        
    Raises:
        click.ClickException: If configuration is invalid
    """
    # Determine repo root
    if repo_root is None:
        repo_root = find_repo_root(Path.cwd())
    
    # Start with defaults from Config dataclass
    config_data = {
        'include_extensions': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.rs'],
        'exclude_paths': ['node_modules', '.git', '__pycache__', 'venv', 'env', '.venv', 'dist', 'build'],
        'output_dir': None,
        'dry_run': False,
        'mode': 'apply',
        'path': '.',
        'strict': False,
        'wrap_comments': True,
        'fallback_comment_style': 'hash',
        'use_block_comments': False,
        'header_version': 'v2',
        'upgrade_from_header': None,
        'upgrade_to_header': None,
        'language_comment_overrides': {},
    }
    
    # Load config file if specified or if default exists
    config_file_data = {}
    if config_file_path:
        config_path = Path(config_file_path)
        if not config_path.is_absolute():
            config_path = repo_root / config_path
            # Validate that relative config paths don't escape the repository
            validate_path_in_repo(config_path, repo_root, "Configuration file path")
        config_file_data = load_config_file(config_path)
    else:
        # Check for default config file
        default_config = repo_root / 'license-header.config.json'
        if default_config.exists():
            config_file_data = load_config_file(default_config)
            logger.info(f"Using default configuration file: {default_config}")
    
    # Merge: config file overrides defaults
    if config_file_data:
        # Map config file keys to internal keys
        for key in ['include_extensions', 'exclude_paths', 'output_dir', 'header_file',
                    'wrap_comments', 'fallback_comment_style', 'use_block_comments',
                    'header_version', 'upgrade_from_header', 'upgrade_to_header',
                    'language_comment_overrides']:
            if key in config_file_data and config_file_data[key] is not None:
                config_data[key] = config_file_data[key]
    
    # Merge: CLI args override everything
    for key, value in cli_args.items():
        if value is not None:
            # Handle special CLI argument names
            if key == 'include_extension':
                # CLI can pass multiple --include-extension flags
                if value:
                    config_data['include_extensions'] = value
            elif key == 'exclude_path':
                # CLI can pass multiple --exclude-path flags
                if value:
                    config_data['exclude_paths'] = value
            elif key == 'header':
                config_data['header_file'] = value
            elif key == 'no_wrap_comments':
                # Handle the --no-wrap-comments flag
                if value:
                    config_data['wrap_comments'] = False
            else:
                config_data[key] = value
    
    # Validate required fields - check for default LICENSE_HEADER if not specified
    if 'header_file' not in config_data:
        default_header = repo_root / 'LICENSE_HEADER'
        if default_header.exists():
            config_data['header_file'] = 'LICENSE_HEADER'
            logger.info(f"Using default header file: {default_header}")
        else:
            raise click.ClickException(
                "Header file is required. Specify it via:\n"
                "  - CLI flag: --header <path>\n"
                "  - Config file: 'header_file' key\n"
                "  - Default: 'LICENSE_HEADER' file in repository root"
            )
    
    # Validate fallback comment style
    valid_fallback_styles = ['hash', 'slash', 'none']
    if config_data['fallback_comment_style'] not in valid_fallback_styles:
        logger.warning(
            f"Invalid fallback_comment_style '{config_data['fallback_comment_style']}'. "
            f"Using 'hash'. Valid options: {valid_fallback_styles}"
        )
        config_data['fallback_comment_style'] = 'hash'
    
    # Validate and warn about extensions and patterns
    validate_extensions(config_data['include_extensions'])
    validate_exclude_patterns(config_data['exclude_paths'])
    
    # Validate V2 configuration fields
    mode = config_data.get('mode', 'apply')
    header_version = config_data.get('header_version', 'v2')
    validate_header_version(header_version, mode)
    
    # Validate upgrade configuration
    upgrade_from = config_data.get('upgrade_from_header')
    upgrade_to = config_data.get('upgrade_to_header')
    validate_upgrade_config(upgrade_from, upgrade_to, mode)
    
    # Validate language comment overrides
    language_overrides = config_data.get('language_comment_overrides', {})
    validate_language_comment_overrides(language_overrides)
    
    # Validate upgrade header paths are within repo if specified
    if upgrade_from:
        upgrade_from_path = Path(upgrade_from)
        if not upgrade_from_path.is_absolute():
            upgrade_from_path = repo_root / upgrade_from_path
        validate_path_in_repo(upgrade_from_path, repo_root, "Upgrade source header path")
    
    if upgrade_to:
        upgrade_to_path = Path(upgrade_to)
        if not upgrade_to_path.is_absolute():
            upgrade_to_path = repo_root / upgrade_to_path
        validate_path_in_repo(upgrade_to_path, repo_root, "Upgrade target header path")
    
    # Create Config object
    config = Config(
        header_file=config_data['header_file'],
        include_extensions=config_data['include_extensions'],
        exclude_paths=config_data['exclude_paths'],
        output_dir=config_data.get('output_dir'),
        dry_run=config_data.get('dry_run', False),
        mode=config_data.get('mode', 'apply'),
        path=config_data.get('path', '.'),
        strict=config_data.get('strict', False),
        wrap_comments=config_data.get('wrap_comments', True),
        fallback_comment_style=config_data.get('fallback_comment_style', 'hash'),
        use_block_comments=config_data.get('use_block_comments', False),
        header_version=header_version,
        upgrade_from_header=upgrade_from,
        upgrade_to_header=upgrade_to,
        language_comment_overrides=language_overrides,
    )
    
    # Store repo root
    config._repo_root = repo_root
    
    # Load and validate header content
    config._header_content = load_header_content(config.header_file, repo_root)
    
    # Validate output directory if specified
    if config.output_dir:
        output_path = Path(config.output_dir)
        if not output_path.is_absolute():
            output_path = repo_root / output_path
        validate_path_in_repo(output_path, repo_root, "Output directory")
    
    logger.info(f"Configuration loaded successfully: {config}")
    return config


def get_header_content(config: Config) -> str:
    """
    Get the header content from the configuration.
    
    Header content is loaded exactly once and cached.
    
    Args:
        config: Configuration object
        
    Returns:
        Header content string
    """
    if config._header_content is None:
        raise RuntimeError("Header content not loaded. This is a bug.")
    return config._header_content
