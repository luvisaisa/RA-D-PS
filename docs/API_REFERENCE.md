# API Documentation - NYT XML Parser

## 📋 Core Module APIs

### XMLPARSE.py - Main Application Module

#### NYTXMLGuiApp Class

##### Constructor
```python
def __init__(self, master: tk.Tk) -> None:
    """
    Initialize the main GUI application.
    
    Args:
        master: Root Tkinter window instance
        
    Attributes:
        files (List[str]): List of selected XML file paths
        excel_path (Optional[str]): Path to selected Excel file for appending
        master (tk.Tk): Reference to root window
    """
```

##### File Selection Methods
```python
def select_files(self) -> None:
    """
    Open file dialog for individual XML file selection.
    Updates self.files with selected file paths.
    """

def select_folder(self) -> None:
    """
    Select single folder and add all XML files to processing list.
    Filters out system files (._*, ~*) and validates XML extensions.
    """

def select_multiple_folders_for_separate_files(self) -> None:
    """
    Advanced multi-folder selection with native system dialogs.
    Creates separate Excel files per folder (legacy mode).
    
    Platform Support:
        - macOS: AppleScript integration for native multi-select
        - Windows/Linux: Fallback to sequential selection
    """
```

##### Core Processing Methods
```python
def _process_multiple_folders(self, folders: List[str]) -> None:
    """
    ⭐ CORE FEATURE: Process multiple folders with combined output.
    
    Args:
        folders: List of folder paths to process
        
    Features:
        - Combined Excel file with separate sheets per folder
        - Single SQLite database for all folders
        - Real-time progress tracking with live logging
        - Template format application
        - Quality validation with user interaction
        
    Workflow:
        1. Initialize combined data structures
        2. Process each folder sequentially  
        3. Collect and validate data
        4. Apply template transformation
        5. Generate combined outputs
        6. Provide comprehensive feedback
    """

def parse_files(self) -> None:
    """
    Parse selected files and append to existing Excel or create new.
    Legacy method for individual file processing.
    """
```

##### Export Methods
```python
def export_new_excel(self) -> None:
    """
    Export parsed data to new Excel file with template formatting.
    
    Features:
        - Template format with Radiologist 1-4 columns
        - Color-coded formatting by radiologist
        - Auto-fitted columns and borders
        - Missing value highlighting
    """

def export_to_sqlite(self) -> None:
    """
    Export parsed data to SQLite database with analytics.
    
    Features:
        - Relational database schema
        - Batch data insertion
        - Quality analysis reporting
        - Excel export from database
        - Comprehensive success feedback
    """
```

##### Template Processing Methods
```python
def _transform_to_template_format(self, all_data: List[Dict]) -> List[Dict]:
    """
    ⭐ CORE FEATURE: Transform data to template format.
    
    Args:
        all_data: List of dictionaries in radiologist-per-row format
        
    Returns:
        List of dictionaries in template format with Radiologist 1-4 columns
        
    Transformation Logic:
        - Groups by FileID and NoduleID
        - Maps radiologists to columns 1-4 cyclically
        - Creates compact rating strings (e.g., "Conf:5 | Sub:3")
        - Preserves all metadata and coordinates
        - Adds reference fields for tracking
    """

def _create_template_excel(self, template_data: List[Dict], excel_path: str) -> None:
    """
    Create Excel file with template formatting.
    
    Args:
        template_data: Data in template format
        excel_path: Output file path
        
    Features:
        - Professional header styling
        - Color-coded radiologist columns
        - Auto-fitted column widths
        - Border formatting
        - Missing value highlighting
    """
```

##### Utility Methods
```python
def _check_for_na_rows(self, all_data: List[Dict], folder_name: str) -> bool:
    """
    Comprehensive data quality validation.
    
    Args:
        all_data: Parsed data to validate
        folder_name: Source identifier for user feedback
        
    Returns:
        bool: True if user wants to continue, False to cancel
        
    Validation Checks:
        - Critical field completeness (Confidence, Subtlety, etc.)
        - Missing value percentage calculation
        - User interaction for quality issues
        - Detailed quality statistics
    """

def show_creator_signature(self) -> None:
    """
    Display animated creator signature popup.
    
    Features:
        - Slide-down animation
        - Auto-positioning relative to main window
        - Timed display with auto-close
        - Professional branding
    """
```

#### Core Parsing Functions

