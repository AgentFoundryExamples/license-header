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
Tests for configuration module.
"""

import json
import pytest
from pathlib import Path
from click import ClickException

from license_header.config import (
    Config,
    find_repo_root,
    load_config_file,
    validate_path_in_repo,
    load_header_content,
    merge_config,
    get_header_content,
)


class TestConfig:
    """Test Config dataclass."""
    
    def test_config_defaults(self):
        """Test that Config has sensible defaults."""
        config = Config(header_file="test.txt")
        assert config.header_file == "test.txt"
        assert '.py' in config.include_extensions
        assert 'node_modules' in config.exclude_paths
        assert config.dry_run is False
        assert config.mode == 'apply'
        

class TestFindRepoRoot:
    """Test find_repo_root function."""
    
    def test_find_repo_root_with_git(self, tmp_path):
        """Test finding repo root when .git exists."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        root = find_repo_root(subdir)
        assert root == tmp_path
    
    def test_find_repo_root_no_git(self, tmp_path):
        """Test finding repo root when no .git exists."""
        root = find_repo_root(tmp_path)
        assert root == tmp_path


class TestLoadConfigFile:
    """Test load_config_file function."""
    
    def test_load_valid_config(self, tmp_path):
        """Test loading a valid config file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "include_extensions": [".py", ".js"]
        }
        config_file.write_text(json.dumps(config_data))
        
        result = load_config_file(config_file)
        assert result["header_file"] == "HEADER.txt"
        assert result["include_extensions"] == [".py", ".js"]
    
    def test_load_nonexistent_config(self, tmp_path):
        """Test loading a non-existent config file."""
        config_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(ClickException) as exc_info:
            load_config_file(config_file)
        assert "not found" in str(exc_info.value)
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading an invalid JSON config file."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")
        
        with pytest.raises(ClickException) as exc_info:
            load_config_file(config_file)
        assert "Invalid JSON" in str(exc_info.value)


class TestValidatePathInRepo:
    """Test validate_path_in_repo function."""
    
    def test_valid_path_in_repo(self, tmp_path):
        """Test validating a path within the repo."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        # Should not raise
        validate_path_in_repo(subdir, tmp_path, "Test path")
    
    def test_path_outside_repo(self, tmp_path):
        """Test validating a path outside the repo."""
        outside_path = tmp_path.parent / "outside"
        
        with pytest.raises(ClickException) as exc_info:
            validate_path_in_repo(outside_path, tmp_path, "Test path")
        assert "traverses above repository root" in str(exc_info.value)


class TestLoadHeaderContent:
    """Test load_header_content function."""
    
    def test_load_existing_header(self, tmp_path):
        """Test loading an existing header file."""
        header_file = tmp_path / "HEADER.txt"
        header_content = "# Copyright 2025\n"
        header_file.write_text(header_content)
        
        result = load_header_content(str(header_file), tmp_path)
        assert result == header_content
    
    def test_load_relative_header(self, tmp_path):
        """Test loading a header file with relative path."""
        header_file = tmp_path / "HEADER.txt"
        header_content = "# License\n"
        header_file.write_text(header_content)
        
        result = load_header_content("HEADER.txt", tmp_path)
        assert result == header_content
    
    def test_load_nonexistent_header(self, tmp_path):
        """Test loading a non-existent header file."""
        with pytest.raises(ClickException) as exc_info:
            load_header_content("nonexistent.txt", tmp_path)
        assert "Header file not found" in str(exc_info.value)
    
    def test_load_header_outside_repo(self, tmp_path):
        """Test loading a header file outside the repo with absolute path."""
        # Create a header file outside the repo
        outside_path = tmp_path.parent / "outside.txt"
        outside_content = "# Absolute Path Header\n"
        outside_path.write_text(outside_content)
        
        # Absolute paths should be allowed for header files
        result = load_header_content(str(outside_path), tmp_path)
        assert result == outside_content
    
    def test_load_header_relative_outside_repo(self, tmp_path):
        """Test that relative paths escaping repo root are blocked."""
        # Try to use a relative path that escapes the repo
        with pytest.raises(ClickException) as exc_info:
            load_header_content("../outside.txt", tmp_path)
        assert "traverses above repository root" in str(exc_info.value)
    
    def test_load_header_without_newline(self, tmp_path):
        """Test loading a header file without trailing newline."""
        header_file = tmp_path / "HEADER.txt"
        header_content = "# Copyright 2025"  # No newline
        header_file.write_text(header_content)
        
        result = load_header_content(str(header_file), tmp_path)
        assert result == header_content


