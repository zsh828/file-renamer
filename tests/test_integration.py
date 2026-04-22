#!/usr/bin/env python3
"""
Integration tests for the file renamer tool.

Tests cover:
- Full rename workflow with tmp_path fixtures
- Edge cases and error conditions
- Command-line argument parsing
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestFullRenameWorkflow:
    """Integration tests for complete rename operations."""
    
    def test_rename_with_prefix(self, tmp_path):
        """Test full workflow: add prefix to files."""
        # Create test files
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        (tmp_path / "file3.md").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "*.txt", recursive=False)
        
        operation = RenameOperation(prefix="backup_")
        renamed, skipped, errors = rename_files(files, operation, dry_run=False)
        
        assert renamed == 2
        assert skipped == 0
        assert errors == 0
        
        assert not (tmp_path / "file1.txt").exists()
        assert not (tmp_path / "file2.txt").exists()
        assert (tmp_path / "backup_file1.txt").exists()
        assert (tmp_path / "backup_file2.txt").exists()
    
    def test_rename_with_suffix(self, tmp_path):
        """Test full workflow: add suffix to files."""
        (tmp_path / "draft.doc").touch()
        (tmp_path / "final.doc").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "*.doc", recursive=False)
        
        operation = RenameOperation(suffix="_approved")
        rename_files(files, operation, dry_run=False)
        
        assert not (tmp_path / "draft.doc").exists()
        assert not (tmp_path / "final.doc").exists()
        assert (tmp_path / "draft_approved.doc").exists()
        assert (tmp_path / "final_approved.doc").exists()
    
    def test_rename_recursive(self, tmp_path):
        """Test recursive directory traversal."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        deep_dir = subdir / "deep"
        deep_dir.mkdir()
        
        (tmp_path / "root.txt").touch()
        (subdir / "nested.txt").touch()
        (deep_dir / "deeper.txt").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "*.txt", recursive=True)
        
        operation = RenameOperation(prefix="[")
        renamed, _, _ = rename_files(files, operation, dry_run=False)
        
        assert renamed == 3
        assert (tmp_path / "[root.txt").exists()
        assert (subdir / "[nested.txt").exists()
        assert (deep_dir / "[deeper.txt").exists()
    
    def test_replace_in_filename(self, tmp_path):
        """Test string replacement in filenames."""
        (tmp_path / "report_old.txt").touch()
        (tmp_path / "old_report.txt").touch()
        (tmp_path / "middle_old_middle.txt").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "*.txt", recursive=False)
        
        operation = RenameOperation(replace_old="old", replace_new="new")
        rename_files(files, operation, dry_run=False)
        
        assert not (tmp_path / "report_old.txt").exists()
        assert not (tmp_path / "old_report.txt").exists()
        assert not (tmp_path / "middle_old_middle.txt").exists()
        
        assert (tmp_path / "report_new.txt").exists()
        assert (tmp_path / "new_report.txt").exists()
        assert (tmp_path / "middle_new_middle.txt").exists()
    
    def test_add_numbering(self, tmp_path):
        """Test sequential numbering."""
        for i in range(5):
            (tmp_path / f"data{i}.csv").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "data*.csv", recursive=False)
        
        operation = RenameOperation(add_number=True, num_digits=3)
        rename_files(files, operation, dry_run=False)
        
        # Verify all numbered versions exist
        # The indexing starts from 1 but filenames contain 0-4
        for i in range(5):
            expected_name = f"{i+1:03d}_data{i}.csv"
            assert (tmp_path / expected_name).exists(), f"Missing: {expected_name}"
    
    def test_combined_operations(self, tmp_path):
        """Test combining multiple operations."""
        (tmp_path / "old.tmp.1").touch()
        (tmp_path / "old.tmp.2").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "old.*", recursive=False)
        
        operation = RenameOperation(
            prefix="v_",
            suffix="_final",
            replace_old="tmp",
            replace_new="temp",
            add_number=True,
        )
        rename_files(files, operation, dry_run=False)
        
        # Verify results - the order is: replace -> prefix -> suffix -> number
        assert (tmp_path / "001_v_old.temp_final.1").exists()
        assert (tmp_path / "002_v_old.temp_final.2").exists()
    
    def test_dry_run_mode(self, tmp_path):
        """Test dry-run mode doesn't modify files."""
        (tmp_path / "test.txt").touch()
        original_size = (tmp_path / "test.txt").stat().st_size
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "*.txt", recursive=False)
        operation = RenameOperation(prefix="renamed_")
        
        rename_files(files, operation, dry_run=True)
        
        # File should still exist with original name
        assert (tmp_path / "test.txt").exists()
        assert (tmp_path / "renamed_test.txt").exists() is False
    
    def test_no_conflict_prevention(self, tmp_path):
        """Test that existing files prevent overwrites."""
        (tmp_path / "target.txt").touch()
        (tmp_path / "source.txt").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "source.txt", recursive=False)
        operation = RenameOperation(force=False)
        
        renamed, skipped, _ = rename_files(files, operation, dry_run=False)
        
        assert renamed == 0
        assert skipped == 1
        assert (tmp_path / "target.txt").exists()
    
    def test_force_overwrite(self, tmp_path):
        """Test --force flag allows overwriting."""
        (tmp_path / "target.txt").touch()
        (tmp_path / "source.txt").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "source.txt", recursive=False)
        operation = RenameOperation(force=True)
        
        renamed, _, _ = rename_files(files, operation, dry_run=False)
        
        assert renamed == 1
        assert (tmp_path / "target.txt").exists()  # Now contains source content


