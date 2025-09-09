# RA-D-PS Excel Export Feature

## Overview
The RA-D-PS (Radiologist-Aggregated Dynamic-Presentation Sheets) export feature provides a new Excel output format that organizes radiologist data in dynamic blocks with automatic naming and versioning.

## Key Features

### 1. Dynamic Radiologist Blocks
- Automatically detects the maximum number of radiologists across all records
- Creates column blocks for each radiologist: Subtlety, Confidence, Obscuration, Reason, Coordinates
- Adds spacer columns between blocks for visual clarity

### 2. Auto-Naming & Versioning
- Derives filename from source folder name + timestamp
- Format: `{folder_name}_RA-D-PS_{YYYY-MM-DD_HHMMSS}.xlsx`
- Automatic versioning (_v2, _v3, etc.) prevents overwrites

### 3. Enhanced Formatting
- Alternating row striping (blue/white) using conditional formatting
- Spacer columns remain unformatted
- Freeze panes at A2 for easy navigation
- Auto-sized columns with wider Reason columns (24 chars)

## Column Layout

```
file # | Study UID | [spacer] | NoduleID | [spacer] | Radiologist_1_Subtlety | Radiologist_1_Confidence | Radiologist_1_Obscuration | Radiologist_1_Reason | Coordinates | [spacer] | Radiologist_2_... | ...
```

## Usage

### GUI Interface
1. Select XML files using "Select XML Files" or "Select Folders"
2. Click the new "Export RA-D-PS" button
3. Choose output folder
4. File automatically saved with timestamp

### Programmatic Usage

```python
from XMLPARSE import parse_radiology_sample, convert_parsed_data_to_ra_d_ps_format, export_excel

# Parse XML file(s)
main_df, unblinded_df = parse_radiology_sample("path/to/file.xml")

# Convert to RA-D-PS format
records = convert_parsed_data_to_ra_d_ps_format((main_df, unblinded_df))

# Export to Excel
output_path = export_excel(records, "output/folder", sheet="data")
```

## Data Format

### Input Records
Each record should contain:
- `file_number`: File identifier (str/int)
- `study_uid`: Study instance UID (str)
- `nodule_id`: Nodule identifier (str)
- `radiologists`: Dict mapping radiologist numbers to data
  - Each radiologist dict contains: `subtlety`, `confidence`, `obscuration`, `reason`, `coordinates`

### Example Record
```python
{
    "file_number": "F-001",
    "study_uid": "1.2.3.4.5.6.7.8.1",
    "nodule_id": "N-1",
    "radiologists": {
        "1": {
            "subtlety": 3,
            "confidence": 4,
            "obscuration": 2,
            "reason": "partial overlap",
            "coordinates": "120, 85, 32"
        },
        "2": {
            "subtlety": 2,
            "confidence": 3,
            "obscuration": 3,
            "reason": "low contrast", 
            "coordinates": "118, 80, 30"
        }
    }
}
```

## Technical Implementation

### Core Functions
- `export_excel(records, folder_path, sheet="data")`: Main export function
- `convert_parsed_data_to_ra_d_ps_format(dataframes)`: Converts parsed XML data
- `_get_R_max(records)`: Determines maximum radiologist count
- `_build_columns(R_max)`: Creates column layout with spacers
- `_apply_row_striping(ws, indices)`: Applies conditional formatting

### File Naming Logic
1. Extract folder name from path
2. Sanitize name (A-Z, a-z, 0-9, _, - only)
3. Add timestamp in YYYY-MM-DD_HHMMSS format
4. Check for existing files and append version suffix if needed

### Conditional Formatting
- Uses Excel's MOD(ROW(),2) formula for alternating rows
- Even rows: Light blue (#CCE5FF)
- Odd rows: White (#FFFFFF)
- Applied only to non-spacer columns

## Benefits

1. **Dynamic Layout**: Adapts to any number of radiologists
2. **Visual Clarity**: Spacer columns and striping improve readability
3. **Automatic Organization**: No manual column management
4. **Version Control**: Prevents accidental overwrites
5. **Professional Format**: Clean, consistent presentation
6. **Integration**: Seamlessly works with existing XML parsing

## Testing

Run the test scripts to verify functionality:
```bash
python test_ra_d_ps_export.py          # Basic export test
python test_ra_d_ps_integration.py     # Full integration test
python test_gui_integration.py         # GUI integration test
```

## Comparison with Standard Export

| Feature | Standard Export | RA-D-PS Export |
|---------|----------------|----------------|
| Layout | Fixed columns | Dynamic radiologist blocks |
| Naming | Manual selection | Auto-generated with timestamp |
| Versioning | Manual handling | Automatic |
| Formatting | Static fills | Conditional formatting |
| Spacers | None | Visual separation columns |
| Scalability | Fixed structure | Adapts to data |
