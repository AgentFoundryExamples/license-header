"""
Tests for reports module.
"""

import json
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
            import os
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
