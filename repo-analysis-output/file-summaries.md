# File Summaries

Heuristic summaries of source files based on filenames, extensions, and paths.

Schema Version: 2.0

Total files: 14

## license_header/__init__.py
**Language:** Python  
**Role:** module-init  
**Role Justification:** module initialization file '__init__'  
**Size:** 1.00 KB  
**LOC:** 4  
**TODOs/FIXMEs:** 0  

## license_header/apply.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 11.95 KB  
**LOC:** 235  
**TODOs/FIXMEs:** 0  
**Declarations:** 8  
**Top-level declarations:**
  - class ApplyResult
  - function normalize_header
  - function detect_newline_style
  - function convert_newlines
  - function has_header
  - function insert_header
  - function apply_header_to_file
  - function apply_headers
**External Dependencies:**
  - **Stdlib:** `dataclasses.dataclass`, `dataclasses.field`, `logging`, `os`, `pathlib.Path`
    _(and 3 more)_

## license_header/check.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 5.15 KB  
**LOC:** 94  
**TODOs/FIXMEs:** 0  
**Declarations:** 3  
**Top-level declarations:**
  - class CheckResult
  - function check_file_header
  - function check_headers
**External Dependencies:**
  - **Stdlib:** `dataclasses.dataclass`, `dataclasses.field`, `logging`, `pathlib.Path`, `typing.List`

## license_header/cli.py
**Language:** Python  
**Role:** cli  
**Role Justification:** CLI-related name 'cli'  
**Size:** 12.03 KB  
**LOC:** 196  
**TODOs/FIXMEs:** 0  
**Declarations:** 4  
**Top-level declarations:**
  - function check_python_version
  - function main
  - function apply
  - function check
**External Dependencies:**
  - **Stdlib:** `logging`, `pathlib.Path`, `sys`
  - **Third-party:** `click`

## license_header/config.py
**Language:** Python  
**Role:** configuration  
**Role Justification:** configuration file name 'config'  
**Size:** 11.75 KB  
**LOC:** 236  
**TODOs/FIXMEs:** 0  
**Declarations:** 9  
**Top-level declarations:**
  - class Config
  - function find_repo_root
  - function load_config_file
  - function validate_path_in_repo
  - function load_header_content
  - function validate_extensions
  - function validate_exclude_patterns
  - function merge_config
  - function get_header_content
**External Dependencies:**
  - **Stdlib:** `dataclasses.dataclass`, `dataclasses.field`, `json`, `logging`, `pathlib.Path`
    _(and 2 more)_
  - **Third-party:** `click`

## license_header/reports.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 10.90 KB  
**LOC:** 223  
**TODOs/FIXMEs:** 0  
**Declarations:** 4  
**Top-level declarations:**
  - function _format_file_list
  - function generate_json_report
  - function generate_markdown_report
  - function generate_reports
**External Dependencies:**
  - **Stdlib:** `datetime.datetime`, `datetime.timezone`, `json`, `logging`, `os`
    _(and 4 more)_

## license_header/scanner.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 13.38 KB  
**LOC:** 224  
**TODOs/FIXMEs:** 0  
**Declarations:** 6  
**Top-level declarations:**
  - class ScanResult
  - function is_binary_file
  - function _try_directory_patterns
  - function _matches_glob_pattern
  - function matches_exclude_pattern
  - function scan_repository
**External Dependencies:**
  - **Stdlib:** `dataclasses.dataclass`, `dataclasses.field`, `logging`, `os`, `pathlib.Path`
    _(and 1 more)_

## license_header/utils.py
**Language:** Python  
**Role:** utility  
**Role Justification:** utility/helper name 'utils'  
**Size:** 5.76 KB  
**LOC:** 116  
**TODOs/FIXMEs:** 0  
**Declarations:** 5  
**Top-level declarations:**
  - function detect_bom
  - function has_shebang
  - function extract_shebang
  - function read_file_with_encoding
  - function write_file_with_encoding
**External Dependencies:**
  - **Stdlib:** `codecs`, `logging`, `pathlib.Path`, `typing.Optional`, `typing.Tuple`

## tests/test_apply.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 36.47 KB  
**LOC:** 611  
**TODOs/FIXMEs:** 0  
**Declarations:** 7  
**Top-level declarations:**
  - class TestApplyResult
  - class TestUtilityFunctions
  - class TestNormalizeHeader
  - class TestHasHeader
  - class TestInsertHeader
  - class TestApplyHeaderToFile
  - class TestApplyHeaders
**External Dependencies:**
  - **Stdlib:** `codecs`, `os`, `pathlib.Path`
  - **Third-party:** `pytest`

## tests/test_check.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 9.63 KB  
**LOC:** 162  
**TODOs/FIXMEs:** 0  
**Declarations:** 3  
**Top-level declarations:**
  - class TestCheckResult
  - class TestCheckFileHeader
  - class TestCheckHeaders
**External Dependencies:**
  - **Stdlib:** `pathlib.Path`, `tempfile`
  - **Third-party:** `pytest`

## tests/test_cli.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 10.83 KB  
**LOC:** 199  
**TODOs/FIXMEs:** 0  
**Declarations:** 3  
**Top-level declarations:**
  - class TestCLI
  - class TestApplyCommand
  - class TestCheckCommand
**External Dependencies:**
  - **Stdlib:** `json`, `os`, `pathlib.Path`, `tempfile`
  - **Third-party:** `click.testing.CliRunner`, `pytest`

## tests/test_config.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 12.98 KB  
**LOC:** 241  
**TODOs/FIXMEs:** 0  
**Declarations:** 7  
**Top-level declarations:**
  - class TestConfig
  - class TestFindRepoRoot
  - class TestLoadConfigFile
  - class TestValidatePathInRepo
  - class TestLoadHeaderContent
  - class TestMergeConfig
  - class TestGetHeaderContent
**External Dependencies:**
  - **Stdlib:** `json`, `pathlib.Path`
  - **Third-party:** `click.ClickException`, `pytest`

## tests/test_reports.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 11.48 KB  
**LOC:** 182  
**TODOs/FIXMEs:** 0  
**Declarations:** 4  
**Top-level declarations:**
  - class TestFormatFileList
  - class TestGenerateJsonReport
  - class TestGenerateMarkdownReport
  - class TestGenerateReports
**External Dependencies:**
  - **Stdlib:** `json`, `os`, `pathlib.Path`, `tempfile`
  - **Third-party:** `pytest`

## tests/test_scanner.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 24.25 KB  
**LOC:** 422  
**TODOs/FIXMEs:** 0  
**Declarations:** 4  
**Top-level declarations:**
  - class TestScanResult
  - class TestIsBinaryFile
  - class TestMatchesExcludePattern
  - class TestScanRepository
**External Dependencies:**
  - **Stdlib:** `os`, `pathlib.Path`
  - **Third-party:** `pytest`
