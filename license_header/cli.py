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
CLI module for license-header tool.
"""

import logging
import sys
import click

from .config import merge_config, get_header_content, find_repo_root, load_header_content
from .apply import (
    apply_headers,
    UpgradeResult,
    prepare_header_for_file,
    upgrade_header_in_file,
)
from .check import check_headers
from .reports import generate_reports
from .scanner import scan_repository


# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python version meets minimum requirement."""
    if sys.version_info < (3, 11):
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        logger.error(f"Python 3.11 or higher is required. Current version: {current_version}")
        click.echo(
            f"Error: Python 3.11 or higher is required.\n"
            f"Current version: {current_version}\n"
            f"Please upgrade your Python installation.",
            err=True
        )
        sys.exit(1)


@click.group()
@click.version_option(message='%(version)s')
def main():
    """
    License Header CLI - Deterministic license header enforcement.
    
    Use 'license-header <command> --help' for more information on a specific command.
    """
    check_python_version()


@main.command()
@click.option('--config', type=str, help='Path to configuration file (default: license-header.config.json if present)')
@click.option('--header', type=str, help='Path to license header file')
@click.option('--path', default='.', help='Path to apply license headers (default: current directory)')
@click.option('--output', type=str, help='Output directory for JSON and Markdown report files (default: no reports generated)')
@click.option('--include-extension', multiple=True, help='File extensions to include (e.g., .py, .js). Can be specified multiple times.')
@click.option('--exclude-path', multiple=True, help='Paths/patterns to exclude (e.g., node_modules). Can be specified multiple times.')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
@click.option('--no-wrap-comments', is_flag=True, help='Disable automatic comment wrapping (use header text as-is)')
@click.option('--fallback-comment-style', type=click.Choice(['hash', 'slash', 'none']), default=None, help='Comment style for unknown file types (hash=#, slash=//, none=no wrapping)')
@click.option('--use-block-comments', is_flag=True, help='Use block comments (/* */) instead of line comments where supported')
def apply(config, header, path, output, include_extension, exclude_path, dry_run, no_wrap_comments, fallback_comment_style, use_block_comments):
    """Apply license headers to source files (modifies files in-place).
    
    Supports multi-language comment wrapping. Header file should contain raw
    license text without comment markers. The tool automatically wraps the
    header with the appropriate comment syntax for each file type (Python, C,
    C++, C#, TypeScript, JavaScript, Java, Rust).
    """
    logger.info(f"Apply command called with path='{path}', dry_run={dry_run}")
    
    try:
        # Build CLI args dictionary
        cli_args = {
            'header': header,
            'path': path,
            'output_dir': output,
            'include_extension': list(include_extension) if include_extension else None,
            'exclude_path': list(exclude_path) if exclude_path else None,
            'dry_run': dry_run,
            'mode': 'apply',
            'no_wrap_comments': no_wrap_comments,
            'fallback_comment_style': fallback_comment_style,
            'use_block_comments': use_block_comments if use_block_comments else None,
        }
        
        # Merge configuration
        cfg = merge_config(cli_args, config_file_path=config)
        
        # Get header content to verify it's loaded
        header_content = get_header_content(cfg)
        
        # Display configuration
        click.echo(f"Configuration loaded successfully:")
        click.echo(f"  Header file: {cfg.header_file}")
        click.echo(f"  Target path: {cfg.path}")
        click.echo(f"  Include extensions: {', '.join(cfg.include_extensions)}")
        click.echo(f"  Exclude paths: {', '.join(cfg.exclude_paths)}")
        if cfg.output_dir:
            click.echo(f"  Output directory: {cfg.output_dir}")
        click.echo(f"  Dry run: {cfg.dry_run}")
        click.echo(f"  Comment wrapping: {cfg.wrap_comments}")
        if cfg.wrap_comments:
            click.echo(f"  Fallback comment style: {cfg.fallback_comment_style}")
            click.echo(f"  Use block comments: {cfg.use_block_comments}")
        click.echo(f"  Header content loaded: {len(header_content)} characters")
        click.echo()
        
        # Apply headers
        logger.info("Applying license headers...")
        # Note: We don't pass output_dir to apply_headers - it's only used for report generation
        # Apply always modifies files in-place
        result = apply_headers(cfg)
        
        # Display summary
        click.echo(f"Summary:")
        click.echo(f"  Scanned: {result.total_processed()}")
        click.echo(f"  Eligible: {len(result.modified_files) + len(result.already_compliant) + len(result.failed_files)}")
        click.echo(f"  Added: {len(result.modified_files)}")
        click.echo(f"  Compliant: {len(result.already_compliant)}")
        click.echo(f"  Skipped: {len(result.skipped_files)}")
        click.echo(f"  Failed: {len(result.failed_files)}")
        click.echo()
        
        if dry_run:
            click.echo("[DRY RUN] Files that would be modified:")
            for file_path in result.modified_files:
                click.echo(f"  - {file_path}")
            click.echo()
            click.echo("[DRY RUN] No files were actually modified.")
        elif result.modified_files:
            click.echo(f"Modified {len(result.modified_files)} file(s):")
            for file_path in result.modified_files[:10]:  # Show first 10
                click.echo(f"  - {file_path}")
            if len(result.modified_files) > 10:
                click.echo(f"  ... and {len(result.modified_files) - 10} more")
        
        if result.failed_files:
            click.echo(f"\nFailed to process {len(result.failed_files)} file(s):")
            for file_path in result.failed_files:
                click.echo(f"  - {file_path}")
        
        # Generate reports if output directory specified
        if cfg.output_dir and not dry_run:
            try:
                from pathlib import Path
                output_path = Path(cfg.output_dir)
                if not output_path.is_absolute():
                    output_path = cfg._repo_root / output_path
                
                click.echo(f"\nGenerating reports in {output_path}...")
                generate_reports(result, output_path, 'apply', cfg._repo_root)
                click.echo(f"Reports written to {output_path}")
            except Exception as e:
                logger.error(f"Failed to generate reports: {e}")
                raise click.ClickException(f"Failed to generate reports: {e}")
        
        logger.info("Apply command completed successfully")
        
    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"Error in apply command: {e}", exc_info=True)
        raise click.ClickException(f"Failed to apply license headers: {e}")


