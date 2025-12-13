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
Tests for reports module.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path

from license_header.reports import (
    generate_json_report,
    generate_markdown_report,
    generate_reports,
    _format_file_list
)
from license_header.apply import ApplyResult
from license_header.check import CheckResult


class TestFormatFileList:
    """Test _format_file_list helper function."""
    
    def test_format_without_repo_root(self):
        """Test formatting file list without repo root."""
        files = [Path('/tmp/a.py'), Path('/tmp/b.py')]
        result = _format_file_list(files)
        assert result == ['/tmp/a.py', '/tmp/b.py']
    
    def test_format_with_repo_root(self):
        """Test formatting file list with repo root."""
        repo_root = Path('/tmp/project')
        files = [Path('/tmp/project/src/a.py'), Path('/tmp/project/test/b.py')]
        result = _format_file_list(files, repo_root)
        assert result == ['src/a.py', 'test/b.py']
    
    def test_format_with_limit(self):
        """Test formatting file list with limit."""
        files = [Path(f'/tmp/file{i}.py') for i in range(10)]
        result = _format_file_list(files, limit=5)
        assert len(result) == 5


class TestGenerateJsonReport:
    """Test generate_json_report function."""
    
    def test_generate_apply_report(self):
        """Test generating JSON report for apply mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create result
            result = ApplyResult()
            result.modified_files = [Path(tmpdir) / 'a.py']
            result.already_compliant = [Path(tmpdir) / 'b.py']
            result.skipped_files = [Path(tmpdir) / 'c.bin']
            
            # Generate report
            output_path = tmpdir_path / 'report.json'
            generate_json_report(result, output_path, 'apply', tmpdir_path)
            
            # Verify report was created
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                report_data = json.load(f)
            
            assert report_data['mode'] == 'apply'
            assert 'timestamp' in report_data
            assert report_data['summary']['modified'] == 1
            assert report_data['summary']['compliant'] == 1
            assert report_data['summary']['skipped'] == 1
            assert len(report_data['files']['modified']) == 1
    
    def test_generate_check_report(self):
        """Test generating JSON report for check mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create result
            result = CheckResult()
            result.compliant_files = [Path(tmpdir) / 'a.py']
            result.non_compliant_files = [Path(tmpdir) / 'b.py']
            result.skipped_files = [Path(tmpdir) / 'c.bin']
            
            # Generate report
            output_path = tmpdir_path / 'report.json'
            generate_json_report(result, output_path, 'check', tmpdir_path)
            
            # Verify report was created
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                report_data = json.load(f)
            
            assert report_data['mode'] == 'check'
            assert 'timestamp' in report_data
            assert report_data['summary']['compliant'] == 1
            assert report_data['summary']['non_compliant'] == 1
            assert report_data['summary']['skipped'] == 1
            assert len(report_data['files']['compliant']) == 1
            assert len(report_data['files']['non_compliant']) == 1
    
    def test_generate_report_creates_directory(self):
        """Test that report generation creates parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create result
            result = ApplyResult()
            
            # Generate report in nested directory
            output_path = tmpdir_path / 'reports' / 'nested' / 'report.json'
            generate_json_report(result, output_path, 'apply')
            
            # Verify directory and report were created
            assert output_path.parent.exists()
            assert output_path.exists()


class TestGenerateMarkdownReport:
    """Test generate_markdown_report function."""
    
    def test_generate_apply_report(self):
        """Test generating Markdown report for apply mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create result
            result = ApplyResult()
            result.modified_files = [Path(tmpdir) / 'a.py']
            result.already_compliant = [Path(tmpdir) / 'b.py']
            
            # Generate report
            output_path = tmpdir_path / 'report.md'
            generate_markdown_report(result, output_path, 'apply', tmpdir_path)
            
            # Verify report was created
            assert output_path.exists()
            
            # Verify content
            content = output_path.read_text()
            assert '# License Header Apply Report' in content
            assert 'Summary' in content
            assert 'Modified Files' in content
            assert 'Already Compliant Files' in content
    
    def test_generate_check_report(self):
        """Test generating Markdown report for check mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create result
            result = CheckResult()
            result.compliant_files = [Path(tmpdir) / 'a.py']
            result.non_compliant_files = [Path(tmpdir) / 'b.py']
            
            # Generate report
            output_path = tmpdir_path / 'report.md'
            generate_markdown_report(result, output_path, 'check', tmpdir_path)
            
            # Verify report was created
            assert output_path.exists()
            
            # Verify content
            content = output_path.read_text()
            assert '# License Header Check Report' in content
            assert 'Summary' in content
            assert 'Non-Compliant Files' in content
            assert 'Compliant Files' in content
    
    def test_generate_report_creates_directory(self):
        """Test that report generation creates parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create result
            result = CheckResult()
            
            # Generate report in nested directory
            output_path = tmpdir_path / 'reports' / 'nested' / 'report.md'
            generate_markdown_report(result, output_path, 'check')
            
            # Verify directory and report were created
            assert output_path.parent.exists()
            assert output_path.exists()
    
    def test_large_file_list_truncation(self):
        """Test that large file lists are truncated in Markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create result with many compliant files
            result = CheckResult()
            result.compliant_files = [Path(tmpdir) / f'file{i}.py' for i in range(150)]
            
            # Generate report
            output_path = tmpdir_path / 'report.md'
            generate_markdown_report(result, output_path, 'check', tmpdir_path)
            
            # Verify truncation message is present
            content = output_path.read_text()
            assert '... and 50 more' in content


class TestGenerateReports:
    """Test generate_reports function."""
    
    def test_generate_both_reports(self):
        """Test generating both JSON and Markdown reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / 'reports'
            
            # Create result
            result = ApplyResult()
            result.modified_files = [Path(tmpdir) / 'a.py']
            
            # Generate reports
            generate_reports(result, output_dir, 'apply', tmpdir_path)
            
            # Verify both reports were created
            json_report = output_dir / 'license-header-apply-report.json'
            md_report = output_dir / 'license-header-apply-report.md'
            assert json_report.exists()
            assert md_report.exists()
    
    def test_generate_reports_creates_directory(self):
        """Test that generate_reports creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / 'new_reports'
            
            # Create result
            result = CheckResult()
            
            # Generate reports
            generate_reports(result, output_dir, 'check', tmpdir_path)
            
            # Verify directory was created
            assert output_dir.exists()
            assert output_dir.is_dir()
    
    def test_generate_reports_unwritable_directory(self):
        """Test error handling for unwritable directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / 'readonly'
            output_dir.mkdir()
            
            # Make directory read-only
            os.chmod(output_dir, 0o444)
            
            try:
                # Create result
                result = ApplyResult()
                
                # Should raise OSError
                with pytest.raises(OSError) as exc_info:
                    generate_reports(result, output_dir, 'apply')
                
                assert 'not writable' in str(exc_info.value)
            finally:
                # Restore permissions for cleanup
                os.chmod(output_dir, 0o755)
    
    def test_generate_reports_invalid_path(self):
        """Test error handling for invalid path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Use a file as output directory
            invalid_path = tmpdir_path / 'file.txt'
            invalid_path.write_text('content')
            
            # Create result
            result = CheckResult()
            
            # Should raise OSError
            with pytest.raises(OSError) as exc_info:
                generate_reports(result, invalid_path, 'check')
            
            assert 'not a directory' in str(exc_info.value)


class TestUpgradeReports:
    """Test upgrade mode report generation."""
    
    def test_generate_upgrade_json_report(self):
        """Test generating JSON report for upgrade mode."""
        from license_header.apply import UpgradeResult
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create upgrade result
            result = UpgradeResult()
            result.upgraded_files = [Path(tmpdir) / 'upgraded.py']
            result.already_target = [Path(tmpdir) / 'already_target.py']
            result.no_source_header = [Path(tmpdir) / 'no_source.py']
            result.skipped_files = [Path(tmpdir) / 'skipped.bin']
            result.failed_files = []
            
            # Generate report
            output_path = tmpdir_path / 'report.json'
            generate_json_report(result, output_path, 'upgrade', tmpdir_path)
            
            # Verify report was created
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                report_data = json.load(f)
            
            assert report_data['mode'] == 'upgrade'
            assert 'timestamp' in report_data
            assert report_data['summary']['upgraded'] == 1
            assert report_data['summary']['already_target'] == 1
            assert report_data['summary']['no_source_header'] == 1
            assert len(report_data['files']['upgraded']) == 1
    
    def test_generate_upgrade_markdown_report(self):
        """Test generating Markdown report for upgrade mode."""
        from license_header.apply import UpgradeResult
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create upgrade result
            result = UpgradeResult()
            result.upgraded_files = [Path(tmpdir) / 'upgraded.py']
            result.already_target = [Path(tmpdir) / 'already_target.py']
            result.no_source_header = [Path(tmpdir) / 'no_source.py']
            
            # Generate report
            output_path = tmpdir_path / 'report.md'
            generate_markdown_report(result, output_path, 'upgrade', tmpdir_path)
            
            # Verify report was created
            assert output_path.exists()
            
            # Verify content
            content = output_path.read_text()
            assert '# License Header Upgrade Report' in content
            assert 'Summary' in content
            assert 'Upgraded' in content
            assert 'Already Target' in content or 'already_target' in content.lower()
    
    def test_upgrade_reports_deterministic_output(self):
        """Test that upgrade reports are deterministic."""
        from license_header.apply import UpgradeResult
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create identical results
            def create_result():
                result = UpgradeResult()
                result.upgraded_files = [
                    Path(tmpdir) / 'b.py',
                    Path(tmpdir) / 'a.py',
                    Path(tmpdir) / 'c.py',
                ]
                return result
            
            # Generate reports twice
            result1 = create_result()
            output1 = tmpdir_path / 'report1.json'
            generate_json_report(result1, output1, 'upgrade', tmpdir_path)
            
            result2 = create_result()
            output2 = tmpdir_path / 'report2.json'
            generate_json_report(result2, output2, 'upgrade', tmpdir_path)
            
            # Compare files (excluding timestamp)
            with open(output1) as f:
                data1 = json.load(f)
            with open(output2) as f:
                data2 = json.load(f)
            
            # Summary and files should be identical
            assert data1['summary'] == data2['summary']
            assert data1['files'] == data2['files']


class TestReportFileListFormatting:
    """Test file list formatting in reports."""
    
    def test_relative_paths_in_reports(self):
        """Test that reports use relative paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create nested directory structure
            nested = tmpdir_path / 'src' / 'pkg'
            nested.mkdir(parents=True)
            
            result = ApplyResult()
            result.modified_files = [nested / 'file.py']
            
            output_path = tmpdir_path / 'report.json'
            generate_json_report(result, output_path, 'apply', tmpdir_path)
            
            with open(output_path) as f:
                data = json.load(f)
            
            # Path should be relative
            modified = data['files']['modified']
            assert len(modified) == 1
            assert modified[0] == 'src/pkg/file.py'
    
    def test_large_file_list_json_not_truncated(self):
        """Test that JSON reports include all files (not truncated)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create result with many files
            result = CheckResult()
            result.compliant_files = [
                Path(tmpdir) / f'file{i}.py' for i in range(200)
            ]
            
            output_path = tmpdir_path / 'report.json'
            generate_json_report(result, output_path, 'check', tmpdir_path)
            
            with open(output_path) as f:
                data = json.load(f)
            
            # JSON should have ALL files
            assert len(data['files']['compliant']) == 200
    
    def test_markdown_truncation_message(self):
        """Test that Markdown reports show truncation message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create result with many files
            result = CheckResult()
            result.compliant_files = [
                Path(tmpdir) / f'file{i}.py' for i in range(150)
            ]
            
            output_path = tmpdir_path / 'report.md'
            generate_markdown_report(result, output_path, 'check', tmpdir_path)
            
            content = output_path.read_text()
            
            # Should show truncation message
            assert '... and 50 more' in content
