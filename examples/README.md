# RA-D-PS Examples

This directory contains example scripts demonstrating how to use the RA-D-PS package for various XML parsing and analysis tasks.

## Available Examples

### 1. `basic_parsing.py`
**Purpose**: Simple single-file XML parsing
**Use Case**: Parse a single XML file and export to Excel
**Requirements**: One XML file path

```bash
python examples/basic_parsing.py
```

### 2. `batch_processing.py`
**Purpose**: Process multiple XML files efficiently
**Use Case**: Batch processing of large XML collections with structure optimization
**Requirements**: Directory containing XML files

```bash
python examples/batch_processing.py
```

### 3. `database_integration.py`
**Purpose**: Store and analyze parsed data in SQLite database
**Use Case**: Long-term data storage, complex analysis, and reporting
**Requirements**: Directory containing XML files

```bash
python examples/database_integration.py
```

## Before Running Examples

1. **Update file paths**: Edit the example files to point to your actual XML files
2. **Create output directories**: Make sure output directories exist or the scripts will create them
3. **Install dependencies**: Ensure all required packages are installed

```bash
pip install -r requirements.txt
```

## Example Data Flow

```
XML Files → Parser → RA-D-PS Format → Excel Export
                  ↘ Database → Analysis → Excel Report
```

## Customization

Each example can be customized by:
- Changing input/output paths
- Modifying export formats
- Adding error handling
- Implementing custom analysis logic

## For Production Use

For production deployments, consider:
- Using the command-line interface (`scripts/cli.py`)
- Implementing proper logging
- Adding comprehensive error handling
- Using configuration files for settings