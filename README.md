# File Batch Renamer

A powerful command-line tool for batch renaming files with support for prefixes, suffixes, string replacement, numbering, and recursive directory traversal.

## Features

- **Pattern Matching**: Find files using glob patterns (e.g., `*.txt`, `report_*.doc`)
- **Prefix/Suffix**: Add text before or after filenames
- **String Replacement**: Replace specific strings in filenames
- **Sequential Numbering**: Add numbered prefixes (001_, 002_, etc.)
- **Recursive Search**: Traverse subdirectories automatically
- **Dry Run Mode**: Preview changes before applying them
- **Safety Checks**: Prevent accidental file overwrites
- **Unicode Support**: Handle international characters

## Installation

```bash
# Clone or download to your preferred location
cd ~/projects/file-renamer

# No external dependencies required! Uses only Python standard library
python3 -m pip install pytest  # Optional: for running tests
```

## Usage

### Basic Syntax

```bash
python main.py [OPTIONS] PATTERN ROOT_DIR
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `PATTERN` | Glob pattern to match files (e.g., `*.txt`, `report_*.doc`) |
| `ROOT_DIR` | Root directory to start searching |

### Options

| Option | Description |
|--------|-------------|
| `--prefix TEXT` | Prefix to add to all filenames |
| `--suffix TEXT` | Suffix to append to all filenames |
| `--replace OLD NEW` | Replace `OLD` string with `NEW` in filenames |
| `--number` | Add sequential numbers to filenames |
| `--start-number N` | Starting number for sequencing (default: 1) |
| `--digits N` | Number of digits for padding (default: 3, e.g., 001) |
| `--dry-run` | Preview changes without actually renaming |
| `--recursive` | Recursively search subdirectories |
| `--verbose`, `-v` | Enable verbose output |
| `--force` | Force overwrite existing files (not recommended) |

## Examples

### 1. Add a prefix to backup files

```bash
python main.py --prefix "backup_" "*.txt" /path/to/documents
```

Result: `file.txt` → `backup_file.txt`

### 2. Recursively rename all PDFs with numbers

```bash
python main.py --recursive --number "*.pdf" /documents
```

Result: `report.pdf` → `001_report.pdf`, `manual.pdf` → `002_manual.pdf`

### 3. Replace text in filenames

```bash
python main.py --replace "old" "new" --suffix "_v2" "*.doc" ./docs
```

Result: `old_document.doc` → `new_document_v2.doc`

### 4. Preview changes first (dry run)

```bash
python main.py --dry-run --prefix "archive_" "**/*.md" /notes
```

Shows what would happen without making changes.

### 5. Complex combined operations

```bash
python main.py \
    --prefix "[" \
    --suffix "]" \
    --replace "tmp" "final" \
    --number \
    --digits 4 \
    "*.tmp"
```

Result: `data.tmp` → `[0001_data].tmp_final]`

## Safety Features

1. **Duplicate Detection**: Will error if multiple files would get the same name
2. **Overwrite Protection**: Won't overwrite existing files unless `--force` is used
3. **Dry Run Mode**: Preview changes before they're applied
4. **Verbose Output**: See exactly what will be renamed with `-v` flag

## Project Structure

```
file-renamer/
├── main.py           # CLI entry point and argument parsing
├── operations.py     # Core renaming logic
├── utils.py          # Utility functions (pattern matching, validation)
├── tests/
│   ├── __init__.py
│   ├── test_operations.py    # Unit tests for renaming logic
│   ├── test_utils.py         # Unit tests for utilities
│   └── test_integration.py   # Integration tests for full workflow
├── README.md         # This file
└── requirements.txt  # Dependencies (optional: pytest)
```

## Running Tests

```bash
# Install pytest
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_operations.py -v

# Run with coverage (if installed)
pytest tests/ -v --cov=operations --cov=utils --cov=main
```

## Implementation Details

### Operation Order

Operations are applied in this order:
1. **Replace** - Replace old string with new string
2. **Prefix** - Add prefix to filename
3. **Suffix** - Add suffix to filename
4. **Number** - Add sequential number at the beginning

### Edge Cases Handled

- Unicode filenames
- Hidden files (dotfiles)
- Files with no extension
- Multi-character extensions (e.g., `.tar.gz`)
- Empty directories
- Permission errors
- Symlinks (tested on Unix systems)

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/ -v`)
5. Submit a pull request
