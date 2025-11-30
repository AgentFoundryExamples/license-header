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
Tests for multi-language comment wrapping functionality.
"""

import pytest
from pathlib import Path

from license_header.languages import (
    CommentStyle,
    LanguageInfo,
    DEFAULT_LANGUAGES,
    DEFAULT_EXTENSION_MAP,
    DEFAULT_FALLBACK_STYLE,
    PYTHON_STYLE,
    C_STYLE,
    RUST_STYLE,
    build_extension_map,
    get_language_for_extension,
    get_comment_style_for_extension,
    wrap_header_with_comments,
    unwrap_header_comments,
    is_header_already_wrapped,
)
from license_header.apply import prepare_header_for_file


class TestCommentStyle:
    """Test CommentStyle dataclass."""
    
    def test_line_comments_support(self):
        """Test detection of line comment support."""
        style = CommentStyle(line_prefix='# ')
        assert style.supports_line_comments()
        assert not style.supports_block_comments()
    
    def test_block_comments_support(self):
        """Test detection of block comment support."""
        style = CommentStyle(block_start='/*', block_end=' */')
        assert not style.supports_line_comments()
        assert style.supports_block_comments()
    
    def test_both_comments_support(self):
        """Test style with both line and block comment support."""
        style = C_STYLE
        assert style.supports_line_comments()
        assert style.supports_block_comments()


class TestDefaultLanguages:
    """Test default language definitions."""
    
    def test_python_language(self):
        """Test Python language definition."""
        assert 'python' in DEFAULT_LANGUAGES
        lang = DEFAULT_LANGUAGES['python']
        assert lang.name == 'Python'
        assert '.py' in lang.extensions
        assert lang.comment_style.line_prefix == '# '
    
    def test_c_language(self):
        """Test C language definition."""
        assert 'c' in DEFAULT_LANGUAGES
        lang = DEFAULT_LANGUAGES['c']
        assert lang.name == 'C'
        assert '.c' in lang.extensions
        assert '.h' in lang.extensions
        assert lang.comment_style.line_prefix == '// '
    
    def test_cpp_language(self):
        """Test C++ language definition."""
        assert 'cpp' in DEFAULT_LANGUAGES
        lang = DEFAULT_LANGUAGES['cpp']
        assert lang.name == 'C++'
        assert '.cpp' in lang.extensions
        assert '.hpp' in lang.extensions
    
    def test_csharp_language(self):
        """Test C# language definition."""
        assert 'csharp' in DEFAULT_LANGUAGES
        lang = DEFAULT_LANGUAGES['csharp']
        assert lang.name == 'C#'
        assert '.cs' in lang.extensions
    
    def test_java_language(self):
        """Test Java language definition."""
        assert 'java' in DEFAULT_LANGUAGES
        lang = DEFAULT_LANGUAGES['java']
        assert lang.name == 'Java'
        assert '.java' in lang.extensions
    
    def test_javascript_language(self):
        """Test JavaScript language definition."""
        assert 'javascript' in DEFAULT_LANGUAGES
        lang = DEFAULT_LANGUAGES['javascript']
        assert lang.name == 'JavaScript'
        assert '.js' in lang.extensions
        assert '.mjs' in lang.extensions
    
    def test_typescript_language(self):
        """Test TypeScript language definition."""
        assert 'typescript' in DEFAULT_LANGUAGES
        lang = DEFAULT_LANGUAGES['typescript']
        assert lang.name == 'TypeScript'
        assert '.ts' in lang.extensions
        assert '.tsx' in lang.extensions
    
    def test_rust_language(self):
        """Test Rust language definition."""
        assert 'rust' in DEFAULT_LANGUAGES
        lang = DEFAULT_LANGUAGES['rust']
        assert lang.name == 'Rust'
        assert '.rs' in lang.extensions


class TestExtensionMapping:
    """Test extension-to-language mapping."""
    
    def test_build_extension_map(self):
        """Test building extension map from language definitions."""
        ext_map = build_extension_map(DEFAULT_LANGUAGES)
        assert '.py' in ext_map
        assert ext_map['.py'] == 'python'
        assert '.c' in ext_map
        assert ext_map['.c'] == 'c'
    
    def test_get_language_for_extension(self):
        """Test getting language info for extension."""
        lang = get_language_for_extension('.py')
        assert lang is not None
        assert lang.name == 'Python'
    
    def test_get_language_unknown_extension(self):
        """Test getting language for unknown extension."""
        lang = get_language_for_extension('.xyz')
        assert lang is None
    
    def test_extension_case_insensitive(self):
        """Test that extension lookup is case-insensitive."""
        lang1 = get_language_for_extension('.py')
        lang2 = get_language_for_extension('.PY')
        lang3 = get_language_for_extension('.Py')
        assert lang1 == lang2 == lang3
    
    def test_extension_with_without_dot(self):
        """Test that extensions work with or without leading dot."""
        lang1 = get_language_for_extension('.py')
        lang2 = get_language_for_extension('py')
        assert lang1 == lang2