class TestMergeConfig:
    """Test merge_config function."""
    
    def test_merge_with_cli_only(self, tmp_path):
        """Test merging config with only CLI args."""
        # Create header file
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        cli_args = {
            'header': str(header_file),
            'path': '.',
            'dry_run': True,
        }
        
        config = merge_config(cli_args, repo_root=tmp_path)
        assert config.header_file == str(header_file)
        assert config.dry_run is True
    
    def test_merge_with_config_file(self, tmp_path):
        """Test merging config with config file."""
        # Create header file
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        # Create config file
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "include_extensions": [".py"],
            "exclude_paths": ["dist"]
        }
        config_file.write_text(json.dumps(config_data))
        
        cli_args = {}
        
        config = merge_config(cli_args, config_file_path=str(config_file), repo_root=tmp_path)
        assert config.header_file == "HEADER.txt"
        assert config.include_extensions == [".py"]
        assert config.exclude_paths == ["dist"]
    
    def test_merge_cli_overrides_config_file(self, tmp_path):
        """Test that CLI args override config file settings."""
        # Create header files
        header_file1 = tmp_path / "HEADER1.txt"
        header_file1.write_text("# Header 1\n")
        header_file2 = tmp_path / "HEADER2.txt"
        header_file2.write_text("# Header 2\n")
        
        # Create config file
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER1.txt",
            "include_extensions": [".py"],
        }
        config_file.write_text(json.dumps(config_data))
        
        cli_args = {
            'header': "HEADER2.txt",
            'include_extension': [".js", ".ts"],
        }
        
        config = merge_config(cli_args, config_file_path=str(config_file), repo_root=tmp_path)
        assert config.header_file == "HEADER2.txt"
        assert config.include_extensions == [".js", ".ts"]
    
    def test_merge_missing_header_file(self, tmp_path):
        """Test merging config without header file raises error."""
        cli_args = {}
        
        with pytest.raises(ClickException) as exc_info:
            merge_config(cli_args, repo_root=tmp_path)
        assert "Header file is required" in str(exc_info.value)
    
    def test_merge_with_default_config_file(self, tmp_path):
        """Test merging config with default config file."""
        # Create header file
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        # Create default config file
        config_file = tmp_path / "license-header.config.json"
        config_data = {
            "header_file": "HEADER.txt",
        }
        config_file.write_text(json.dumps(config_data))
        
        cli_args = {}
        
        config = merge_config(cli_args, repo_root=tmp_path)
        assert config.header_file == "HEADER.txt"
    
    def test_merge_with_default_license_header(self, tmp_path):
        """Test merging config with default LICENSE_HEADER file."""
        # Create default LICENSE_HEADER file
        header_file = tmp_path / "LICENSE_HEADER"
        header_content = "# Default Header\n"
        header_file.write_text(header_content)
        
        cli_args = {}
        
        config = merge_config(cli_args, repo_root=tmp_path)
        assert config.header_file == "LICENSE_HEADER"
        # Verify content was loaded
        assert get_header_content(config) == header_content
    
    def test_merge_cli_overrides_default_license_header(self, tmp_path):
        """Test that CLI header flag overrides default LICENSE_HEADER."""
        # Create both default and custom header files
        default_header = tmp_path / "LICENSE_HEADER"
        default_header.write_text("# Default\n")
        
        custom_header = tmp_path / "CUSTOM.txt"
        custom_header.write_text("# Custom\n")
        
        cli_args = {'header': 'CUSTOM.txt'}
        
        config = merge_config(cli_args, repo_root=tmp_path)
        assert config.header_file == "CUSTOM.txt"
    
    def test_merge_config_file_overrides_default_license_header(self, tmp_path):
        """Test that config file header overrides default LICENSE_HEADER."""
        # Create both default header and custom header
        default_header = tmp_path / "LICENSE_HEADER"
        default_header.write_text("# Default\n")
        
        custom_header = tmp_path / "CUSTOM.txt"
        custom_header.write_text("# Custom\n")
        
        # Create config file
        config_file = tmp_path / "license-header.config.json"
        config_data = {"header_file": "CUSTOM.txt"}
        config_file.write_text(json.dumps(config_data))
        
        cli_args = {}
        
        config = merge_config(cli_args, repo_root=tmp_path)
        assert config.header_file == "CUSTOM.txt"
    
    def test_merge_config_path_outside_repo_rejected(self, tmp_path):
        """Test that config file paths escaping repo root are rejected."""
        # Create header file
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        # Try to use a relative config path that escapes the repo
        cli_args = {}
        
        with pytest.raises(ClickException) as exc_info:
            merge_config(cli_args, config_file_path="../outside_config.json", repo_root=tmp_path)
        assert "Configuration file path" in str(exc_info.value)
        assert "traverses above repository root" in str(exc_info.value)


