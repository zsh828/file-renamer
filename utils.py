#!/usr/bin/env python3
"""
Utility Functions for File Renamer

This module provides utility functions for:
- File pattern matching and filtering
- Safe file system operations
- Validation of patterns and paths
- Duplicate detection
"""

import fnmatch
import os
from pathlib import Path
from typing import List, Set


def validate_pattern(pattern: str) -> bool:
    """
    Validate that a glob pattern is syntactically correct.
    
    Args:
        pattern: Glob pattern string (e.g., '*.txt', 'report_*.doc')
    
    Returns:
        True if pattern is valid, False otherwise
    
    Examples:
        >>> validate_pattern("*.txt")
        True
        >>> validate_pattern("[invalid")
        False
    """
    try:
        # Try to compile the pattern to check syntax
        import re
        # Convert glob pattern to regex for validation
        regex_pattern = fnmatch.translate(pattern)
        re.compile(regex_pattern)
        return True
    except Exception:
        return False


def find_files(
    root_path: Path,
    pattern: str,
    recursive: bool = False,
    verbose: bool = False,
) -> List[Path]:
    """
    Find all files matching the specified pattern.
    
    Args:
        root_path: Starting directory path
        pattern: Glob pattern to match files
        recursive: If True, search subdirectories recursively
        verbose: Enable verbose output
    
    Returns:
        List of Path objects matching the pattern
    
    Raises:
        ValueError: If root_path is not a directory
    
    Examples:
        >>> find_files(Path("/tmp"), "*.py", recursive=False)
        [Path('/tmp/file1.py'), Path('/tmp/file2.py')]
    """
    if not root_path.is_dir():
        raise ValueError(f"Root path must be a directory: {root_path}")
    
    files = []
    
    if recursive:
        # Recursive search using glob with **/
        search_pattern = f"**/{pattern}"
        search_path = root_path
        
        if verbose:
            print(f"Searching recursively in {search_path}...")
        
        try:
            for file_path in search_path.glob(search_pattern):
                if file_path.is_file():
                    files.append(file_path)
        except Exception as e:
            print(f"Warning: Error during recursive search: {e}")
            # Fall back to non-recursive if recursive fails
            for file_path in root_path.glob(pattern):
                if file_path.is_file():
                    files.append(file_path)
    else:
        # Non-recursive search
        for file_path in root_path.glob(pattern):
            if file_path.is_file():
                files.append(file_path)
    
    # Sort files for consistent ordering
    files.sort()
    
    return files