class TestGetCommentStyle:
    """Test getting comment style for extensions."""
    
    def test_python_comment_style(self):
        """Test Python comment style."""
        style = get_comment_style_for_extension('.py')
        assert style.line_prefix == '# '
    
    def test_c_comment_style(self):
        """Test C comment style."""
        style = get_comment_style_for_extension('.c')
        assert style.line_prefix == '// '
        assert style.block_start == '/*'
    
    def test_unknown_uses_fallback(self):
        """Test that unknown extension uses fallback style."""
        style = get_comment_style_for_extension('.xyz')
        assert style == DEFAULT_FALLBACK_STYLE
    
    def test_custom_fallback(self):
        """Test using custom fallback style."""
        custom_fallback = CommentStyle(line_prefix='// ')
        style = get_comment_style_for_extension('.xyz', fallback_style=custom_fallback)
        assert style == custom_fallback


class TestIsHeaderAlreadyWrapped:
    """Test detection of already-wrapped headers."""
    
    def test_hash_comment_detected(self):
        """Test detection of hash comment."""
        assert is_header_already_wrapped('# Copyright 2025\n')
    
    def test_slash_comment_detected(self):
        """Test detection of slash comment."""
        assert is_header_already_wrapped('// Copyright 2025\n')
    
    def test_block_comment_detected(self):
        """Test detection of block comment start."""
        assert is_header_already_wrapped('/* Copyright 2025 */\n')
    
    def test_star_prefix_detected(self):
        """Test detection of star prefix (inside block comment)."""
        assert is_header_already_wrapped(' * Copyright 2025\n')
    
    def test_raw_text_not_detected(self):
        """Test that raw text is not detected as wrapped."""
        assert not is_header_already_wrapped('Copyright 2025\n')
    
    def test_empty_string(self):
        """Test empty string."""
        assert not is_header_already_wrapped('')
    
    def test_inconsistent_prefixes_not_detected(self):
        """Test that headers with inconsistent prefixes are not detected as wrapped."""
        # First line looks like a comment, but subsequent lines don't match
        header = "# Copyright 2025\nThis is raw text\nMore raw text\n"
        assert not is_header_already_wrapped(header)
    
    def test_consistent_hash_comments(self):
        """Test that consistent hash comments are detected."""
        header = "# Copyright 2025\n# Licensed under MIT\n# All rights reserved\n"
        assert is_header_already_wrapped(header)
    
    def test_consistent_slash_comments(self):
        """Test that consistent slash comments are detected."""
        header = "// Copyright 2025\n// Licensed under MIT\n// All rights reserved\n"
        assert is_header_already_wrapped(header)
    
    def test_block_comment_style(self):
        """Test that block comment style is detected."""
        header = "/*\n * Copyright 2025\n * Licensed under MIT\n */"
        assert is_header_already_wrapped(header)
    
    def test_whitespace_only_header(self):
        """Test that whitespace-only header is not detected as wrapped."""
        assert not is_header_already_wrapped('   \n   \n   ')


class TestWrapHeaderWithComments:
    """Test header wrapping functionality."""
    
    def test_wrap_with_hash_comments(self):
        """Test wrapping with Python-style hash comments."""
        header = "Copyright 2025\nLicensed under MIT\n"
        result = wrap_header_with_comments(header, PYTHON_STYLE)
        assert result == "# Copyright 2025\n# Licensed under MIT\n"
    
    def test_wrap_with_slash_comments(self):
        """Test wrapping with C-style slash comments."""
        header = "Copyright 2025\nLicensed under MIT\n"
        result = wrap_header_with_comments(header, C_STYLE)
        assert result == "// Copyright 2025\n// Licensed under MIT\n"
    
    def test_wrap_with_block_comments(self):
        """Test wrapping with block comments."""
        header = "Copyright 2025\nLicensed under MIT\n"
        result = wrap_header_with_comments(header, C_STYLE, use_block_comments=True)
        assert '/*' in result
        assert ' * Copyright 2025' in result
        assert ' */' in result
    
    def test_skip_already_wrapped(self):
        """Test that already-wrapped headers are not re-wrapped."""
        header = "# Copyright 2025\n# Licensed under MIT\n"
        result = wrap_header_with_comments(header, PYTHON_STYLE)
        # Should not double-wrap
        assert result == header
        assert not result.startswith('# # ')
    
    def test_multiline_header(self):
        """Test wrapping multiline header."""
        header = "Line 1\nLine 2\nLine 3\n"
        result = wrap_header_with_comments(header, PYTHON_STYLE)
        assert result == "# Line 1\n# Line 2\n# Line 3\n"
    
    def test_empty_lines_preserved(self):
        """Test that empty lines are preserved."""
        header = "Line 1\n\nLine 2\n"
        result = wrap_header_with_comments(header, PYTHON_STYLE)
        lines = result.split('\n')
        assert lines[0] == '# Line 1'
        assert lines[1] == '#'  # Empty line gets just the prefix
        assert lines[2] == '# Line 2'
    
    def test_null_comment_style_raises_error(self):
        """Test that None comment_style raises ValueError."""
        header = "Copyright 2025\n"
        with pytest.raises(ValueError, match="comment_style parameter cannot be None"):
            wrap_header_with_comments(header, None)


