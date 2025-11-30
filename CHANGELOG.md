# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-30

### ⚠️ Breaking Changes

#### V1 Header Format End-of-Life

V1 headers (with embedded comment markers) are **no longer supported** for regular operations. All users must migrate to V2 format.

- **V1 headers are deprecated**: The `header_version: "v1"` configuration is only allowed in `upgrade` mode
- **V2 is now required**: All `apply` and `check` operations require V2 headers (raw license text without comment markers)
- **No retroactive V1 support**: Files with V1 headers will not be automatically detected or updated without using the upgrade command

### Added

#### Upgrade Command for V1 to V2 Migration
- New `upgrade` command for safe, deterministic migration from V1 to V2 headers
- Required `--from-header` and `--to-header` arguments to prevent accidental modifications
- Support for migrating from V1 headers (with embedded comment markers) or older V2 headers
- Dry-run mode (`--dry-run`) to preview changes before applying
- JSON and Markdown report generation for audit purposes
- Atomic file writes to prevent partial modifications
- Detailed summary counters (scanned, upgraded, already target, no source header, skipped, failed)

#### Multi-Language Comment Wrapping
- Automatic comment syntax wrapping for Python, C, C++, C#, Java, JavaScript, TypeScript, and Rust
- Single comment-agnostic header file works across all supported languages
- Block comment mode (`--use-block-comments`) for C-style block comments
- Fallback comment style (`--fallback-comment-style`) for unknown file extensions
- Per-language comment style overrides via configuration

#### Enhanced Configuration
- `header_version` configuration field (`v1` or `v2`) with validation
- `language_comment_overrides` for per-extension comment style customization
- `upgrade_from_header` and `upgrade_to_header` configuration options
- Validation that `header_version: "v1"` is only allowed in upgrade mode

### Changed

- Default header format is now V2 (raw license text without comment markers)
- Header detection now handles both V1 and V2 formats during upgrade operations
- Configuration validation enforces V2 for `apply` and `check` modes

### Migration Guide

**Before using V2 features, you must upgrade existing headers:**

1. Create your old V1 header file (copy your existing header with comment markers)
2. Create your new V2 header file (raw license text without comment markers)
3. Preview the upgrade:
   ```bash
   license-header upgrade --from-header OLD_HEADER.txt --to-header NEW_HEADER.txt --dry-run
   ```
4. Perform the upgrade:
   ```bash
   license-header upgrade --from-header OLD_HEADER.txt --to-header NEW_HEADER.txt
   ```
5. Verify results with `license-header check`

## [0.2.0] - 2025-11-21

### Added

#### Core CLI Commands
- `apply` command: Automatically add or update license headers in source files
- `check` command: Verify that all source files have correct license headers
- `--dry-run` flag for both commands to preview changes without modifying files
- `--version` flag to display current version

#### Configuration System
- JSON configuration file support (`license-header.config.json`)
- CLI options for all configuration parameters with precedence over config file
- Support for custom configuration file paths via `--config` flag
- Configuration validation and security checks for path traversal
- Default configuration with sensible exclude patterns and file extensions

#### Repository Traversal
- Deterministic file scanning with consistent ordering across platforms
- Iterative directory walking for deep directory trees (handles >1000 levels)
- Case-insensitive file extension matching
- Binary file detection and automatic skipping
- Symlink detection and circular reference prevention
- Permission error handling without aborting scans
- Default exclusion of common directories: `.git`, `node_modules`, `__pycache__`, `venv`, `dist`, `build`
- Support for custom exclude patterns (simple directory names and glob patterns)
- Configurable file extension filtering

#### Header Management
- Idempotent header detection and application
- Shebang-aware header insertion (preserves `#!/...` lines)
- Exact header matching for compliance verification
- Whitespace normalization (ensures one trailing newline)
- BOM (Byte Order Mark) preservation for UTF-8, UTF-16, UTF-32 files
- Atomic file writes using temporary files and rename operations
- File permission preservation during modifications

#### Reporting
- JSON report generation with complete file lists and statistics
- Markdown report generation with human-readable summaries
- Separate reports for `apply` and `check` modes
- Deterministic summary counters (scanned, eligible, compliant, skipped, failed)
- Optional report generation via `--output` flag
- Automatic output directory creation
- Report generation validation and error handling

#### GitHub Actions Integration
- Exit code 1 for check failures (CI/CD ready)
- Exit code 0 for successful checks
- Examples for basic check workflow, check with reports, and auto-fix workflow
- Designed for use in CI/CD pipelines

### Features by Category

**Configuration Options:**
- `--header`: Path to license header file (default: `LICENSE_HEADER`)
- `--path`: Target directory to scan (default: current directory)
- `--output`: Output directory for JSON and Markdown reports
- `--include-extension`: File extensions to process (can be specified multiple times)
- `--exclude-path`: Paths/patterns to exclude (can be specified multiple times)
- `--dry-run`: Preview mode without file modifications
- `--config`: Custom configuration file path

**Traversal Capabilities:**
- Deterministic ordering for reproducible results
- Deep directory tree support without recursion limits
- Binary file automatic detection
- Symlink and circular reference handling
- Permission error graceful handling
- Case-insensitive extension matching
- Glob pattern support for exclusions

**Apply Mode:**
- In-place file modification
- Dry-run preview mode
- Summary statistics (scanned, eligible, added, compliant, skipped, failed)
- Optional JSON and Markdown report generation
- Idempotent operations (safe to run multiple times)

**Check Mode:**
- Read-only verification
- Non-zero exit code on non-compliance (fails CI/CD builds)
- Detailed listing of non-compliant files
- Summary statistics (scanned, eligible, compliant, non-compliant, skipped, failed)
- Optional JSON and Markdown report generation
- Dry-run mode to preview without generating reports

**Reporting:**
- JSON reports with complete data and ISO 8601 timestamps
- Markdown reports with human-readable summaries
- Large file list truncation in Markdown (shows first 100 files)
- Automatic output directory creation
- Validation of output directory permissions

### Technical Details
- Requires Python 3.11 or higher
- Built with Click framework for CLI
- Setuptools-based packaging
- Comprehensive test suite with 164+ tests
- Structured logging for debugging

### Limitations
- Per-file or per-extension custom headers not yet supported (uses single header file for all files)
- Report file limits: Markdown reports truncate large file lists to first 100 entries (full data in JSON)

## [0.1.0] - Initial Development

### Added
- Initial project structure
- Basic CLI framework
- Python version validation (3.11+ requirement)
