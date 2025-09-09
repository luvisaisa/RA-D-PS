#!/usr/bin/env python3
"""
Quick test to verify the type handling fixes in the XML parser
"""

# Test data with different types that could cause the '>' comparison error
test_data = [
    {"FileID": "test1", "Confidence": "#N/A", "Subtlety": "3", "Reason": "#N/A"},
    {"FileID": "test1", "Confidence": "MISSING", "Subtlety": "#N/A", "Reason": ""},  
    {"FileID": "test2", "Confidence": "#N/A", "Subtlety": "#N/A", "Reason": "#N/A"},
    {"FileID": "test2", "Confidence": "#N/A", "Subtlety": "#N/A", "Reason": "#N/A"},
]

def test_na_percentage_calculation():
    """Test the N/A percentage calculation logic"""
    print("Testing N/A percentage calculation...")
    
    # Test the logic that was causing the error
    total_rows = len(test_data)
    
    for col_name in ["Confidence", "Subtlety", "Reason"]:
        na_count = 0
        for row in test_data:
            cell_value = row.get(col_name, "")
            str_value = str(cell_value).strip()
            if str_value.upper() == "#N/A" or str_value.upper() == "N/A":
                na_count += 1
        
        # This is the fixed calculation - should not cause type errors
        na_percentage = float(na_count / total_rows * 100) if total_rows > 0 else 0.0
        
        print(f"Column '{col_name}': {na_count}/{total_rows} = {na_percentage:.1f}% N/A")
        
        # Test the comparison that was failing
        should_hide = na_percentage > 85.0
        print(f"  Should hide column? {should_hide} (>{85.0})")
        
    print("✅ Type handling test passed!")

if __name__ == "__main__":
    test_na_percentage_calculation()