@main.command()
@click.option('--config', type=str, help='Path to configuration file (default: license-header.config.json if present)')
@click.option('--header', type=str, help='Path to license header file')
@click.option('--path', default='.', help='Path to check for license headers (default: current directory)')
@click.option('--output', type=str, help='Output directory for report files (default: none)')
@click.option('--include-extension', multiple=True, help='File extensions to include (e.g., .py, .js). Can be specified multiple times.')
@click.option('--exclude-path', multiple=True, help='Paths/patterns to exclude (e.g., node_modules). Can be specified multiple times.')
@click.option('--dry-run', is_flag=True, help='Preview results without generating reports')
@click.option('--no-wrap-comments', is_flag=True, help='Disable automatic comment wrapping (check for header text as-is)')
@click.option('--fallback-comment-style', type=click.Choice(['hash', 'slash', 'none']), default=None, help='Comment style for unknown file types (hash=#, slash=//, none=no wrapping)')
@click.option('--use-block-comments', is_flag=True, help='Expect block comments (/* */) instead of line comments where supported')
def check(config, header, path, output, include_extension, exclude_path, dry_run, no_wrap_comments, fallback_comment_style, use_block_comments):
    """Check source files for correct license headers.
    
    Supports multi-language comment detection. Header file should contain raw
    license text without comment markers. The tool automatically checks for
    the header wrapped with the appropriate comment syntax for each file type.
    """
    logger.info(f"Check command called with path='{path}', dry_run={dry_run}")
    
    try:
        # Build CLI args dictionary
        cli_args = {
            'header': header,
            'path': path,
            'output_dir': output,
            'include_extension': list(include_extension) if include_extension else None,
            'exclude_path': list(exclude_path) if exclude_path else None,
            'dry_run': dry_run,
            'mode': 'check',
            'no_wrap_comments': no_wrap_comments,
            'fallback_comment_style': fallback_comment_style,
            'use_block_comments': use_block_comments if use_block_comments else None,
        }
        
        # Merge configuration
        cfg = merge_config(cli_args, config_file_path=config)
        
        # Get header content to verify it's loaded
        header_content = get_header_content(cfg)
        
        # Display configuration
        click.echo(f"Configuration loaded successfully:")
        click.echo(f"  Header file: {cfg.header_file}")
        click.echo(f"  Target path: {cfg.path}")
        click.echo(f"  Include extensions: {', '.join(cfg.include_extensions)}")
        click.echo(f"  Exclude paths: {', '.join(cfg.exclude_paths)}")
        if cfg.output_dir:
            click.echo(f"  Output directory: {cfg.output_dir}")
        click.echo(f"  Dry run: {cfg.dry_run}")
        click.echo(f"  Comment wrapping: {cfg.wrap_comments}")
        if cfg.wrap_comments:
            click.echo(f"  Fallback comment style: {cfg.fallback_comment_style}")
            click.echo(f"  Use block comments: {cfg.use_block_comments}")
        click.echo(f"  Header content loaded: {len(header_content)} characters")
        click.echo()
        
        # Check headers
        logger.info("Checking license headers...")
        result = check_headers(cfg)
        
        # Display summary
        click.echo(f"Summary:")
        click.echo(f"  Scanned: {result.total_scanned()}")
        click.echo(f"  Eligible: {result.total_eligible()}")
        click.echo(f"  Compliant: {len(result.compliant_files)}")
        click.echo(f"  Non-compliant: {len(result.non_compliant_files)}")
        click.echo(f"  Skipped: {len(result.skipped_files)}")
        click.echo(f"  Failed: {len(result.failed_files)}")
        click.echo()
        
        # Display non-compliant files
        if result.non_compliant_files:
            click.echo(f"Files missing license headers ({len(result.non_compliant_files)}):")
            for file_path in result.non_compliant_files:
                click.echo(f"  - {file_path}")
            click.echo()
        
        # Display failed files
        if result.failed_files:
            click.echo(f"Failed to check {len(result.failed_files)} file(s):")
            for file_path in result.failed_files:
                click.echo(f"  - {file_path}")
            click.echo()
        
        # Generate reports if output directory specified and not dry-run
        if cfg.output_dir and not dry_run:
            try:
                from pathlib import Path
                output_path = Path(cfg.output_dir)
                if not output_path.is_absolute():
                    output_path = cfg._repo_root / output_path
                
                click.echo(f"Generating reports in {output_path}...")
                generate_reports(result, output_path, 'check', cfg._repo_root)
                click.echo(f"Reports written to {output_path}")
                click.echo()
            except Exception as e:
                logger.error(f"Failed to generate reports: {e}")
                raise click.ClickException(f"Failed to generate reports: {e}")
        elif cfg.output_dir and dry_run:
            click.echo(f"[DRY RUN] Would generate reports in {cfg.output_dir}")
            click.echo()
        
        # Determine exit code
        # Check mode should fail by default when there are non-compliant files
        if result.non_compliant_files or result.failed_files:
            logger.error(f"Check failed: {len(result.non_compliant_files)} non-compliant, {len(result.failed_files)} failed")
            click.echo("Check FAILED: Files are missing license headers or could not be checked.", err=True)
            sys.exit(1)
        else:
            click.echo("Check PASSED: All files have correct license headers.")
        
        logger.info("Check command completed successfully")
        
    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"Error in check command: {e}", exc_info=True)
        raise click.ClickException(f"Failed to check license headers: {e}")