class TestGetHeaderContent:
    """Test get_header_content function."""
    
    def test_get_header_content(self, tmp_path):
        """Test getting header content from config."""
        header_file = tmp_path / "HEADER.txt"
        header_content = "# Copyright\n"
        header_file.write_text(header_content)
        
        cli_args = {'header': str(header_file)}
        config = merge_config(cli_args, repo_root=tmp_path)
        
        result = get_header_content(config)
        assert result == header_content
    
    def test_get_header_content_unloaded(self):
        """Test getting header content from unloaded config."""
        config = Config(header_file="test.txt")
        
        with pytest.raises(RuntimeError):
            get_header_content(config)


class TestHeaderVersionValidation:
    """Test header_version validation."""
    
    def test_valid_v2_header_version(self, tmp_path):
        """Test that V2 header version is valid for regular operations."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "header_version": "v2"
        }
        config_file.write_text(json.dumps(config_data))
        
        config = merge_config({}, config_file_path=str(config_file), repo_root=tmp_path)
        assert config.header_version == "v2"
    
    def test_v1_header_rejected_in_apply_mode(self, tmp_path):
        """Test that V1 header version is rejected in apply mode."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "header_version": "v1"
        }
        config_file.write_text(json.dumps(config_data))
        
        with pytest.raises(ClickException) as exc_info:
            merge_config({'mode': 'apply'}, config_file_path=str(config_file), repo_root=tmp_path)
        assert "v1" in str(exc_info.value)
        assert "upgrade" in str(exc_info.value).lower()
    
    def test_v1_header_rejected_in_check_mode(self, tmp_path):
        """Test that V1 header version is rejected in check mode."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "header_version": "v1"
        }
        config_file.write_text(json.dumps(config_data))
        
        with pytest.raises(ClickException) as exc_info:
            merge_config({'mode': 'check'}, config_file_path=str(config_file), repo_root=tmp_path)
        assert "v1" in str(exc_info.value)
    
    def test_invalid_header_version_rejected(self, tmp_path):
        """Test that unknown header version strings fail validation."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "header_version": "v3"
        }
        config_file.write_text(json.dumps(config_data))
        
        with pytest.raises(ClickException) as exc_info:
            merge_config({}, config_file_path=str(config_file), repo_root=tmp_path)
        assert "v3" in str(exc_info.value)
        assert "Valid options" in str(exc_info.value)
    
    def test_default_header_version_is_v2(self, tmp_path):
        """Test that default header version is V2."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config = merge_config({'header': str(header_file)}, repo_root=tmp_path)
        assert config.header_version == "v2"


class TestLanguageCommentOverrides:
    """Test language_comment_overrides validation."""
    
    def test_valid_language_overrides(self, tmp_path):
        """Test valid language comment overrides."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "language_comment_overrides": {
                ".py": "hash",
                ".js": "slash",
                ".c": "block"
            }
        }
        config_file.write_text(json.dumps(config_data))
        
        config = merge_config({}, config_file_path=str(config_file), repo_root=tmp_path)
        assert config.language_comment_overrides[".py"] == "hash"
        assert config.language_comment_overrides[".js"] == "slash"
        assert config.language_comment_overrides[".c"] == "block"
    
    def test_empty_language_overrides_uses_defaults(self, tmp_path):
        """Test that empty language overrides fall back to built-in defaults."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "language_comment_overrides": {}
        }
        config_file.write_text(json.dumps(config_data))
        
        config = merge_config({}, config_file_path=str(config_file), repo_root=tmp_path)
        assert config.language_comment_overrides == {}
    
    def test_invalid_extension_format_rejected(self, tmp_path):
        """Test that extensions without leading dot are rejected."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "language_comment_overrides": {
                "py": "hash"  # Missing leading dot
            }
        }
        config_file.write_text(json.dumps(config_data))
        
        with pytest.raises(ClickException) as exc_info:
            merge_config({}, config_file_path=str(config_file), repo_root=tmp_path)
        assert "py" in str(exc_info.value)
        assert "must start with '.'" in str(exc_info.value)
    
    def test_invalid_comment_style_rejected(self, tmp_path):
        """Test that invalid comment style values are rejected."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "language_comment_overrides": {
                ".py": "invalid_style"
            }
        }
        config_file.write_text(json.dumps(config_data))
        
        with pytest.raises(ClickException) as exc_info:
            merge_config({}, config_file_path=str(config_file), repo_root=tmp_path)
        assert "invalid_style" in str(exc_info.value)
        assert "Valid styles" in str(exc_info.value)


class TestUpgradeConfig:
    """Test upgrade configuration validation."""
    
    def test_upgrade_fields_stored_in_config(self, tmp_path):
        """Test that upgrade fields are stored in config when provided."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        from_header = tmp_path / "FROM.txt"
        from_header.write_text("# Old Header\n")
        to_header = tmp_path / "TO.txt"
        to_header.write_text("# New Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "upgrade_from_header": "FROM.txt",
            "upgrade_to_header": "TO.txt"
        }
        config_file.write_text(json.dumps(config_data))
        
        # Note: upgrade fields are only validated in 'upgrade' mode
        # In 'apply' mode, they are stored but with a warning
        config = merge_config({'mode': 'apply'}, config_file_path=str(config_file), repo_root=tmp_path)
        assert config.upgrade_from_header == "FROM.txt"
        assert config.upgrade_to_header == "TO.txt"
    
    def test_upgrade_path_outside_repo_rejected(self, tmp_path):
        """Test that relative upgrade paths outside repo root are rejected."""
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Header\n")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "header_file": "HEADER.txt",
            "upgrade_from_header": "../outside_from.txt",
            "upgrade_to_header": "TO.txt"
        }
        config_file.write_text(json.dumps(config_data))
        
        with pytest.raises(ClickException) as exc_info:
            merge_config({}, config_file_path=str(config_file), repo_root=tmp_path)
        assert "traverses above repository root" in str(exc_info.value)


class TestConfigNewFields:
    """Test Config dataclass new fields."""
    
    def test_config_with_new_fields(self):
        """Test Config dataclass with all new V2 fields."""
        config = Config(
            header_file="test.txt",
            header_version="v2",
            upgrade_from_header="from.txt",
            upgrade_to_header="to.txt",
            language_comment_overrides={".py": "hash", ".js": "slash"}
        )
        
        assert config.header_version == "v2"
        assert config.upgrade_from_header == "from.txt"
        assert config.upgrade_to_header == "to.txt"
        assert config.language_comment_overrides[".py"] == "hash"
        assert config.language_comment_overrides[".js"] == "slash"
    
    def test_config_default_new_fields(self):
        """Test Config dataclass default values for new fields."""
        config = Config(header_file="test.txt")
        
        assert config.header_version == "v2"
        assert config.upgrade_from_header is None
        assert config.upgrade_to_header is None
        assert config.language_comment_overrides == {}