```python
def parse_radiology_sample(file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main XML parsing function with intelligent structure detection.
    
    Args:
        file_path: Path to XML file to parse
        
    Returns:
        Tuple containing:
            - Main DataFrame with radiologist session data
            - Unblinded DataFrame with unblinded session data
            
    Features:
        - Multi-format support (NYT, LIDC, custom)
        - Automatic parse case detection
        - Missing value differentiation (MISSING vs #N/A)
        - Coordinate extraction with edge mapping
        - Session type classification (Standard vs Detailed)
        - Radiologist identification and tracking
    """

def detect_parse_case(file_path: str) -> str:
    """
    Intelligent XML structure detection and classification.
    
    Args:
        file_path: Path to XML file to analyze
        
    Returns:
        Classification string indicating parse strategy
        
    Classification Types:
        - Complete_Attributes: Full radiologist data available
        - With_Reason_Partial: Has reason + partial attributes
        - Core_Attributes_Only: Essential attributes without reason  
        - Minimal_Attributes: Limited attribute set
        - No_Characteristics: Structure without characteristics
        - LIDC_Single_Session: Single LIDC reading session
        - LIDC_Multi_Session_X: Multiple LIDC sessions (2-4)
        - No_Sessions_Found: XML without readable sessions
        - XML_Parse_Error: Malformed or unparseable XML
        - Detection_Error: Structure analysis failure
        
    Detection Algorithm:
        1. Parse XML root and detect namespace
        2. Identify format type (NYT vs LIDC)
        3. Count and analyze reading sessions
        4. Check characteristic attribute availability
        5. Classify based on completeness pattern
    """

def parse_multiple(files: List[str]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """
    Batch processing with memory optimization and progress tracking.
    
    Args:
        files: List of XML file paths to process
        
    Returns:
        Tuple containing:
            - Dict of main DataFrames organized by parse case
            - Dict of unblinded DataFrames organized by parse case
            
    Features:
        - Batch processing for memory efficiency
        - Progress reporting with file-by-file status
        - Error isolation (continue on individual failures)
        - Garbage collection optimization
        - Parse case organization for export
    """
```

### radiology_database.py - Database Module

#### RadiologyDatabase Class

```python
class RadiologyDatabase:
    """
    Specialized SQLite database for radiology data analysis.
    
    Features:
        - Medical data optimized schema
        - Batch operations for performance
        - Quality analysis and reporting
        - Excel export integration
        - Context manager support
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database connection and create schema.
        
        Args:
            db_path: Path to SQLite database file
        """
    
    def insert_batch_data(self, data_list: List[Dict]) -> str:
        """
        Insert batch of radiologist session data.
        
        Args:
            data_list: List of dictionaries containing session data
            
        Returns:
            str: Batch ID for tracking
            
        Features:
            - Bulk insert operations for performance
            - Data validation and type conversion
            - Batch tracking and metadata
            - Error handling with rollback
        """
    
    def get_quality_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive data quality analysis.
        
        Returns:
            Dictionary containing:
                - overall_stats: Basic statistics
                - quality_issues: List of identified issues
                - completeness_analysis: Field-by-field completeness
                - radiologist_stats: Per-radiologist analysis
                
        Analysis Features:
            - Missing value analysis
            - Data consistency checks
            - Radiologist agreement metrics
            - Processing success rates
        """
    
    def export_to_excel(self, excel_path: str) -> str:
        """
        Export database analysis to formatted Excel file.
        
        Args:
            excel_path: Output Excel file path
            
        Returns:
            str: Success message with export details
            
        Excel Features:
            - Multiple analysis sheets
            - Professional formatting
            - Charts and visualizations
            - Quality issue highlighting
            - Summary statistics
        """
```

## 🔧 Utility Functions

### File Operations
```python
def open_file_cross_platform(file_path: str) -> None:
    """
    Open file with default system application across platforms.
    
    Args:
        file_path: Path to file to open
        
    Platform Support:
        - macOS: Uses 'open' command
        - Windows: Uses os.startfile()
        - Linux: Uses 'xdg-open' command
        
    Error Handling:
        - Graceful failure with error logging
        - User notification of open failures
    """
```

### Data Validation
```python
def get_expected_attributes_for_case(parse_case: str) -> Dict[str, List[str]]:
    """
    Get expected attribute structure for specific parse case.
    
    Args:
        parse_case: Classification from detect_parse_case()
        
    Returns:
        Dictionary with expected attributes by category:
            - header: Expected header fields
            - characteristics: Expected characteristic fields
            - roi: Expected ROI/coordinate fields
            - nodule: Expected nodule identification fields
            
    Usage:
        Used for distinguishing MISSING vs #N/A values based on
        whether fields are expected in the detected XML structure.
    """
```

## 📊 Data Structures

