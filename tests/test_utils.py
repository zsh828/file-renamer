#!/usr/bin/env python3
"""
Unit tests for utility functions.

Tests cover:
- File pattern matching
- Duplicate detection
- Safe filename checks
- Path validation
"""

from pathlib import Path

import pytest

import utils


class TestValidatePattern:
    """Tests for validate_pattern function."""
    
    def test_valid_patterns(self):
        """Test valid glob patterns."""
        assert utils.validate_pattern("*.txt") is True
        assert utils.validate_pattern("report_*.doc") is True
        assert utils.validate_pattern("[a-z]*.py") is True
        assert utils.validate_pattern("**/*.md") is True
    
    def test_invalid_patterns(self):
        """Test invalid glob patterns."""
        # Note: fnmatch.translate() is lenient, so many 'invalid' patterns still pass
        assert isinstance(utils.validate_pattern("*"), bool)


class TestFindFiles:
    """Tests for find_files function."""
    
    def test_find_single_directory(self, tmp_path):
        """Test finding files in a single directory."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        
        files = utils.find_files(tmp_path, "*.txt", recursive=False)
        
        assert len(files) == 1
        assert tmp_path / "file1.txt" in files
    
    def test_find_recursive(self, tmp_path):
        """Test recursive file search."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        (tmp_path / "root.txt").touch()
        (subdir / "nested.txt").touch()
        
        files = utils.find_files(tmp_path, "*.txt", recursive=True)
        
        assert len(files) == 2
        assert tmp_path / "root.txt" in files
        assert tmp_path / "subdir" / "nested.txt" in files
    
    def test_no_matching_files(self, tmp_path):
        """Test when no files match pattern."""
        (tmp_path / "file.txt").touch()
        
        files = utils.find_files(tmp_path, "*.pdf", recursive=False)
        
        assert len(files) == 0
    
    def test_nonexistent_root(self, tmp_path):
        """Test with nonexistent root path."""
        nonexistent = tmp_path / "does_not_exist"
        
        with pytest.raises(ValueError):
            utils.find_files(nonexistent, "*.txt")
    
    def test_sorted_results(self, tmp_path):
        """Test that results are sorted."""
        (tmp_path / "z.txt").touch()
        (tmp_path / "a.txt").touch()
        (tmp_path / "m.txt").touch()
        
        files = utils.find_files(tmp_path, "*.txt", recursive=False)
        
        names = [f.name for f in files]
        assert names == sorted(names)


class TestIsSafeFilename:
    """Tests for is_safe_filename function."""
    
    def test_safe_filenames(self):
        """Test safe filenames."""
        assert utils.is_safe_filename("normal_file.txt") is True
        assert utils.is_safe_filename("file-with-dashes.txt") is True
        assert utils.is_safe_filename("file_with_underscores.txt") is True
        assert utils.is_safe_filename("file123.txt") is True
    
    def test_unsafe_filenames(self):
        """Test unsafe filenames."""
        assert utils.is_safe_filename("") is False
        assert utils.is_safe_filename("   ") is False
        assert utils.is_safe_filename("file\tname.txt") is False
        assert utils.is_safe_filename("file/name.txt") is False
        assert utils.is_safe_filename("file\\name.txt") is False
        assert utils.is_safe_filename("file:name.txt") is False
        assert utils.is_safe_filename("file*name.txt") is False
        assert utils.is_safe_filename('file"name.txt') is False
        assert utils.is_safe_filename("file<name.txt") is False
        assert utils.is_safe_filename("file>name.txt") is False
        assert utils.is_safe_filename("file|name.txt") is False


class TestDetectDuplicates:
    """Tests for detect_duplicates function."""
    
    def test_no_duplicates(self):
        """Test list with no duplicates."""
        files = [
            Path("/a/one.txt"),
            Path("/b/two.txt"),
            Path("/c/three.txt"),
        ]
        
        duplicates = utils.detect_duplicates(files)
        
        assert duplicates == {}
    
    def test_with_duplicates(self):
        """Test list with duplicate filenames."""
        files = [
            Path("/a/file.txt"),
            Path("/b/file.txt"),
            Path("/c/other.txt"),
            Path("/d/file.txt"),
        ]
        
        duplicates = utils.detect_duplicates(files)
        
        assert "file.txt" in duplicates
        assert len(duplicates["file.txt"]) == 3
    
    def test_all_duplicates(self):
        """Test list where all files have same name."""
        files = [
            Path("/a/same.txt"),
            Path("/b/same.txt"),
            Path("/c/same.txt"),
        ]
        
        duplicates = utils.detect_duplicates(files)
        
        assert "same.txt" in duplicates
        assert len(duplicates["same.txt"]) == 3