@main.command()
@click.option('--from-header', required=True, type=str, help='Path to source header file (V1 or old V2) to replace')
@click.option('--to-header', required=True, type=str, help='Path to target header file (V2 format) to insert')
@click.option('--path', default='.', help='Path to scan for files (default: current directory)')
@click.option('--output', type=str, help='Output directory for JSON and Markdown report files')
@click.option('--include-extension', multiple=True, help='File extensions to include (e.g., .py, .js). Can be specified multiple times.')
@click.option('--exclude-path', multiple=True, help='Paths/patterns to exclude (e.g., node_modules). Can be specified multiple times.')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
@click.option('--fallback-comment-style', type=click.Choice(['hash', 'slash', 'none']), default='hash', help='Comment style for unknown file types (hash=#, slash=//, none=no wrapping)')
@click.option('--use-block-comments', is_flag=True, help='Use block comments (/* */) instead of line comments where supported')
def upgrade(from_header, to_header, path, output, include_extension, exclude_path, dry_run, fallback_comment_style, use_block_comments):
    """Upgrade license headers from V1/old format to V2 format.
    
    This command transitions files from an old header (V1 with embedded comment
    markers or older V2) to a new V2 header format.
    
    REQUIRED: Both --from-header and --to-header must be specified.
    
    The source header (--from-header) can be either:
    - A V1 header file with embedded comment markers
    - An older V2 raw header file
    
    The target header (--to-header) should be a V2 raw license text file
    without comment markers. The tool will wrap it with appropriate comment
    syntax for each file type.
    
    Files that already have the target header will be skipped. Files without
    the source header will be reported but not modified.
    
    SAFETY: Always run with --dry-run first to preview changes.
    """
    logger.info(f"Upgrade command called with from='{from_header}', to='{to_header}', path='{path}', dry_run={dry_run}")
    
    try:
        from pathlib import Path as PathLib
        
        # Find repo root
        repo_root = find_repo_root(PathLib.cwd())
        
        # Load source header content
        from_header_content = load_header_content(from_header, repo_root)
        
        # Load target header content
        to_header_content = load_header_content(to_header, repo_root)
        
        # Display configuration
        click.echo(f"Upgrade configuration:")
        click.echo(f"  Source header: {from_header}")
        click.echo(f"  Target header: {to_header}")
        click.echo(f"  Target path: {path}")
        if include_extension:
            click.echo(f"  Include extensions: {', '.join(include_extension)}")
        if exclude_path:
            click.echo(f"  Exclude paths: {', '.join(exclude_path)}")
        if output:
            click.echo(f"  Output directory: {output}")
        click.echo(f"  Dry run: {dry_run}")
        click.echo(f"  Fallback comment style: {fallback_comment_style}")
        click.echo(f"  Use block comments: {use_block_comments}")
        click.echo(f"  Source header: {len(from_header_content)} characters")
        click.echo(f"  Target header: {len(to_header_content)} characters")
        click.echo()
        
        # Set up scan parameters
        scan_path = PathLib(path)
        if not scan_path.is_absolute():
            scan_path = repo_root / scan_path
        
        # Use defaults if not specified
        include_exts = list(include_extension) if include_extension else ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.rs']
        exclude_paths = list(exclude_path) if exclude_path else ['node_modules', '.git', '__pycache__', 'venv', 'env', '.venv', 'dist', 'build']
        
        # Scan for files
        logger.info(f"Scanning {scan_path} for eligible files...")
        scan_result = scan_repository(
            root_path=scan_path,
            include_extensions=include_exts,
            exclude_patterns=exclude_paths,
            repo_root=repo_root,
        )
        
        click.echo(f"Found {len(scan_result.eligible_files)} eligible files to check")
        click.echo()
        
        # Process files
        result = UpgradeResult()
        
        for file_path in scan_result.eligible_files:
            try:
                # Prepare target header for this specific file (wrap with comments)
                wrapped_to_header = prepare_header_for_file(
                    raw_header=to_header_content,
                    file_path=file_path,
                    wrap_comments=True,
                    fallback_style_name=fallback_comment_style,
                    use_block_comments=use_block_comments
                )
                
                # Perform upgrade
                status = upgrade_header_in_file(
                    file_path=file_path,
                    from_header=from_header_content,
                    to_header=wrapped_to_header,
                    dry_run=dry_run
                )
                
                if status == 'upgraded':
                    result.upgraded_files.append(file_path)
                elif status == 'already_target':
                    result.already_target.append(file_path)
                elif status == 'no_source':
                    result.no_source_header.append(file_path)
                elif status.startswith('error:'):
                    result.failed_files.append(file_path)
                    result.error_messages[file_path] = status[6:]  # Remove 'error:' prefix
                    
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                result.failed_files.append(file_path)
                result.error_messages[file_path] = str(e)
        
        # Track skipped files from scan
        result.skipped_files.extend(scan_result.skipped_binary)
        result.skipped_files.extend(scan_result.skipped_excluded)
        result.skipped_files.extend(scan_result.skipped_symlink)
        result.skipped_files.extend(scan_result.skipped_permission)
        result.skipped_files.extend(scan_result.skipped_extension)
        
        # Display summary
        click.echo(f"Summary:")
        click.echo(f"  Scanned: {result.total_processed()}")
        click.echo(f"  Upgraded: {len(result.upgraded_files)}")
        click.echo(f"  Already target: {len(result.already_target)}")
        click.echo(f"  No source header: {len(result.no_source_header)}")
        click.echo(f"  Skipped: {len(result.skipped_files)}")
        click.echo(f"  Failed: {len(result.failed_files)}")
        click.echo()
        
        if dry_run:
            click.echo("[DRY RUN] Files that would be upgraded:")
            for file_path in result.upgraded_files[:20]:
                try:
                    rel_path = file_path.relative_to(repo_root)
                except ValueError:
                    rel_path = file_path
                click.echo(f"  - {rel_path}")
            if len(result.upgraded_files) > 20:
                click.echo(f"  ... and {len(result.upgraded_files) - 20} more")
            click.echo()
            click.echo("[DRY RUN] No files were actually modified.")
        elif result.upgraded_files:
            click.echo(f"Upgraded {len(result.upgraded_files)} file(s):")
            for file_path in result.upgraded_files[:10]:
                try:
                    rel_path = file_path.relative_to(repo_root)
                except ValueError:
                    rel_path = file_path
                click.echo(f"  - {rel_path}")
            if len(result.upgraded_files) > 10:
                click.echo(f"  ... and {len(result.upgraded_files) - 10} more")
        
        if result.failed_files:
            click.echo(f"\nFailed to process {len(result.failed_files)} file(s):")
            for file_path in result.failed_files[:10]:
                try:
                    rel_path = file_path.relative_to(repo_root)
                except ValueError:
                    rel_path = file_path
                error_msg = result.error_messages.get(file_path, 'Unknown error')
                click.echo(f"  - {rel_path}: {error_msg}")
            if len(result.failed_files) > 10:
                click.echo(f"  ... and {len(result.failed_files) - 10} more")
        
        # Generate reports if output directory specified and not dry-run
        if output and not dry_run:
            try:
                output_path = PathLib(output)
                if not output_path.is_absolute():
                    output_path = repo_root / output_path
                
                click.echo(f"\nGenerating reports in {output_path}...")
                generate_reports(result, output_path, 'upgrade', repo_root)
                click.echo(f"Reports written to {output_path}")
            except Exception as e:
                logger.error(f"Failed to generate reports: {e}")
                raise click.ClickException(f"Failed to generate reports: {e}")
        elif output and dry_run:
            click.echo(f"\n[DRY RUN] Would generate reports in {output}")
        
        # Exit code based on failures
        if result.failed_files:
            click.echo("\nUpgrade completed with errors.", err=True)
            sys.exit(1)
        else:
            click.echo("\nUpgrade completed successfully.")
        
        logger.info("Upgrade command completed")
        
    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"Error in upgrade command: {e}", exc_info=True)
        raise click.ClickException(f"Failed to upgrade license headers: {e}")


if __name__ == '__main__':
    main()
