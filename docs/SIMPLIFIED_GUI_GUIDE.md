# Simplified 2-Button GUI Guide

## Overview
The GUI has been simplified to provide a cleaner, more intuitive interface with just 2 main export options instead of 8 separate buttons.

## New Interface Layout

### 1. Folder Selection Section
**Button:** `📂 Select Folders`
- Click to select multiple folders containing XML files
- A dialog will open allowing you to select folders one by one
- Click "Cancel" when done selecting folders
- Selected folders will appear in the listbox below the button

### 2. Selected Folders Display
Shows all folders you have selected for processing. Each folder name is displayed in a scrollable listbox.

### 3. Export Options (Main Section)

#### Button 1: `1️⃣ SINGLE EXPORT` (Green)
**Purpose:** Combine all selected folders into ONE Excel file with multiple sheets
- Creates a single `.xlsx` file
- Each folder becomes a separate sheet in the Excel file
- All data is consolidated in one place for easy comparison
- Ideal for: Comparative analysis, overview reports, single-file distribution

#### Button 2: `2️⃣ MULTI EXPORT` (Blue)
**Purpose:** Export each folder as an INDIVIDUAL Excel file
- Creates separate `.xlsx` files for each folder
- Each folder gets its own dedicated Excel file
- Keeps folder data isolated
- Ideal for: Separate analysis, individual reports, modular data organization

### 4. Legend/Key Section
Located at the bottom of the GUI, explains the difference between the two export modes:
- **Option 1:** Export to single XLSX file, multiple sheets
- **Option 2:** Export each folder as an individual XLSX file

### 5. Management Buttons
- **Clear Selection:** Remove all selected folders and start over
- **Help:** Opens help dialog with usage instructions

## Workflow

### Standard Workflow
1. Click "📂 Select Folders"
2. Choose folders one by one (click Cancel when done)
3. Review selected folders in the listbox
4. Choose export mode:
   - Click "1️⃣ SINGLE EXPORT" for combined output
   - Click "2️⃣ MULTI EXPORT" for separate outputs
5. Select output location when prompted
6. Wait for processing to complete

### Example Use Cases

#### Use Case 1: Department-Wide Report
**Scenario:** You have 4 folders (radiologist A, B, C, D) and want to compare all findings in one file.

**Steps:**
1. Select all 4 folders
2. Click "1️⃣ SINGLE EXPORT"
3. Choose output location
4. Result: One Excel file with 4 sheets (one per radiologist)

#### Use Case 2: Individual Radiologist Reports
**Scenario:** You have 4 folders and need separate reports for each radiologist.

**Steps:**
1. Select all 4 folders
2. Click "2️⃣ MULTI EXPORT"
3. Choose output directory
4. Result: 4 separate Excel files (one per radiologist)

## Technical Notes

### Processing Methods
- **Single Export** calls: `_process_multiple_folders_one_excel(folders)`
- **Multi Export** calls: `_process_multiple_folders(folders)`

### Data Storage
- Selected folders are stored in: `self.selected_folder_paths`
- Also maintained in: `self.files` for backward compatibility
- Display updated in: `self.listbox`

### Validation
Both export buttons validate that folders are selected before processing:
- If no folders selected → Warning dialog: "Please select folders first"
- Prevents accidental empty exports

## Comparison: Old vs New GUI

### Old GUI (8 Buttons)
```
❌ Complex layout with 4 sections
❌ 8 different buttons (confusing options)
❌ Separate file vs folder selection
❌ Multiple paths to achieve same goal
```

### New GUI (2 Buttons)
```
✅ Clean layout with clear sections
✅ 2 intuitive export options
✅ Single folder selection method
✅ Clear visual hierarchy with color coding
✅ Explanatory legend at bottom
```

## Color Coding
- **Green (Single Export):** Consolidation, unity, single output
- **Blue (Multi Export):** Separation, individual outputs
- **Light Blue Background:** Consistent branding
- **White Listbox:** Clean display area

## Testing
Run tests to verify functionality:
```bash
python3 tests/test_simplified_gui.py
python3 -m pytest tests/test_gui_workflow.py -v
```

## Future Enhancements
Potential improvements (not yet implemented):
- Drag-and-drop folder selection
- Preview of folder contents before export
- Progress indicator during folder selection
- Batch folder selection (select parent directory)
- Recent folders quick-select
- Export presets (save common configurations)

## Troubleshooting

### "No Folders" Warning
**Problem:** Export button shows warning about no folders selected  
**Solution:** Click "📂 Select Folders" first and select at least one folder

### Empty Listbox After Selection
**Problem:** Selected folders don't appear in listbox  
**Solution:** Make sure you're clicking folders (not files) and that dialog completes successfully

### Processing Takes Too Long
**Problem:** Export seems stuck or slow  
**Solution:** Large folders with many XML files take time. Watch progress dialog for status updates.

### Can't Select More Folders
**Problem:** Need to add more folders after initial selection  
**Solution:** Click "Clear Selection" then "📂 Select Folders" to start fresh

## Support
For issues, bugs, or feature requests:
- Check test results: `python3 tests/test_simplified_gui.py`
- Review logs in terminal output
- See `docs/GUI_STATE_REPORT.md` for detailed GUI analysis
- Check `docs/DEVELOPER_GUIDE.md` for technical details
