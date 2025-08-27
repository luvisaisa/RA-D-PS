#!/usr/bin/env python3
"""
Test the type handling improvements for the Excel export
"""
import pandas as pd

# Test data with mixed types that could cause comparison errors
test_data = [
    {"FileID": "test1", "Confidence": "MISSING", "Subtlety": 3.5, "Reason": None},
    {"FileID": "test1", "Confidence": None, "Subtlety": "MISSING", "Reason": ""},  
    {"FileID": "test2", "Confidence": "MISSING", "Subtlety": "#N/A", "Reason": "some_reason"},
    {"FileID": "test2", "Confidence": "#N/A", "Subtlety": "#N/A", "Reason": "MISSING"},
]

def test_type_safe_operations():
    """Test the type-safe operations that were causing errors"""
    print("Testing type-safe operations...")
    
    df = pd.DataFrame(test_data)
    print(f"DataFrame created with {len(df)} rows")
    
    # Test row enumeration (this was causing the error)
    for row_idx, (_, row_data) in enumerate(df.iterrows(), start=2):
        print(f"Row {row_idx}: FileID={row_data['FileID']}")
        
        # Test blank row detection with mixed types
        try:
            is_blank_row = all(
                str(value) == "" or value is None or 
                (hasattr(pd, 'isna') and pd.isna(value)) or
                str(value).lower() == 'nan'
                for value in row_data
            )
            print(f"  Blank row check: {is_blank_row}")
        except Exception as e:
            print(f"  Blank row check failed: {e}")
        
        # Test data row counting logic
        try:
            data_row_count = 0
            for prev_idx, (_, prev_row) in enumerate(df.iterrows()):
                if prev_idx >= (row_idx - 2):  # This was the problematic comparison
                    break
                data_row_count += 1
            
            is_even_row = data_row_count % 2 == 0
            print(f"  Data row count: {data_row_count}, Even: {is_even_row}")
        except Exception as e:
            print(f"  Row counting failed: {e}")
    
    # Test MISSING value detection with mixed types
    missing_count = 0
    for row in test_data:
        for key, value in row.items():
            try:
                if value is None:
                    continue
                str_value = str(value)
                if str_value == "MISSING":
                    missing_count += 1
                    print(f"  Found MISSING: {key} = {value}")
            except Exception as e:
                print(f"  Error checking {key}: {e}")
    
    print(f"✅ Type handling test completed! Found {missing_count} MISSING values")

if __name__ == "__main__":
    test_type_safe_operations()