### Input Data Format
```python
# Raw XML data is parsed into this structure
XMLSessionData = {
    'FileID': str,              # Source file identifier
    'ParseCase': str,           # Classification from detect_parse_case()
    'Radiologist': str,         # Radiologist identifier
    'SessionType': str,         # 'Standard', 'Detailed', or 'Unblinded'
    'NoduleID': Union[int, str], # Nodule identifier
    'Confidence': Union[float, str], # Confidence rating or MISSING/#N/A
    'Subtlety': Union[float, str],   # Subtlety rating or MISSING/#N/A
    'Obscuration': Union[float, str], # Obscuration rating or MISSING/#N/A
    'Reason': str,              # Diagnostic reason or MISSING/#N/A
    'SOP_UID': str,             # DICOM SOP Instance UID
    'StudyInstanceUID': str,    # DICOM Study Instance UID
    'SeriesInstanceUID': str,   # DICOM Series Instance UID
    'Modality': str,            # Imaging modality (e.g., 'CT', 'MR')
    'DateService': str,         # Service date
    'TimeService': str,         # Service time
    'X_coord': Union[float, str], # X coordinate or MISSING/#N/A
    'Y_coord': Union[float, str], # Y coordinate or MISSING/#N/A
    'Z_coord': Union[float, str], # Z coordinate or MISSING/#N/A
    'CoordCount': int,          # Number of coordinates in ROI
}
```

### Template Data Format
```python
# Data transformed for template export
TemplateData = {
    'FileID': str,                  # Source file identifier
    'NoduleID': Union[int, str],    # Nodule identifier
    'ParseCase': str,               # XML structure classification
    'SessionType': str,             # Session type classification
    'Radiologist 1': str,          # Compact rating string or empty
    'Radiologist 2': str,          # Compact rating string or empty
    'Radiologist 3': str,          # Compact rating string or empty
    'Radiologist 4': str,          # Compact rating string or empty
    'SOP_UID': str,                 # DICOM identifiers
    'StudyInstanceUID': str,
    'SeriesInstanceUID': str,
    'X_coord': Union[float, str],   # Coordinate data
    'Y_coord': Union[float, str],
    'Z_coord': Union[float, str],
    'CoordCount': int,
    'Modality': str,                # Imaging metadata
    'DateService': str,
    'TimeService': str,
    'ActualRadiologist': str,       # Reference: actual radiologist ID
    'RadiologistSlot': int,         # Reference: which slot (1-4) used
    'SourceFolder': str,            # Reference: source folder name
}
```

### Compact Rating String Format
```python
# Format used in Radiologist 1-4 columns
CompactRatingString = "Conf:5 | Sub:3 | Obs:2 | Reason:1"

# Generation logic:
def create_compact_rating(session_data: XMLSessionData) -> str:
    ratings = []
    if session_data['Confidence'] not in ['', '#N/A', 'MISSING']:
        ratings.append(f"Conf:{session_data['Confidence']}")
    if session_data['Subtlety'] not in ['', '#N/A', 'MISSING']:
        ratings.append(f"Sub:{session_data['Subtlety']}")
    # ... similar for Obscuration and Reason
    return " | ".join(ratings) if ratings else ""
```

## 🗄️ Database Schema Reference

### Sessions Table
```sql
CREATE TABLE sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    file_id TEXT NOT NULL,
    nodule_id TEXT,
    radiologist TEXT,
    parse_case TEXT,
    session_type TEXT,
    confidence REAL,
    subtlety REAL,
    obscuration REAL,
    reason TEXT,
    sop_uid TEXT,
    study_instance_uid TEXT,
    series_instance_uid TEXT,
    modality TEXT,
    date_service TEXT,
    time_service TEXT,
    x_coord REAL,
    y_coord REAL,
    z_coord REAL,
    coord_count INTEGER,
    is_unblinded BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_sessions_file_id (file_id),
    INDEX idx_sessions_nodule_id (nodule_id), 
    INDEX idx_sessions_radiologist (radiologist),
    INDEX idx_sessions_batch_id (batch_id)
);
```

### Quality Issues Table
```sql
CREATE TABLE quality_issues (
    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    file_id TEXT,
    issue_type TEXT NOT NULL,
    issue_description TEXT,
    severity TEXT DEFAULT 'warning',
    field_name TEXT,
    expected_value TEXT,
    actual_value TEXT,
    suggestion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_quality_batch_id (batch_id),
    INDEX idx_quality_type (issue_type)
);
```

### Batches Table
```sql
CREATE TABLE batches (
    batch_id TEXT PRIMARY KEY,
    total_files INTEGER,
    successful_files INTEGER,
    failed_files INTEGER,
    total_sessions INTEGER,
    processing_time_seconds REAL,
    memory_usage_mb REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'processing'
);
```

## 🎨 UI Component APIs

