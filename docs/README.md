# RA-D-PS Documentation

## Quick Start
- [README](../README.md) - Main project overview and setup
- [Installation Guide](INSTALLATION.md) - Detailed installation instructions

## User Guides
- [RA-D-PS Export Guide](RA_D_PS_EXPORT_GUIDE.md) - How to export data in RA-D-PS format
- [Excel vs SQLite Guide](EXCEL_vs_SQLITE_GUIDE.md) - Choosing output formats
- [Integration Guide](INTEGRATION_GUIDE.md) - Integrating with other systems

## Developer Documentation
- [Developer Guide](DEVELOPER_GUIDE.md) - Contributing and development setup
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Performance Guide](PERFORMANCE_README.md) - Performance optimization

## Architecture
- [Project Structure](#project-structure)
- [Module Overview](#module-overview)

## Project Structure

```
ra-d-ps/
├── src/ra_d_ps/          # Main package
│   ├── core.py           # XML parsing logic
│   ├── exporters.py      # Excel/file export
│   ├── gui.py            # GUI components
│   ├── database.py       # SQLite operations
│   ├── config.py         # Configuration
│   └── utils.py          # Utilities
├── tests/                # Test suite
├── docs/                 # Documentation
└── cli.py               # Command-line interface
```

## Module Overview

### Core (`ra_d_ps.core`)
- `parse_radiology_sample()` - Parse single XML file
- `parse_multiple()` - Parse multiple XML files
- `detect_parse_case()` - Auto-detect XML format

### Exporters (`ra_d_ps.exporters`)
- `export_excel()` - Export to Excel with formatting
- `convert_parsed_data_to_ra_d_ps_format()` - Convert to RA-D-PS format

### GUI (`ra_d_ps.gui`)
- `NYTXMLGuiApp` - Main GUI application
- Cross-platform file operations

### Database (`ra_d_ps.database`)
- `RadiologyDatabase` - SQLite database interface
- Analytics and querying capabilities
