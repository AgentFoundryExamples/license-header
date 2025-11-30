# Dependency Graph

Intra-repository dependency analysis for Python and JavaScript/TypeScript files.

Includes classification of external dependencies as stdlib vs third-party.

## Statistics

- **Total files**: 16
- **Intra-repo dependencies**: 17
- **External stdlib dependencies**: 16
- **External third-party dependencies**: 4

## External Dependencies

### Standard Library / Core Modules

Total: 16 unique modules

- `codecs`
- `dataclasses.dataclass`
- `dataclasses.field`
- `datetime.datetime`
- `datetime.timezone`
- `json`
- `logging`
- `os`
- `pathlib.Path`
- `sys`
- `tempfile`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Tuple`
- `typing.Union`

### Third-Party Packages

Total: 4 unique packages

- `click`
- `click.ClickException`
- `click.testing.CliRunner`
- `pytest`

## Most Depended Upon Files (Intra-Repo)

- `license_header/config.py` (4 dependents)
- `license_header/utils.py` (3 dependents)
- `license_header/apply.py` (3 dependents)
- `license_header/languages.py` (2 dependents)
- `license_header/check.py` (2 dependents)
- `license_header/cli.py` (1 dependents)
- `license_header/reports.py` (1 dependents)
- `license_header/scanner.py` (1 dependents)

## Files with Most Dependencies (Intra-Repo)

- `tests/test_apply.py` (3 dependencies)
- `tests/test_languages.py` (3 dependencies)
- `tests/test_reports.py` (3 dependencies)
- `license_header/apply.py` (2 dependencies)
- `tests/test_check.py` (2 dependencies)
- `license_header/scanner.py` (1 dependencies)
- `tests/test_cli.py` (1 dependencies)
- `tests/test_config.py` (1 dependencies)
- `tests/test_scanner.py` (1 dependencies)