### Progress Dialog
```python
class ProgressDialog:
    """
    Advanced progress tracking dialog with live logging.
    
    Features:
        - Real-time progress bar
        - Color-coded activity log
        - File-by-file status updates
        - Statistics display
        - Auto-close options
    """
    
    def log_message(self, message: str, level: str = "INFO") -> None:
        """
        Add timestamped message to live log.
        
        Args:
            message: Log message text
            level: Message level ("INFO", "SUCCESS", "ERROR", "PARSING", "FILE")
            
        Features:
            - Automatic timestamping
            - Color coding by message level
            - Auto-scroll to latest message
            - Message level icons
        """
    
    def update_progress(self, current: int, total: int, current_task: str = "") -> None:
        """
        Update progress bar and task description.
        
        Args:
            current: Current progress value
            total: Total progress value
            current_task: Description of current task
        """
```

### File Selection Dialogs
```python
def create_export_choice_dialog(parent: tk.Widget, folder_name: str) -> Dict[str, str]:
    """
    Create export format selection dialog.
    
    Args:
        parent: Parent widget for dialog
        folder_name: Name of folder being processed
        
    Returns:
        Dictionary with user choice: {'format': 'excel'|'sqlite'|'both'|None}
        
    Features:
        - Clear format descriptions
        - Platform-appropriate styling
        - Cancel option handling
        - Context-specific messaging
    """
```

## 🔄 Event System

### Processing Events
```python
# Event types generated during processing
ProcessingEvents = {
    'file_started': {
        'file_path': str,
        'file_index': int,
        'total_files': int
    },
    'file_completed': {
        'file_path': str,
        'success': bool,
        'records_extracted': int,
        'parse_case': str
    },
    'batch_completed': {
        'batch_id': str,
        'total_records': int,
        'export_paths': List[str]
    },
    'quality_issue_detected': {
        'issue_type': str,
        'severity': str,
        'file_id': str,
        'description': str
    }
}
```

## 📈 Performance APIs

### Memory Management
```python
def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage statistics.
    
    Returns:
        Dictionary containing:
            - current_mb: Current memory usage in MB
            - peak_mb: Peak memory usage in MB
            - available_mb: Available system memory in MB
    """

def optimize_memory_usage() -> None:
    """
    Perform memory optimization operations.
    
    Operations:
        - Explicit garbage collection
        - DataFrame memory optimization
        - Temporary file cleanup
        - Cache clearing
    """
```

### Performance Monitoring
```python
def benchmark_processing(files: List[str]) -> Dict[str, Any]:
    """
    Benchmark processing performance.
    
    Args:
        files: List of files to process for benchmarking
        
    Returns:
        Performance metrics:
            - total_time_seconds: Total processing time
            - files_per_second: Processing rate
            - records_per_second: Record extraction rate
            - memory_efficiency: Memory usage per record
            - bottlenecks: Identified performance bottlenecks
    """
```

## 🔒 Security & Validation APIs

### Data Sanitization
```python
def sanitize_file_path(file_path: str) -> str:
    """
    Sanitize file path for safe processing.
    
    Args:
        file_path: Raw file path from user input
        
    Returns:
        Sanitized file path safe for processing
        
    Security Checks:
        - Path traversal prevention
        - Invalid character removal
        - Length validation
        - Extension validation
    """

def validate_xml_structure(xml_content: str) -> Dict[str, Any]:
    """
    Validate XML structure for security and compatibility.
    
    Args:
        xml_content: Raw XML content
        
    Returns:
        Validation results:
            - is_valid: Boolean validation result
            - security_issues: List of security concerns
            - compatibility_issues: List of compatibility problems
            - recommendations: Suggested fixes
    """
```

## 🚀 Extension Points

### Custom Parse Case Handlers
```python
def register_custom_parse_case(case_name: str, handler: Callable) -> None:
    """
    Register custom parse case handler for new XML formats.
    
    Args:
        case_name: Unique identifier for parse case
        handler: Function that handles parsing for this case type
        
    Handler Signature:
        def custom_handler(xml_root: ET.Element, file_id: str) -> List[Dict]:
            # Return list of extracted session data
    """
```

### Custom Export Formats
```python
def register_export_format(format_name: str, exporter: Callable) -> None:
    """
    Register custom export format handler.
    
    Args:
        format_name: Name of export format
        exporter: Function that handles export for this format
        
    Exporter Signature:
        def custom_exporter(data: List[Dict], output_path: str) -> bool:
            # Export data to custom format
            # Return success boolean
    """
```

---

*This API documentation is automatically maintained and reflects the current codebase structure.*

*Last Updated: August 12, 2025*
*Version: 2.0*