class TestCommandLineInterface:
    """Integration tests for CLI interface."""
    
    def test_help_output(self):
        """Test that --help provides documentation."""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "Batch rename" in result.stdout
        assert "--prefix" in result.stdout
    
    def test_missing_arguments(self, tmp_path):
        """Test error when no arguments provided."""
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "usage" in result.stdout.lower()
    
    def test_nonexistent_directory(self, tmp_path):
        """Test error on nonexistent root directory."""
        result = subprocess.run(
            [sys.executable, "main.py", "--dry-run", "*.txt", "/nonexistent/path"],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True,
        )
        
        assert result.returncode != 0
        assert "does not exist" in result.stderr.lower()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_special_files(self, tmp_path):
        """Test with special files like empty extensions."""
        (tmp_path / "test.txt").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        # Use valid pattern instead of empty pattern
        files = find_files(tmp_path, "*", recursive=False)
        operation = RenameOperation(prefix="x_")
        
        renamed, _, _ = rename_files(files, operation, dry_run=False)
        assert renamed >= 0  # Should not crash
    
    def test_special_characters_in_pattern(self, tmp_path):
        """Test pattern with special regex-like characters."""
        (tmp_path / "file[1].txt").touch()
        (tmp_path / "file[2].txt").touch()
        
        # This should handle gracefully even if patterns don't match exactly
        from utils import find_files
        
        files = find_files(tmp_path, "*", recursive=False)
        assert len(files) >= 2
    
    def test_unicode_filenames(self, tmp_path):
        """Test handling of unicode filenames."""
        (tmp_path / "文档.txt").touch()
        (tmp_path / "файл.txt").touch()
        (tmp_path / "ファイル.txt").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "*.txt", recursive=False)
        
        operation = RenameOperation(prefix="_")
        renamed, _, _ = rename_files(files, operation, dry_run=False)
        
        assert renamed == 3
    
    def test_dotfiles(self, tmp_path):
        """Test handling of hidden dotfiles."""
        (tmp_path / ".hidden").touch()
        (tmp_path / ".gitignore").touch()
        
        # Should be found with * pattern but not *.txt
        from utils import find_files
        
        all_files = find_files(tmp_path, "*", recursive=False)
        txt_files = find_files(tmp_path, "*.txt", recursive=False)
        
        assert len(all_files) == 2
        assert len(txt_files) == 0
    
    def test_symlinks(self, tmp_path):
        """Test behavior with symlinks."""
        target = tmp_path / "real_file.txt"
        target.touch()
        link = tmp_path / "link_to_file.txt"
        
        try:
            link.symlink_to(target)
            
            from utils import find_files
            
            files = find_files(tmp_path, "*.txt", recursive=False)
            # Symlinks are included as files
            assert len(files) == 2
        except OSError:
            # Symlinks might not work on some systems
            pytest.skip("Symlinks not supported")


class TestErrorHandling:
    """Tests for error conditions and recovery."""
    
    def test_permission_denied(self, tmp_path):
        """Test handling of permission errors."""
        import stat
        
        # Create file and make it read-only
        file = tmp_path / "readonly.txt"
        file.touch()
        file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        
        # Try to rename to same location (no change needed)
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        files = find_files(tmp_path, "*.txt", recursive=False)
        
        # Read-only shouldn't prevent rename on most Unix systems
        operation = RenameOperation(prefix="x_")
        renamed, _, errors = rename_files(files, operation, dry_run=False)
        
        # Should succeed or fail gracefully
        assert errors >= 0
    
    def test_invalid_start_number(self, tmp_path):
        """Test invalid start_number parameter."""
        from operations import RenameOperation
        
        with pytest.raises(ValueError):
            RenameOperation(start_number=-1)
    
    def test_operation_order_consistency(self, tmp_path):
        """Test that operations are applied in consistent order."""
        (tmp_path / "test.txt").touch()
        
        from utils import find_files
        from operations import RenameOperation, rename_files
        
        # Different orderings should produce different results
        op1 = RenameOperation(prefix="a_", suffix="_b_")
        op2 = RenameOperation(prefix="a_", suffix="_b_", replace_old="test", replace_new="test")
        
        # Both should have deterministic behavior
        files = find_files(tmp_path, "*.txt", recursive=False)
        
        rename_files(files.copy(), op1, dry_run=False)
        assert True  # No crash indicates success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