class TestUnwrapHeaderComments:
    """Test header unwrapping functionality."""
    
    def test_unwrap_hash_comments(self):
        """Test unwrapping hash comments."""
        wrapped = "# Copyright 2025\n# Licensed under MIT\n"
        result = unwrap_header_comments(wrapped, PYTHON_STYLE)
        assert result == "Copyright 2025\nLicensed under MIT\n"
    
    def test_unwrap_slash_comments(self):
        """Test unwrapping slash comments."""
        wrapped = "// Copyright 2025\n// Licensed under MIT\n"
        result = unwrap_header_comments(wrapped, C_STYLE)
        assert result == "Copyright 2025\nLicensed under MIT\n"


class TestPrepareHeaderForFile:
    """Test prepare_header_for_file function."""
    
    def test_python_file(self):
        """Test header preparation for Python file."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.py"), wrap_comments=True
        )
        assert result == "# Copyright 2025\n"
    
    def test_javascript_file(self):
        """Test header preparation for JavaScript file."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.js"), wrap_comments=True
        )
        assert result == "// Copyright 2025\n"
    
    def test_java_file(self):
        """Test header preparation for Java file."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("Test.java"), wrap_comments=True
        )
        assert result == "// Copyright 2025\n"
    
    def test_c_file(self):
        """Test header preparation for C file."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.c"), wrap_comments=True
        )
        assert result == "// Copyright 2025\n"
    
    def test_rust_file(self):
        """Test header preparation for Rust file."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.rs"), wrap_comments=True
        )
        assert result == "// Copyright 2025\n"
    
    def test_csharp_file(self):
        """Test header preparation for C# file."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("Test.cs"), wrap_comments=True
        )
        assert result == "// Copyright 2025\n"
    
    def test_typescript_file(self):
        """Test header preparation for TypeScript file."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.ts"), wrap_comments=True
        )
        assert result == "// Copyright 2025\n"
    
    def test_unknown_extension_uses_fallback(self):
        """Test that unknown extension uses fallback style."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.xyz"), wrap_comments=True,
            fallback_style_name='hash'
        )
        assert result == "# Copyright 2025\n"
    
    def test_fallback_slash(self):
        """Test slash fallback style."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.xyz"), wrap_comments=True,
            fallback_style_name='slash'
        )
        assert result == "// Copyright 2025\n"
    
    def test_fallback_none(self):
        """Test no fallback style."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.xyz"), wrap_comments=True,
            fallback_style_name='none'
        )
        # Should return raw header
        assert result == "Copyright 2025\n"
    
    def test_wrap_disabled(self):
        """Test with comment wrapping disabled."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.py"), wrap_comments=False
        )
        # Should return raw header
        assert result == "Copyright 2025\n"
    
    def test_block_comments(self):
        """Test block comment mode."""
        header = "Copyright 2025\n"
        result = prepare_header_for_file(
            header, Path("test.c"), wrap_comments=True,
            use_block_comments=True
        )
        assert '/*' in result
        assert ' * Copyright 2025' in result


class TestMultiLanguageApply:
    """Test multi-language apply functionality with file system."""
    
    def test_python_and_javascript(self, tmp_path):
        """Test applying headers to Python and JavaScript files."""
        from license_header.apply import apply_headers
        from license_header.config import merge_config
        
        # Create raw header file (no comment markers)
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("Copyright 2025\n")
        
        # Create Python and JavaScript files
        (tmp_path / "test.py").write_text("print('hello')\n")
        (tmp_path / "test.js").write_text("console.log('hello');\n")
        
        # Configure
        cli_args = {'header': str(header_file)}
        config = merge_config(cli_args, repo_root=tmp_path)
        
        # Apply headers
        result = apply_headers(config)
        
        # Check results
        assert len(result.modified_files) == 2
        
        # Verify Python file has hash comments
        py_content = (tmp_path / "test.py").read_text()
        assert py_content.startswith("# Copyright 2025\n")
        
        # Verify JavaScript file has slash comments
        js_content = (tmp_path / "test.js").read_text()
        assert js_content.startswith("// Copyright 2025\n")
    
    def test_idempotency_with_wrapping(self, tmp_path):
        """Test that apply is idempotent with comment wrapping."""
        from license_header.apply import apply_headers
        from license_header.config import merge_config
        
        # Create raw header file
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("Copyright 2025\n")
        
        # Create Python file
        (tmp_path / "test.py").write_text("print('hello')\n")
        
        # Configure
        cli_args = {'header': str(header_file)}
        config = merge_config(cli_args, repo_root=tmp_path)
        
        # First application
        result1 = apply_headers(config)
        assert len(result1.modified_files) == 1
        content1 = (tmp_path / "test.py").read_text()
        
        # Second application
        result2 = apply_headers(config)
        assert len(result2.already_compliant) == 1
        content2 = (tmp_path / "test.py").read_text()
        
        # Content should be identical
        assert content1 == content2
    
    def test_legacy_commented_header(self, tmp_path):
        """Test that legacy header files with comments still work."""
        from license_header.apply import apply_headers
        from license_header.config import merge_config
        
        # Create header file WITH comment markers (legacy format)
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("# Copyright 2025\n")
        
        # Create Python file
        (tmp_path / "test.py").write_text("print('hello')\n")
        
        # Configure
        cli_args = {'header': str(header_file)}
        config = merge_config(cli_args, repo_root=tmp_path)
        
        # Apply headers
        result = apply_headers(config)
        
        # Check results
        assert len(result.modified_files) == 1
        
        # Verify Python file has the header (should NOT be double-wrapped)
        py_content = (tmp_path / "test.py").read_text()
        assert py_content.startswith("# Copyright 2025\n")
        assert not py_content.startswith("# # Copyright")  # No double wrapping
    
    def test_multiline_header_wrapping(self, tmp_path):
        """Test multiline header wrapping for different languages."""
        from license_header.apply import apply_headers
        from license_header.config import merge_config
        
        # Create multiline raw header
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("Copyright 2025\nLicensed under MIT\nAll rights reserved\n")
        
        # Create files for different languages
        (tmp_path / "test.py").write_text("print('hello')\n")
        (tmp_path / "test.js").write_text("console.log('hello');\n")
        (tmp_path / "test.c").write_text("int main() { return 0; }\n")
        (tmp_path / "test.rs").write_text("fn main() {}\n")
        
        # Configure
        cli_args = {'header': str(header_file)}
        config = merge_config(cli_args, repo_root=tmp_path)
        
        # Apply headers
        result = apply_headers(config)
        
        # Check Python
        py_content = (tmp_path / "test.py").read_text()
        assert "# Copyright 2025" in py_content
        assert "# Licensed under MIT" in py_content
        
        # Check JavaScript
        js_content = (tmp_path / "test.js").read_text()
        assert "// Copyright 2025" in js_content
        assert "// Licensed under MIT" in js_content
        
        # Check C
        c_content = (tmp_path / "test.c").read_text()
        assert "// Copyright 2025" in c_content
        
        # Check Rust
        rs_content = (tmp_path / "test.rs").read_text()
        assert "// Copyright 2025" in rs_content
    
    def test_shebang_preservation_with_wrapping(self, tmp_path):
        """Test that shebangs are preserved with comment wrapping."""
        from license_header.apply import apply_headers
        from license_header.config import merge_config
        
        # Create raw header
        header_file = tmp_path / "HEADER.txt"
        header_file.write_text("Copyright 2025\n")
        
        # Create Python script with shebang
        (tmp_path / "script.py").write_text("#!/usr/bin/env python\nprint('hello')\n")
        
        # Configure
        cli_args = {'header': str(header_file)}
        config = merge_config(cli_args, repo_root=tmp_path)
        
        # Apply headers
        result = apply_headers(config)
        
        # Check result
        assert len(result.modified_files) == 1
        content = (tmp_path / "script.py").read_text()
        
        # Shebang should come first
        assert content.startswith("#!/usr/bin/env python\n")
        # Header should follow
        assert "# Copyright 2025\n" in content
        # Code should be at the end
        assert "print('hello')" in content
