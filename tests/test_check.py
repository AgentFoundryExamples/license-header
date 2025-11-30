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
Tests for check module.
"""

import tempfile
import pytest
from pathlib import Path

from license_header.check import check_file_header, check_headers, CheckResult
from license_header.config import Config


class TestCheckResult:
    """Test CheckResult dataclass."""
    
    def test_check_result_defaults(self):
        """Test CheckResult with default values."""
        result = CheckResult()
        assert result.compliant_files == []
        assert result.non_compliant_files == []
        assert result.skipped_files == []
        assert result.failed_files == []
    
    def test_total_eligible(self):
        """Test total_eligible calculation."""
        result = CheckResult()
        result.compliant_files = [Path('a.py'), Path('b.py')]
        result.non_compliant_files = [Path('c.py')]
        result.skipped_files = [Path('d.bin')]
        assert result.total_eligible() == 3
    
    def test_total_scanned(self):
        """Test total_scanned calculation."""
        result = CheckResult()
        result.compliant_files = [Path('a.py')]
        result.non_compliant_files = [Path('b.py')]
        result.skipped_files = [Path('c.bin')]
        result.failed_files = [Path('d.py')]
        assert result.total_scanned() == 4
    
    def test_is_compliant_all_compliant(self):
        """Test is_compliant when all files are compliant."""
        result = CheckResult()
        result.compliant_files = [Path('a.py'), Path('b.py')]
        assert result.is_compliant() is True
    
    def test_is_compliant_with_non_compliant(self):
        """Test is_compliant when there are non-compliant files."""
        result = CheckResult()
        result.compliant_files = [Path('a.py')]
        result.non_compliant_files = [Path('b.py')]
        assert result.is_compliant() is False
    
    def test_is_compliant_with_failed(self):
        """Test is_compliant when there are failed files."""
        result = CheckResult()
        result.compliant_files = [Path('a.py')]
        result.failed_files = [Path('b.py')]
        assert result.is_compliant() is False


class TestCheckFileHeader:
    """Test check_file_header function."""
    
    def test_file_with_header(self):
        """Test checking a file that has the header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create file with header
            header = '# Copyright 2024\n'
            file_path = tmpdir_path / 'test.py'
            file_path.write_text(f'{header}print("hello")\n')
            
            # Check file
            assert check_file_header(file_path, header) is True
    
    def test_file_without_header(self):
        """Test checking a file that doesn't have the header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create file without header
            header = '# Copyright 2024\n'
            file_path = tmpdir_path / 'test.py'
            file_path.write_text('print("hello")\n')
            
            # Check file
            assert check_file_header(file_path, header) is False
    
    def test_file_with_shebang_and_header(self):
        """Test checking a file with shebang and header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create file with shebang and header
            header = '# Copyright 2024\n'
            file_path = tmpdir_path / 'test.py'
            file_path.write_text(f'#!/usr/bin/env python\n{header}print("hello")\n')
            
            # Check file
            assert check_file_header(file_path, header) is True
    
    def test_nonexistent_file(self):
        """Test checking a nonexistent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / 'nonexistent.py'
            header = '# Copyright 2024\n'
            
            # Should raise OSError
            with pytest.raises(OSError):
                check_file_header(file_path, header)


class TestCheckHeaders:
    """Test check_headers function."""
    
    def test_all_compliant(self):
        """Test checking when all files are compliant."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create header file
            header = '# Copyright 2024\n'
            header_file = tmpdir_path / 'HEADER.txt'
            header_file.write_text(header)
            
            # Create compliant Python files
            (tmpdir_path / 'file1.py').write_text(f'{header}print("1")\n')
            (tmpdir_path / 'file2.py').write_text(f'{header}print("2")\n')
            
            # Create config
            config = Config(header_file=str(header_file))
            config._repo_root = tmpdir_path
            config._header_content = header
            config.path = '.'
            config.include_extensions = ['.py']
            config.exclude_paths = []
            
            # Check headers
            result = check_headers(config)
            
            assert len(result.compliant_files) == 2
            assert len(result.non_compliant_files) == 0
            assert result.is_compliant() is True
    
    def test_some_non_compliant(self):
        """Test checking when some files are non-compliant."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create header file
            header = '# Copyright 2024\n'
            header_file = tmpdir_path / 'HEADER.txt'
            header_file.write_text(header)
            
            # Create one compliant and one non-compliant file
            (tmpdir_path / 'compliant.py').write_text(f'{header}print("ok")\n')
            (tmpdir_path / 'non_compliant.py').write_text('print("missing header")\n')
            
            # Create config
            config = Config(header_file=str(header_file))
            config._repo_root = tmpdir_path
            config._header_content = header
            config.path = '.'
            config.include_extensions = ['.py']
            config.exclude_paths = []
            
            # Check headers
            result = check_headers(config)
            
            assert len(result.compliant_files) == 1
            assert len(result.non_compliant_files) == 1
            assert result.is_compliant() is False
    
    def test_skipped_files(self):
        """Test that binary and excluded files are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create header file
            header = '# Copyright 2024\n'
            header_file = tmpdir_path / 'HEADER.txt'
            header_file.write_text(header)
            
            # Create compliant Python file
            (tmpdir_path / 'file.py').write_text(f'{header}print("ok")\n')
            
            # Create binary file
            (tmpdir_path / 'file.pyc').write_bytes(b'\x00\x01\x02\x03')
            
            # Create excluded directory and file
            excluded_dir = tmpdir_path / 'node_modules'
            excluded_dir.mkdir()
            (excluded_dir / 'lib.py').write_text('console.log("excluded")\n')
            
            # Create config
            config = Config(header_file=str(header_file))
            config._repo_root = tmpdir_path
            config._header_content = header
            config.path = '.'
            config.include_extensions = ['.py', '.pyc']
            config.exclude_paths = ['node_modules']
            
            # Check headers
            result = check_headers(config)
            
            assert len(result.compliant_files) == 1
            assert len(result.non_compliant_files) == 0
            # Skipped files include binary and excluded
            assert len(result.skipped_files) > 0
    
    def test_empty_directory(self):
        """Test checking an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create header file
            header = '# Copyright 2024\n'
            header_file = tmpdir_path / 'HEADER.txt'
            header_file.write_text(header)
            
            # Create config for empty directory
            config = Config(header_file=str(header_file))
            config._repo_root = tmpdir_path
            config._header_content = header
            config.path = '.'
            config.include_extensions = ['.py']
            config.exclude_paths = []
            
            # Check headers
            result = check_headers(config)
            
            assert len(result.compliant_files) == 0
            assert len(result.non_compliant_files) == 0
            assert result.is_compliant() is True