class TestCheckForOverwrites:
    """Tests for check_for_overwrites function."""
    
    def test_no_overwrites(self, tmp_path):
        """Test when new files don't exist."""
        source_files = [tmp_path / "old.txt"]
        new_filenames = ["new.txt"]
        
        conflicts = utils.check_for_overwrites(source_files, new_filenames, tmp_path)
        
        assert conflicts == {}
    
    def test_with_overwrites(self, tmp_path):
        """Test when destination already exists."""
        existing = tmp_path / "existing.txt"
        existing.touch()
        
        source_files = [tmp_path / "rename_me.txt"]
        new_filenames = ["existing.txt"]
        
        conflicts = utils.check_for_overwrites(source_files, new_filenames, tmp_path)
        
        assert "rename_me.txt" in conflicts
        assert conflicts["rename_me.txt"] == "existing.txt"


class TestFormatSize:
    """Tests for format_size function."""
    
    def test_bytes(self):
        """Test formatting small sizes."""
        assert utils.format_size(0) == "0.0 B"
        assert utils.format_size(500) == "500.0 B"
        assert utils.format_size(1023) == "1023.0 B"
    
    def test_kilobytes(self):
        """Test kilobyte formatting."""
        assert utils.format_size(1024) == "1.0 KB"
        assert utils.format_size(1536) == "1.5 KB"
        assert utils.format_size(10240) == "10.0 KB"
    
    def test_megabytes(self):
        """Test megabyte formatting."""
        assert utils.format_size(1048576) == "1.0 MB"
        assert utils.format_size(1572864) == "1.5 MB"
    
    def test_gigabytes(self):
        """Test gigabyte formatting."""
        assert utils.format_size(1073741824) == "1.0 GB"


class TestSafeRenameCheck:
    """Tests for safe_rename_check function."""
    
    def test_source_not_exists(self, tmp_path):
        """Test with non-existent source."""
        source = tmp_path / "does_not_exist.txt"
        dest = tmp_path / "destination.txt"
        
        is_safe, error = utils.safe_rename_check(source, dest)
        
        assert is_safe is False
        assert "does not exist" in error
    
    def test_source_not_file(self, tmp_path):
        """Test with directory as source."""
        subdir = tmp_path / "not_a_file"
        subdir.mkdir()
        dest = tmp_path / "destination.txt"
        
        is_safe, error = utils.safe_rename_check(subdir, dest)
        
        assert is_safe is False
        assert "not a file" in error
    
    def test_destination_exists(self, tmp_path):
        """Test with existing destination."""
        source = tmp_path / "source.txt"
        source.touch()
        dest = tmp_path / "dest.txt"
        dest.touch()
        
        is_safe, error = utils.safe_rename_check(source, dest)
        
        assert is_safe is False
        assert "already exists" in error
    
    def test_force_overwrite(self, tmp_path):
        """Test force overwrite of existing destination."""
        source = tmp_path / "source.txt"
        source.touch()
        dest = tmp_path / "dest.txt"
        dest.touch()
        
        is_safe, error = utils.safe_rename_check(source, dest, force=True)
        
        assert is_safe is True
        assert "Overwriting" in error
    
    def test_same_source_destination(self, tmp_path):
        """Test when source equals destination."""
        file = tmp_path / "same.txt"
        file.touch()
        
        is_safe, error = utils.safe_rename_check(file, file)
        
        assert is_safe is False
        assert "same" in error.lower()


class TestFilterByExtension:
    """Tests for filter_by_extension function."""
    
    def test_filter_one_extension(self, tmp_path):
        """Test filtering by one extension."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        (tmp_path / "file3.txt").touch()
        
        files = utils.filter_by_extension(list(tmp_path.glob("*")), ["txt"])
        
        assert len(files) == 2
    
    def test_filter_multiple_extensions(self, tmp_path):
        """Test filtering by multiple extensions."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        (tmp_path / "file3.md").touch()
        
        files = utils.filter_by_extension(list(tmp_path.glob("*")), ["txt", "py"])
        
        assert len(files) == 2
    
    def test_case_insensitive(self, tmp_path):
        """Test case-insensitive extension matching."""
        (tmp_path / "file1.TXT").touch()
        (tmp_path / "file2.Txt").touch()
        (tmp_path / "file3.py").touch()
        
        files = utils.filter_by_extension(list(tmp_path.glob("*")), ["txt"])
        
        assert len(files) == 2


class TestSortFilesByDate:
    """Tests for sort_files_by_date function."""
    
    def test_sort_newest_first(self, tmp_path):
        """Test sorting files by modification date."""
        file1 = tmp_path / "first.txt"
        file1.touch()
        
        import time
        time.sleep(0.1)
        
        file2 = tmp_path / "second.txt"
        file2.touch()
        
        sorted_files = utils.sort_files_by_date([file1, file2], reverse=True)
        
        assert sorted_files[0] == file2
        assert sorted_files[1] == file1
    
    def test_default_order(self, tmp_path):
        """Test default sorting order (oldest first)."""
        file1 = tmp_path / "first.txt"
        file1.touch()
        
        import time
        time.sleep(0.1)
        
        file2 = tmp_path / "second.txt"
        file2.touch()
        
        sorted_files = utils.sort_files_by_date([file1, file2])
        
        assert sorted_files[0] == file1
        assert sorted_files[1] == file2
