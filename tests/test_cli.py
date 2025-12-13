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
Tests for CLI module.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from click.testing import CliRunner

from license_header.cli import main


class TestCLI:
    """Test CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_version(self):
        """Test --version flag."""
        result = self.runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output
    
    def test_help(self):
        """Test --help flag."""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'License Header CLI' in result.output
        assert 'apply' in result.output
        assert 'check' in result.output
    
    def test_apply_help(self):
        """Test apply --help."""
        result = self.runner.invoke(main, ['apply', '--help'])
        assert result.exit_code == 0
        assert '--config' in result.output
        assert '--header' in result.output
        assert '--include-extension' in result.output
        assert '--exclude-path' in result.output
        assert '--dry-run' in result.output
    
    def test_check_help(self):
        """Test check --help."""
        result = self.runner.invoke(main, ['check', '--help'])
        assert result.exit_code == 0
        assert '--config' in result.output
        assert '--header' in result.output
        assert '--dry-run' in result.output


class TestApplyCommand:
    """Test apply command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_apply_with_header_file(self):
        """Test apply command with header file."""
        with self.runner.isolated_filesystem():
            # Create header file
            Path('HEADER.txt').write_text('# Copyright\n')
            
            result = self.runner.invoke(main, ['apply', '--header', 'HEADER.txt', '--dry-run'])
            assert result.exit_code == 0
            assert 'Configuration loaded successfully' in result.output
            assert 'Header file: HEADER.txt' in result.output
    
    def test_apply_missing_header_file(self):
        """Test apply command with missing header file."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(main, ['apply', '--header', 'nonexistent.txt'])
            assert result.exit_code != 0
            assert 'Header file not found' in result.output
    
    def test_apply_with_config_file(self):
        """Test apply command with config file."""
        with self.runner.isolated_filesystem():
            # Create header file
            Path('HEADER.txt').write_text('# Copyright\n')
            
            # Create config file
            config_data = {
                'header_file': 'HEADER.txt',
                'include_extensions': ['.py'],
            }
            Path('config.json').write_text(json.dumps(config_data))
            
            result = self.runner.invoke(main, ['apply', '--config', 'config.json', '--dry-run'])
            assert result.exit_code == 0
            assert 'Configuration loaded successfully' in result.output
            assert 'Include extensions: .py' in result.output
    
    def test_apply_cli_overrides_config(self):
        """Test that CLI flags override config file."""
        with self.runner.isolated_filesystem():
            # Create header files
            Path('HEADER1.txt').write_text('# Header 1\n')
            Path('HEADER2.txt').write_text('# Header 2\n')
            
            # Create config file
            config_data = {
                'header_file': 'HEADER1.txt',
            }
            Path('config.json').write_text(json.dumps(config_data))
            
            result = self.runner.invoke(main, [
                'apply',
                '--config', 'config.json',
                '--header', 'HEADER2.txt',
                '--dry-run'
            ])
            assert result.exit_code == 0
            assert 'Header file: HEADER2.txt' in result.output
    
    def test_apply_with_default_config(self):
        """Test apply command with default config file."""
        with self.runner.isolated_filesystem():
            # Create header file
            Path('HEADER.txt').write_text('# Copyright\n')
            
            # Create default config file
            config_data = {
                'header_file': 'HEADER.txt',
            }
            Path('license-header.config.json').write_text(json.dumps(config_data))
            
            result = self.runner.invoke(main, ['apply', '--dry-run'])
            assert result.exit_code == 0
            assert 'Configuration loaded successfully' in result.output
    
    def test_apply_with_extensions(self):
        """Test apply command with custom extensions."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright\n')
            
            result = self.runner.invoke(main, [
                'apply',
                '--header', 'HEADER.txt',
                '--include-extension', '.py',
                '--include-extension', '.js',
                '--dry-run'
            ])
            assert result.exit_code == 0
            assert 'Include extensions: .py, .js' in result.output
    
    def test_apply_with_exclude_paths(self):
        """Test apply command with exclude paths."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright\n')
            
            result = self.runner.invoke(main, [
                'apply',
                '--header', 'HEADER.txt',
                '--exclude-path', 'dist',
                '--exclude-path', 'build',
                '--dry-run'
            ])
            assert result.exit_code == 0
            assert 'Exclude paths: dist, build' in result.output
    
    def test_apply_with_default_license_header(self):
        """Test apply command with default LICENSE_HEADER file."""
        with self.runner.isolated_filesystem():
            Path('LICENSE_HEADER').write_text('# Default Header\n')
            
            result = self.runner.invoke(main, ['apply', '--dry-run'])
            assert result.exit_code == 0
            assert 'Configuration loaded successfully' in result.output
            assert 'Header file: LICENSE_HEADER' in result.output
    
    def test_apply_cli_overrides_default_license_header(self):
        """Test that --header flag overrides default LICENSE_HEADER."""
        with self.runner.isolated_filesystem():
            Path('LICENSE_HEADER').write_text('# Default\n')
            Path('CUSTOM.txt').write_text('# Custom\n')
            
            result = self.runner.invoke(main, ['apply', '--header', 'CUSTOM.txt', '--dry-run'])
            assert result.exit_code == 0
            assert 'Header file: CUSTOM.txt' in result.output
    
    def test_apply_with_absolute_header_path(self):
        """Test apply command with absolute path to header file."""
        with self.runner.isolated_filesystem():
            # Create a header file with absolute path
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write('# Absolute Path Header\n')
                abs_header_path = f.name
            
            try:
                result = self.runner.invoke(main, ['apply', '--header', abs_header_path, '--dry-run'])
                assert result.exit_code == 0
                assert 'Configuration loaded successfully' in result.output
                assert abs_header_path in result.output
            finally:
                # Clean up
                os.unlink(abs_header_path)
    
    def test_apply_with_config_path_outside_repo_rejected(self):
        """Test that config paths escaping repo are rejected."""
        with self.runner.isolated_filesystem():
            # Create header file
            Path('HEADER.txt').write_text('# Copyright\n')
            
            # Try to use a config path that escapes the repo
            result = self.runner.invoke(main, ['apply', '--config', '../outside_config.json', '--dry-run'])
            assert result.exit_code != 0
            assert 'Configuration file path' in result.output
            assert 'traverses above repository root' in result.output


class TestCheckCommand:
    """Test check command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_check_with_header_file(self):
        """Test check command with header file."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright\n')
            
            result = self.runner.invoke(main, ['check', '--header', 'HEADER.txt'])
            assert result.exit_code == 0
            assert 'Configuration loaded successfully' in result.output
    
    def test_check_basic(self):
        """Test basic check command."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright\n')
            
            result = self.runner.invoke(main, ['check', '--header', 'HEADER.txt'])
            assert result.exit_code == 0
            assert 'Summary:' in result.output
    
    def test_check_dry_run_mode(self):
        """Test check command with dry-run mode."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright\n')
            
            result = self.runner.invoke(main, ['check', '--header', 'HEADER.txt', '--dry-run'])
            assert result.exit_code == 0
            assert 'Dry run: True' in result.output
            assert 'Summary:' in result.output
    
    def test_check_missing_header_file(self):
        """Test check command with missing header file."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(main, ['check', '--header', 'nonexistent.txt'])
            assert result.exit_code != 0
            assert 'Header file not found' in result.output


