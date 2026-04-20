#!/usr/bin/env python3
"""
Unit tests for file renaming operations.

Tests cover:
- Prefix/suffix addition
- String replacement
- Numbering
- Edge cases and error handling
"""

import os
from pathlib import Path

import pytest

from operations import RenameOperation, build_new_filename, collect_unique_names


class TestBuildNewFilename:
    """Tests for build_new_filename function."""
    
    def test_no_operations(self):
        """Test with no operations - should return original filename."""
        result = build_new_filename("test", ".txt", RenameOperation())
        assert result == "test.txt"
    
    def test_prefix_only(self):
        """Test adding prefix only."""
        operation = RenameOperation(prefix="backup_")
        result = build_new_filename("document", ".docx", operation)
        assert result == "backup_document.docx"
    
    def test_suffix_only(self):
        """Test adding suffix only."""
        operation = RenameOperation(suffix="_final")
        result = build_new_filename("draft", ".md", operation)
        assert result == "draft_final.md"
    
    def test_prefix_and_suffix(self):
        """Test adding both prefix and suffix."""
        operation = RenameOperation(prefix="[", suffix="]")
        result = build_new_filename("file", ".txt", operation)
        assert result == "[file].txt"
    
    def test_replace_single_occurrence(self):
        """Test replacing string with single occurrence."""
        operation = RenameOperation(replace_old="old", replace_new="new")
        result = build_new_filename("old_file", ".txt", operation)
        assert result == "new_file.txt"
    
    def test_replace_multiple_occurrences(self):
        """Test replacing string with multiple occurrences."""
        operation = RenameOperation(replace_old="a", replace_new="b")
        result = build_new_filename("banana", ".txt", operation)
        assert result == "bbnbnb.txt"
    
    def test_number_with_padding(self):
        """Test adding number with digit padding."""
        operation = RenameOperation(add_number=True, num_digits=3)
        result = build_new_filename("report", ".pdf", operation, index=5)
        assert result == "005_report.pdf"
    
    def test_number_start_at_one(self):
        """Test numbering starting from 1."""
        operation = RenameOperation(add_number=True, start_number=1, num_digits=2)
        result = build_new_filename("file", ".txt", operation, index=1)
        assert result == "01_file.txt"
        result = build_new_filename("file2", ".txt", operation, index=10)
        assert result == "10_file2.txt"
    
    def test_all_operations_combined(self):
        """Test combining all operations in order."""
        operation = RenameOperation(
            prefix="archive_",
            suffix="_v2",
            replace_old="tmp",
            replace_new="final",
            add_number=True,
            num_digits=4,
        )
        result = build_new_filename("tmp_data", ".csv", operation, index=42)
        # Order: replace -> prefix -> suffix -> number
        # After replace: final_data
        # After prefix: archive_final_data
        # After suffix: archive_final_data_v2
        # After number: 0042_archive_final_data_v2.csv
        assert result == "0042_archive_final_data_v2.csv"
    
    def test_empty_extension(self):
        """Test with empty extension."""
        operation = RenameOperation(prefix="back_")
        result = build_new_filename("file", "", operation)
        assert result == "back_file"
    
    def test_multichar_extension(self):
        """Test with multi-character extension."""
        operation = RenameOperation(suffix="_copy")
        result = build_new_filename("image", ".tar.gz", operation)
        assert result == "image_copy.tar.gz"
    
    def test_unicode_filename(self):
        """Test with unicode characters in filename."""
        operation = RenameOperation(prefix="prefix_")
        result = build_new_filename("文档", ".txt", operation)
        # Prefix is attached directly to the filename
        assert result == "prefix_文档.txt"


class TestRenameOperationValidation:
    """Tests for RenameOperation validation."""
    
    def test_negative_start_number(self):
        """Test that negative start_number raises ValueError."""
        with pytest.raises(ValueError):
            RenameOperation(start_number=-1)
    
    def test_invalid_digits_low(self):
        """Test that digits < 1 raises ValueError."""
        with pytest.raises(ValueError):
            RenameOperation(num_digits=0)
    
    def test_invalid_digits_high(self):
        """Test that digits > 10 raises ValueError."""
        with pytest.raises(ValueError):
            RenameOperation(num_digits=11)
    
    def test_valid_operations(self):
        """Test valid boundary values."""
        op1 = RenameOperation(start_number=0, num_digits=1)
        assert op1.start_number == 0
        assert op1.num_digits == 1
        
        op2 = RenameOperation(start_number=999, num_digits=10)
        assert op2.start_number == 999
        assert op2.num_digits == 10


class TestCollectUniqueNames:
    """Tests for collect_unique_names function."""
    
    def test_basic_uniqueness(self, tmp_path):
        """Test that unique names are collected correctly."""
        # Create test files
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        
        files = [tmp_path / "file1.txt", tmp_path / "file2.txt"]
        operation = RenameOperation(prefix="renamed_")
        
        mapping = collect_unique_names(files, operation, verbose=False)
        
        assert len(mapping) == 2
        assert mapping[(files[0], 1)] == "renamed_file1.txt"
        assert mapping[(files[1], 2)] == "renamed_file2.txt"
    
    def test_duplicate_detection(self, tmp_path):
        """Test duplicate detection with numbering."""
        files = [tmp_path / f"{i}.txt" for i in range(3)]
        for f in files:
            f.touch()
        
        operation = RenameOperation(add_number=True, num_digits=2)
        mapping = collect_unique_names(files, operation, verbose=False)
        
        assert len(mapping) == 3
        # Index is based on enumerate starting from start_number (default=1)
        assert mapping[(files[0], 1)] == "01_0.txt"
        assert mapping[(files[1], 2)] == "02_1.txt"
        assert mapping[(files[2], 3)] == "03_2.txt"
    
    def test_empty_list(self, tmp_path):
        """Test with empty file list."""
        mapping = collect_unique_names([], RenameOperation(), verbose=False)
        assert mapping == {}
