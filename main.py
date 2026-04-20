#!/usr/bin/env python3
"""
File Batch Renamer - Command Line Interface

A powerful command-line tool for batch renaming files with support for
prefixes, suffixes, string replacement, numbering, and recursive directory traversal.

Usage:
    python main.py [OPTIONS] PATTERN ROOT_DIR

Examples:
    # Preview renaming *.txt files with prefix
    python main.py --dry-run --prefix "backup_" "*.txt" /path/to/dir
    
    # Recursively add numbers to all .pdf files
    python main.py --recursive --number "*.pdf" /documents
    
    # Replace old text with new in filenames
    python main.py --replace "old" "new" --suffix "_v2" "*.doc" ./docs
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from operations import rename_files, RenameOperation
from utils import find_files, validate_pattern


def parse_arguments() -> argparse.Namespace:
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch rename files with support for prefixes, suffixes, replacements, and numbering.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run --prefix "backup_" "*.txt" /path/to/dir
  %(prog)s --recursive --number "*.pdf" /documents
  %(prog)s --replace "old" "new" --suffix "_v2" "*.doc" ./docs
        """,
    )

    parser.add_argument(
        "pattern",
        type=str,
        help="Glob pattern to match files (e.g., '*.txt', 'report_*.doc')",
    )

    parser.add_argument(
        "root_dir",
        type=str,
        help="Root directory to start searching for files",
    )

    parser.add_argument(
        "--prefix",
        type=str,
        default="",
        help="Prefix to add to all matching filenames",
    )

    parser.add_argument(
        "--suffix",
        type=str,
        default="",
        help="Suffix to add to all matching filenames",
    )

    parser.add_argument(
        "--replace",
        nargs=2,
        metavar=("OLD", "NEW"),
        dest="replace_pairs",
        default=None,
        help="Replace OLD string with NEW in filenames (usage: --replace old new)",
    )

    parser.add_argument(
        "--number",
        action="store_true",
        help="Add sequential number to each filename",
    )

    parser.add_argument(
        "--start-number",
        type=int,
        default=1,
        help="Starting number for sequencing (default: 1)",
    )

    parser.add_argument(
        "--digits",
        type=int,
        default=3,
        help="Number of digits for padding (default: 3, i.e., 001, 002, ...)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without actually renaming files",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search subdirectories",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing files (not recommended)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.pattern:
        parser.error("Pattern is required")

    root_path = Path(args.root_dir)
    if not root_path.exists():
        parser.error(f"Root directory does not exist: {args.root_dir}")

    if not root_path.is_dir():
        parser.error(f"Root path is not a directory: {args.root_dir}")

    # Validate replace pairs
    if args.replace_pairs and len(args.replace_pairs) != 2:
        parser.error("--replace requires exactly two arguments: old_string new_string")

    # Validate digits
    if args.digits < 1 or args.digits > 10:
        parser.error("--digits must be between 1 and 10")

    return args


def validate_operations(args: argparse.Namespace) -> None:
    """Validate that at least one rename operation is specified."""
    has_operation = bool(
        args.prefix
        or args.suffix
        or args.replace_pairs
        or args.number
    )
    
    if not has_operation:
        print("\nWarning: No rename operations specified!")
        print("Use --prefix, --suffix, --replace, or --number to specify what to do.\n")
        sys.exit(1)


def main() -> int:
    """Main entry point for the file renamer tool."""
    try:
        args = parse_arguments()
        
        # Validate pattern
        if not validate_pattern(args.pattern):
            print(f"Error: Invalid glob pattern: {args.pattern}")
            return 1
        
        # Validate operations
        validate_operations(args)
        
        # Find matching files
        root_path = Path(args.root_dir).resolve()
        files_to_rename = find_files(root_path, args.pattern, args.recursive, args.verbose)
        
        if not files_to_rename:
            print(f"\nNo files found matching pattern '{args.pattern}' in {args.root_dir}")
            return 0
        
        print(f"\nFound {len(files_to_rename)} file(s) matching '{args.pattern}'\n")
        if args.verbose:
            for f in files_to_rename:
                print(f"  - {f}")
            print()
        
        # Build rename operation
        operation = RenameOperation(
            prefix=args.prefix,
            suffix=args.suffix,
            replace_old=args.replace_pairs[0] if args.replace_pairs else None,
            replace_new=args.replace_pairs[1] if args.replace_pairs else None,
            add_number=args.number,
            start_number=args.start_number,
            num_digits=args.digits,
            force=args.force,
        )
        
        # Perform rename
        renamed_count, skipped_count, error_count = rename_files(
            files=files_to_rename,
            operation=operation,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        
        # Print summary
        print("\n" + "=" * 50)
        print("Summary:")
        print(f"  Files renamed:   {renamed_count}")
        print(f"  Files skipped:   {skipped_count}")
        print(f"  Errors occurred: {error_count}")
        
        if args.dry_run:
            print("\n(DRY RUN - no actual changes were made)")
        
        if error_count > 0:
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