def is_safe_filename(filename: str) -> bool:
    """
    Check if a filename is safe (no special characters or reserved names).
    
    Args:
        filename: Filename to check
    
    Returns:
        True if filename is considered safe, False otherwise
    
    Note:
        This is a basic check. Platform-specific reserved names are not checked.
    """
    # Check for empty name
    if not filename or filename.strip() == "":
        return False
    
    # Check for control characters
    for char in filename:
        if ord(char) < 32 or ord(char) > 126:
            return False
    
    # Check for problematic characters (basic check)
    problematic_chars = ['\0', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in problematic_chars:
        if char in filename:
            return False
    
    return True


def detect_duplicates(files: List[Path]) -> dict:
    """
    Detect duplicate filenames in a list of paths.
    
    Useful for identifying potential conflicts when combining results from
    multiple searches or before renaming operations.
    
    Args:
        files: List of file paths to check
    
    Returns:
        Dictionary mapping filename -> list of paths with that name
    
    Examples:
        >>> files = [Path('/a/f.txt'), Path('/b/f.txt'), Path('/c/g.txt')]
        >>> duplicates = detect_duplicates(files)
        >>> duplicates['f.txt']
        [PosixPath('/a/f.txt'), PosixPath('/b/f.txt')]
    """
    name_to_paths: dict[str, List[Path]] = {}
    
    for file_path in files:
        name = file_path.name
        if name not in name_to_paths:
            name_to_paths[name] = []
        name_to_paths[name].append(file_path)
    
    # Filter to only include actual duplicates
    return {name: paths for name, paths in name_to_paths.items() if len(paths) > 1}


def check_for_overwrites(
    source_files: List[Path],
    new_filenames: List[str],
    base_dir: Path,
) -> dict:
    """
    Check which new filenames would overwrite existing files.
    
    Args:
        source_files: Original file paths
        new_filenames: Proposed new filenames
        base_dir: Base directory where files will be moved/renamed
    
    Returns:
        Dictionary mapping old_filename -> new_filename for conflicts
    """
    conflicts = {}
    
    for old_name, new_name in zip(source_files, new_filenames):
        destination = base_dir / new_name
        if destination.exists() and destination not in source_files:
            conflicts[old_name.name] = new_name
    
    return conflicts


def get_file_size_info(files: List[Path]) -> dict:
    """
    Get size information for a list of files.
    
    Args:
        files: List of file paths
    
    Returns:
        Dictionary mapping file_path -> size_in_bytes
    
    Examples:
        >>> sizes = get_file_size_info([Path('/etc/passwd')])
        >>> sizes[Path('/etc/passwd')]
        1234
    """
    return {f: f.stat().st_size for f in files if f.exists()}


def calculate_total_size(files: List[Path]) -> int:
    """
    Calculate total size of all files.
    
    Args:
        files: List of file paths
    
    Returns:
        Total size in bytes
    """
    total = 0
    for file_path in files:
        if file_path.exists():
            total += file_path.stat().st_size
    return total


def format_size(size_bytes: int) -> str:
    """
    Format size in bytes to human-readable string.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Human-readable size string (e.g., "1.5 MB")
    
    Examples:
        >>> format_size(1024)
        '1.0 KB'
        >>> format_size(1572864)
        '1.5 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def safe_rename_check(
    source: Path,
    destination: Path,
    force: bool = False,
) -> tuple[bool, str | None]:
    """
    Perform pre-rename safety checks.
    
    Args:
        source: Source file path
        destination: Destination file path
        force: Whether to allow overwriting
    
    Returns:
        Tuple of (is_safe, error_message)
        - If is_safe is True, error_message is None
        - If is_safe is False, error_message explains the issue
    """
    # Source must exist
    if not source.exists():
        return False, f"Source does not exist: {source}"
    
    if not source.is_file():
        return False, f"Source is not a file: {source}"
    
    # Check destination
    if destination.exists():
        if not force:
            return False, f"Destination already exists: {destination}"
        # If force, it's okay but warn
        return True, "Overwriting existing file (--force)"
    
    # Check if source == destination (no change needed)
    if source.resolve() == destination.resolve():
        return False, "Source and destination are the same file"
    
    return True, None


def validate_path_writable(path: Path) -> tuple[bool, str | None]:
    """
    Check if a path is writable.
    
    Args:
        path: Path to check
    
    Returns:
        Tuple of (is_writable, error_message)
    """
    # Create parent directory if it doesn't exist
    parent = path.parent
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return False, f"Cannot create parent directory: {e}"
    
    # Try to create a test file
    test_file = parent / f".rename_test_{os.getpid()}"
    try:
        test_file.touch(exist_ok=True)
        test_file.unlink()
        return True, None
    except OSError as e:
        return False, f"Directory not writable: {e}"


def filter_by_extension(files: List[Path], extensions: List[str]) -> List[Path]:
    """
    Filter files by their extensions.
    
    Args:
        files: List of file paths
        extensions: List of extensions to include (without dot, e.g., ['txt', 'py'])
    
    Returns:
        Filtered list of files
    
    Examples:
        >>> files = [Path('a.txt'), Path('b.py'), Path('c.txt')]
        >>> filter_by_extension(files, ['txt'])
        [PosixPath('a.txt'), PosixPath('c.txt')]
    """
    ext_lower = [ext.lower().lstrip('.') for ext in extensions]
    return [f for f in files if f.suffix.lstrip('.').lower() in ext_lower]


def sort_files_by_date(files: List[Path], reverse: bool = False) -> List[Path]:
    """
    Sort files by modification time.
    
    Args:
        files: List of file paths
        reverse: If True, sort newest first
    
    Returns:
        Sorted list of files
    """
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=reverse)
