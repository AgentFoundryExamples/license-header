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
        assert '0.2.0' in result.output
    
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
