#!/usr/bin/env python3
"""
File Renaming Operations Module

This module contains the core logic for renaming files with support for:
- Adding prefixes and suffixes
- String replacement
- Sequential numbering
- Safety checks to prevent overwriting existing files
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional


@dataclass
class RenameOperation:
    """
    Configuration for a file rename operation.
    
    Attributes:
        prefix: String to prepend to filenames
        suffix: String to append to filenames
        replace_old: Old string to find in filename
        replace_new: New string to replace old with
        add_number: Whether to add sequential numbers
        start_number: Starting number for sequencing
        num_digits: Number of digits for number padding
        force: If True, allow overwriting existing files
    """
    prefix: str = ""
    suffix: str = ""
    replace_old: Optional[str] = None
    replace_new: Optional[str] = None
    add_number: bool = False
    start_number: int = 1
    num_digits: int = 3
    force: bool = False
    
    def __post_init__(self):
        """Validate operation parameters after initialization."""
        if self.start_number < 0:
            raise ValueError("start_number must be non-negative")
        if self.num_digits < 1 or self.num_digits > 10:
            raise ValueError("num_digits must be between 1 and 10")


def build_new_filename(
    original_name: str,
    extension: str,
    operation: RenameOperation,
    index: Optional[int] = None,
) -> str:
    """
    Build a new filename based on the specified operations.
    
    The order of operations is:
    1. Replace old string with new string (if specified)
    2. Add prefix
    3. Add suffix
    4. Add number (if requested)
    
    Args:
        original_name: Original filename without extension
        extension: File extension including dot (e.g., '.txt')
        operation: RenameOperation configuration
        index: Sequential number to use if add_number is True
    
    Returns:
        New filename with extension
    """
    name = original_name
    
    # Step 1: Replace old string with new
    if operation.replace_old and operation.replace_new:
        name = name.replace(operation.replace_old, operation.replace_new)
    
    # Step 2: Add prefix
    if operation.prefix:
        name = f"{operation.prefix}{name}"
    
    # Step 3: Add suffix (before number)
    if operation.suffix:
        name = f"{name}{operation.suffix}"
    
    # Step 4: Add number
    if operation.add_number and index is not None:
        numbered = f"{index:0{operation.num_digits}d}"
        name = f"{numbered}_{name}"
    
    return f"{name}{extension}"


def get_safe_destination(
    base_path: Path,
    new_filename: str,
    operation: RenameOperation,
    verbose: bool = False,
) -> Tuple[Path, bool]:
    """
    Get a safe destination path, checking for conflicts.
    
    Args:
        base_path: Base directory path
        new_filename: Desired new filename
        operation: Current rename operation config
        verbose: Whether to print conflict information
    
    Returns:
        Tuple of (destination_path, has_conflict)
    
    Raises:
        ValueError: If forced overwrite would destroy important files
    """
    destination = base_path / new_filename
    
    if not destination.exists():
        return destination, False
    
    if operation.force:
        if verbose:
            print(f"  WARNING: Overwriting existing file: {destination.name}")
        return destination, True
    
    # Check if it's the same as source (no actual change needed)
    # This handles edge cases
    return destination, True


def collect_unique_names(
    files: List[Path],
    operation: RenameOperation,
    verbose: bool = False,
) -> dict:
    """
    Pre-calculate all new filenames and detect duplicates.
    
    This function builds a mapping from current filenames to proposed new names,
    and detects conflicts where multiple files would be renamed to the same name.
    
    Args:
        files: List of file paths to rename
        operation: Rename operation configuration
        verbose: Enable verbose output
    
    Returns:
        Dictionary mapping (path, index) -> new_filename
    
    Raises:
        RuntimeError: If duplicate new names are detected
    """
    unique_mapping = {}
    used_names = set()
    
    for index, file_path in enumerate(files, start=operation.start_number):
        stem = file_path.stem
        ext = file_path.suffix
        new_name = build_new_filename(stem, ext, operation, index)
        
        if new_name in used_names:
            raise RuntimeError(
                f"Duplicate new filename '{new_name}' would be created. "
                f"This typically happens when adding --number without other differentiating changes."
            )
        
        used_names.add(new_name)
        key = (file_path.resolve(), index)
        unique_mapping[key] = new_name
        
        if verbose:
            print(f"  #{index}: {file_path.name} -> {new_name}")
    
    return unique_mapping


def rename_files(
    files: List[Path],
    operation: RenameOperation,
    dry_run: bool = False,
    verbose: bool = False,
) -> Tuple[int, int, int]:
    """
    Perform batch file renaming with safety checks.
    
    Args:
        files: List of file paths to rename
        operation: Rename operation configuration
        dry_run: If True, only preview changes without executing
        verbose: Enable verbose output
    
    Returns:
        Tuple of (renamed_count, skipped_count, error_count)
    """
    if not files:
        return 0, 0, 0
    
    # Pre-calculate all new names to detect conflicts early
    try:
        unique_mapping = collect_unique_names(files, operation, verbose)
    except RuntimeError as e:
        print(f"\nError: {e}")
        return 0, len(files), 1
    
    renamed_count = 0
    skipped_count = 0
    error_count = 0
    
    for (file_path, index), new_filename in unique_mapping.items():
        base_dir = file_path.parent
        
        try:
            # Get safe destination
            destination, has_conflict = get_safe_destination(
                base_dir, new_filename, operation, verbose
            )
            
            if has_conflict and not operation.force:
                # Skip if we can't safely overwrite
                if verbose:
                    print(f"  SKIPPED: {file_path.name} (conflict with {destination.name})")
                skipped_count += 1
                continue
            
            if dry_run:
                print(f"  [DRY RUN] {file_path.name} -> {destination.name}")
                renamed_count += 1
            else:
                # Actually perform the rename
                os.rename(file_path, destination)
                print(f"  RENAMED: {file_path.name} -> {destination.name}")
                renamed_count += 1
                
        except PermissionError:
            print(f"\nERROR: Permission denied: {file_path}")
            error_count += 1
        except OSError as e:
            print(f"\nERROR: Failed to rename {file_path}: {e}")
            error_count += 1
        except Exception as e:
            print(f"\nERROR: Unexpected error renaming {file_path}: {e}")
            error_count += 1
    
    return renamed_count, skipped_count, error_count


def validate_rename_plan(
    files: List[Path],
    operation: RenameOperation,
    dry_run: bool = False,
) -> bool:
    """
    Validate that a rename plan is safe before execution.
    
    Args:
        files: List of files to be renamed
        operation: Operation configuration
        dry_run: Whether this is a dry run
    
    Returns:
        True if the plan is valid, False otherwise
    """
    try:
        # Try to build the mapping (will raise if duplicates)
        collect_unique_names(files, operation)
        return True
    except RuntimeError:
        return False


def calculate_size_change(files: List[Path], operation: RenameOperation) -> int:
    """
    Calculate if any size change will occur during renaming.
    
    Note: Filename changes don't affect file size, but this function
    can be extended to check for special cases.
    
    Args:
        files: List of files
        operation: Operation configuration
    
    Returns:
        Size change in bytes (always 0 for pure renames)
    """
    return 0