class TestUpgradeCommand:
    """Test upgrade command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_upgrade_help(self):
        """Test upgrade --help."""
        result = self.runner.invoke(main, ['upgrade', '--help'])
        assert result.exit_code == 0
        assert '--from-header' in result.output
        assert '--to-header' in result.output
        assert '--dry-run' in result.output
        assert 'REQUIRED' in result.output
    
    def test_upgrade_requires_from_header(self):
        """Test upgrade command requires --from-header."""
        with self.runner.isolated_filesystem():
            Path('TO_HEADER.txt').write_text('New Copyright\n')
            result = self.runner.invoke(main, ['upgrade', '--to-header', 'TO_HEADER.txt'])
            assert result.exit_code != 0
            assert 'Missing option' in result.output or '--from-header' in result.output
    
    def test_upgrade_requires_to_header(self):
        """Test upgrade command requires --to-header."""
        with self.runner.isolated_filesystem():
            Path('FROM_HEADER.txt').write_text('Old Copyright\n')
            result = self.runner.invoke(main, ['upgrade', '--from-header', 'FROM_HEADER.txt'])
            assert result.exit_code != 0
            assert 'Missing option' in result.output or '--to-header' in result.output
    
    def test_upgrade_dry_run(self):
        """Test upgrade command with dry-run mode."""
        with self.runner.isolated_filesystem():
            # Create old V1 header (with comment markers)
            Path('OLD_HEADER.txt').write_text('# Old Copyright 2024\n')
            
            # Create new V2 header (raw text)
            Path('NEW_HEADER.txt').write_text('New Copyright 2025\n')
            
            # Create test file with old header
            Path('test.py').write_text('# Old Copyright 2024\ndef hello():\n    pass\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt',
                '--dry-run'
            ])
            assert result.exit_code == 0
            assert '[DRY RUN]' in result.output
            assert 'Upgraded: 1' in result.output
            
            # File should not be modified
            content = Path('test.py').read_text()
            assert '# Old Copyright 2024' in content
    
    def test_upgrade_actual(self):
        """Test upgrade command actually modifies files."""
        with self.runner.isolated_filesystem():
            # Create old V1 header (with comment markers)
            Path('OLD_HEADER.txt').write_text('# Old Copyright 2024\n')
            
            # Create new V2 header (raw text)
            Path('NEW_HEADER.txt').write_text('New Copyright 2025\n')
            
            # Create test file with old header
            Path('test.py').write_text('# Old Copyright 2024\ndef hello():\n    pass\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt'
            ])
            assert result.exit_code == 0
            assert 'Upgraded: 1' in result.output
            
            # File should be modified
            content = Path('test.py').read_text()
            assert '# New Copyright 2025' in content
            assert '# Old Copyright 2024' not in content
    
    def test_upgrade_already_target(self):
        """Test upgrade command skips files that already have target header."""
        with self.runner.isolated_filesystem():
            # Create headers
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            
            # Create test file already with new header
            Path('test.py').write_text('# New Copyright\ndef hello():\n    pass\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt'
            ])
            assert result.exit_code == 0
            assert 'Already target: 1' in result.output
            assert 'Upgraded: 0' in result.output
    
    def test_upgrade_no_source_header(self):
        """Test upgrade command reports files without source header."""
        with self.runner.isolated_filesystem():
            # Create headers
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            
            # Create test file without any header
            Path('test.py').write_text('def hello():\n    pass\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt'
            ])
            assert result.exit_code == 0
            assert 'No source header: 1' in result.output
    
    def test_upgrade_missing_from_header_file(self):
        """Test upgrade command with missing from-header file."""
        with self.runner.isolated_filesystem():
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'nonexistent.txt',
                '--to-header', 'NEW_HEADER.txt'
            ])
            assert result.exit_code != 0
            assert 'Header file not found' in result.output
    
    def test_upgrade_missing_to_header_file(self):
        """Test upgrade command with missing to-header file."""
        with self.runner.isolated_filesystem():
            Path('OLD_HEADER.txt').write_text('Old Copyright\n')
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'nonexistent.txt'
            ])
            assert result.exit_code != 0
            assert 'Header file not found' in result.output
    
    def test_upgrade_with_output_reports(self):
        """Test upgrade command with output reports."""
        with self.runner.isolated_filesystem():
            # Create headers
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            
            # Create test file with old header
            Path('test.py').write_text('# Old Copyright\ndef hello():\n    pass\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt',
                '--output', 'reports'
            ])
            assert result.exit_code == 0
            assert Path('reports/license-header-upgrade-report.json').exists()
            assert Path('reports/license-header-upgrade-report.md').exists()
    
    def test_upgrade_same_file_rejected(self):
        """Test upgrade command rejects same file for from and to headers."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('Copyright\n')
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'HEADER.txt',
                '--to-header', 'HEADER.txt'
            ])
            assert result.exit_code != 0
            assert '--from-header and --to-header cannot be the same file' in result.output
    
    def test_upgrade_multi_file_mixed_results(self):
        """Test upgrade with multiple files having different statuses."""
        with self.runner.isolated_filesystem():
            # Create headers
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            
            # Create file with old header (will be upgraded)
            Path('file1.py').write_text('# Old Copyright\ndef f1(): pass\n')
            
            # Create file already with new header (will be skipped)
            Path('file2.py').write_text('# New Copyright\ndef f2(): pass\n')
            
            # Create file without any header (no source)
            Path('file3.py').write_text('def f3(): pass\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt'
            ])
            
            assert result.exit_code == 0
            assert 'Upgraded: 1' in result.output
            assert 'Already target: 1' in result.output
            assert 'No source header: 1' in result.output
    
    def test_upgrade_preserves_shebang(self):
        """Test that upgrade preserves shebang lines."""
        with self.runner.isolated_filesystem():
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            
            # Create file with shebang and old header
            Path('script.py').write_text('#!/usr/bin/env python\n# Old Copyright\nprint("hi")\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt'
            ])
            
            assert result.exit_code == 0
            content = Path('script.py').read_text()
            assert content.startswith('#!/usr/bin/env python\n')
            assert '# New Copyright' in content
    
    def test_upgrade_with_extension_filter(self):
        """Test upgrade with extension filtering."""
        with self.runner.isolated_filesystem():
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            
            # Create Python file (should be upgraded)
            Path('file.py').write_text('# Old Copyright\ncode\n')
            
            # Create JS file (should be skipped due to extension filter)
            Path('file.js').write_text('// Old Copyright\ncode\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt',
                '--include-extension', '.py'
            ])
            
            assert result.exit_code == 0
            # Python file should be upgraded
            assert '# New Copyright' in Path('file.py').read_text()
            # JS file should be unchanged
            assert '// Old Copyright' in Path('file.js').read_text()
    
    def test_upgrade_reports_json_structure(self):
        """Test that upgrade reports have correct JSON structure."""
        with self.runner.isolated_filesystem():
            import json
            
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            Path('test.py').write_text('# Old Copyright\ncode\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt',
                '--output', 'reports'
            ])
            
            assert result.exit_code == 0
            
            # Check JSON report structure
            json_path = Path('reports/license-header-upgrade-report.json')
            assert json_path.exists()
            
            with open(json_path) as f:
                report = json.load(f)
            
            assert 'timestamp' in report
            assert report['mode'] == 'upgrade'
            assert 'summary' in report
            assert 'files' in report
            
            # Check summary fields
            summary = report['summary']
            assert 'upgraded' in summary
            assert 'already_target' in summary
            assert 'no_source_header' in summary
    
    def test_upgrade_reports_markdown_content(self):
        """Test that upgrade reports have correct Markdown content."""
        with self.runner.isolated_filesystem():
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            Path('test.py').write_text('# Old Copyright\ncode\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt',
                '--output', 'reports'
            ])
            
            assert result.exit_code == 0
            
            # Check Markdown report content
            md_path = Path('reports/license-header-upgrade-report.md')
            assert md_path.exists()
            
            content = md_path.read_text()
            assert '# License Header Upgrade Report' in content
            assert 'Summary' in content
            assert 'Upgraded' in content
    
    def test_upgrade_file_io_error_handling(self):
        """Test that upgrade handles file I/O errors gracefully."""
        import os
        
        with self.runner.isolated_filesystem():
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            
            # Create a read-only directory to cause I/O errors
            readonly_dir = Path('readonly')
            readonly_dir.mkdir()
            test_file = readonly_dir / 'test.py'
            test_file.write_text('# Old Copyright\ncode\n')
            
            # Make directory read-only (file can be read but not written)
            if os.name != 'nt':  # Skip on Windows
                os.chmod(readonly_dir, 0o555)
                
                try:
                    result = self.runner.invoke(main, [
                        'upgrade',
                        '--from-header', 'OLD_HEADER.txt',
                        '--to-header', 'NEW_HEADER.txt'
                    ])
                    
                    # Should report the failed file in output
                    assert 'Failed: 1' in result.output or 'error' in result.output.lower()
                    # File should remain unchanged due to I/O error
                    assert '# Old Copyright' in test_file.read_text()
                finally:
                    # Restore permissions for cleanup
                    os.chmod(readonly_dir, 0o755)
    
    def test_upgrade_with_binary_files_skipped(self):
        """Test that upgrade skips binary files gracefully."""
        with self.runner.isolated_filesystem():
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            
            # Create a valid text file
            Path('test.py').write_text('# Old Copyright\ncode\n')
            
            # Create a binary file with .py extension
            Path('binary.py').write_bytes(b'\x00\x01\x02\x03binary')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt'
            ])
            
            assert result.exit_code == 0
            # Text file should be upgraded
            assert '# New Copyright' in Path('test.py').read_text()
            # Binary file should be unchanged
            assert Path('binary.py').read_bytes() == b'\x00\x01\x02\x03binary'
    
    def test_upgrade_nonexistent_directory(self):
        """Test that upgrade handles nonexistent directory gracefully."""
        with self.runner.isolated_filesystem():
            Path('OLD_HEADER.txt').write_text('# Old Copyright\n')
            Path('NEW_HEADER.txt').write_text('New Copyright\n')
            
            result = self.runner.invoke(main, [
                'upgrade',
                '--from-header', 'OLD_HEADER.txt',
                '--to-header', 'NEW_HEADER.txt',
                '--path', 'nonexistent_dir'
            ])
            
            # Should fail or show no files processed
            # The exact behavior depends on implementation
            assert 'Upgraded: 0' in result.output or result.exit_code != 0


class TestCheckCommandExtended:
    """Extended tests for check command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_check_fails_on_missing_header(self):
        """Test that check fails when files are missing headers."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright 2025\n')
            Path('missing.py').write_text('print("no header")\n')
            
            result = self.runner.invoke(main, ['check', '--header', 'HEADER.txt'])
            assert result.exit_code == 1
            assert 'Non-compliant: 1' in result.output
    
    def test_check_succeeds_on_compliant_files(self):
        """Test that check succeeds when all files have headers."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright 2025\n')
            Path('compliant.py').write_text('# Copyright 2025\nprint("has header")\n')
            
            result = self.runner.invoke(main, ['check', '--header', 'HEADER.txt'])
            assert result.exit_code == 0
            assert 'Compliant: 1' in result.output
    
    def test_check_with_multi_language_headers(self):
        """Test check with different language comment styles."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('Copyright 2025\n')
            
            # Create compliant files with correct comment styles
            Path('test.py').write_text('# Copyright 2025\ncode\n')
            Path('test.js').write_text('// Copyright 2025\ncode\n')
            
            result = self.runner.invoke(main, ['check', '--header', 'HEADER.txt'])
            assert result.exit_code == 0
            assert 'Compliant: 2' in result.output
    
    def test_check_output_reports(self):
        """Test check command with output reports."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright 2025\n')
            Path('test.py').write_text('# Copyright 2025\ncode\n')
            
            result = self.runner.invoke(main, [
                'check', '--header', 'HEADER.txt', '--output', 'reports'
            ])
            
            assert result.exit_code == 0
            assert Path('reports/license-header-check-report.json').exists()
            assert Path('reports/license-header-check-report.md').exists()


class TestApplyCommandExtended:
    """Extended tests for apply command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_apply_multi_language_correct_wrapping(self):
        """Test apply wraps headers correctly for multiple languages."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('Copyright 2025\n')
            
            Path('test.py').write_text('code\n')
            Path('test.js').write_text('code\n')
            Path('test.rs').write_text('code\n')
            
            result = self.runner.invoke(main, ['apply', '--header', 'HEADER.txt'])
            assert result.exit_code == 0
            
            # Verify correct comment styles
            assert '# Copyright 2025' in Path('test.py').read_text()
            assert '// Copyright 2025' in Path('test.js').read_text()
            assert '// Copyright 2025' in Path('test.rs').read_text()
    
    def test_apply_dry_run_shows_would_modify(self):
        """Test apply dry-run shows files that would be modified."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright 2025\n')
            Path('needs_header.py').write_text('print("hello")\n')
            Path('has_header.py').write_text('# Copyright 2025\nprint("hello")\n')
            
            result = self.runner.invoke(main, [
                'apply', '--header', 'HEADER.txt', '--dry-run'
            ])
            
            assert result.exit_code == 0
            assert '[DRY RUN]' in result.output
            assert 'Added: 1' in result.output
            assert 'Compliant: 1' in result.output
            
            # File should NOT be modified
            assert 'Copyright' not in Path('needs_header.py').read_text()
    
    def test_apply_idempotent_multiple_runs(self):
        """Test that apply is idempotent across multiple runs."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright 2025\n')
            Path('test.py').write_text('print("hello")\n')
            
            # First run
            result1 = self.runner.invoke(main, ['apply', '--header', 'HEADER.txt'])
            assert result1.exit_code == 0
            content1 = Path('test.py').read_text()
            
            # Second run
            result2 = self.runner.invoke(main, ['apply', '--header', 'HEADER.txt'])
            assert result2.exit_code == 0
            content2 = Path('test.py').read_text()
            
            # Content should be identical
            assert content1 == content2
            assert 'Compliant: 1' in result2.output
    
    def test_apply_output_reports(self):
        """Test apply command with output reports."""
        with self.runner.isolated_filesystem():
            Path('HEADER.txt').write_text('# Copyright 2025\n')
            Path('test.py').write_text('print("hello")\n')
            
            result = self.runner.invoke(main, [
                'apply', '--header', 'HEADER.txt', '--output', 'reports'
            ])
            
            assert result.exit_code == 0
            assert Path('reports/license-header-apply-report.json').exists()
            assert Path('reports/license-header-apply-report.md').exists()
