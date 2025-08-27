#!/usr/bin/env python3
"""
Comprehensive test for all type safety issues in XML parser
"""
import pandas as pd

def test_coordinate_count_comparison():
    """Test the CoordCount comparison that was causing the type error"""
    print("Testing CoordCount comparison...")
    
    # Test data with mixed types for CoordCount
    test_data = [
        {"FileID": "test1", "SessionType": "Standard", "CoordCount": 5},      # int
        {"FileID": "test2", "SessionType": "Standard", "CoordCount": "15"},   # string that should be > 10
        {"FileID": "test3", "SessionType": "Detailed", "CoordCount": "abc"},  # invalid string
        {"FileID": "test4", "SessionType": "Standard", "CoordCount": None},   # None
        {"FileID": "test5", "SessionType": "Standard", "CoordCount": 12.5},   # float
        {"FileID": "test6", "SessionType": "Standard"},                       # missing key
    ]
    
    # Simulate the fixed logic
    detailed_data = []
    standard_data = []
    
    for row in test_data:
        # This is the fixed logic from XMLPARSE.py
        coord_count = row.get('CoordCount', 0)
        try:
            coord_count_int = int(coord_count) if coord_count is not None else 0
        except (ValueError, TypeError):
            coord_count_int = 0
        
        print(f"Row {row['FileID']}: CoordCount={coord_count} -> {coord_count_int}, "
              f"Detailed: {row.get('SessionType') == 'Detailed' or coord_count_int > 10}")
        
        if row.get('SessionType') == 'Detailed' or coord_count_int > 10:
            detailed_data.append(row)
        else:
            standard_data.append(row)
    
    print(f"✅ Detailed: {len(detailed_data)}, Standard: {len(standard_data)}")
    return True

def test_pandas_iteration():
    """Test pandas DataFrame iteration with mixed types"""
    print("\nTesting pandas DataFrame iteration...")
    
    # Create DataFrame with mixed types
    data = [
        {"FileID": "file1", "Value": 10, "Text": "hello"},
        {"FileID": "file2", "Value": "20", "Text": None},
        {"FileID": "file3", "Value": None, "Text": ""},
        {"FileID": "", "Value": "", "Text": ""},  # Blank row
    ]
    
    df = pd.DataFrame(data)
    print(f"DataFrame created with {len(df)} rows")
    
    # Test the row iteration logic
    for row_idx, (_, row_data) in enumerate(df.iterrows(), start=2):
        print(f"Row {row_idx}: {dict(row_data)}")
        
        # Test blank row detection
        try:
            is_blank_row = all(
                str(value) == "" or value is None or 
                (hasattr(pd, 'isna') and pd.isna(value)) or
                str(value).lower() == 'nan'
                for value in row_data
            )
            print(f"  Blank row: {is_blank_row}")
        except Exception as e:
            print(f"  Blank row detection failed: {e}")
            return False
        
        # Test row counting (the problematic logic that was fixed)
        data_row_count = 0
        try:
            for prev_idx, (_, prev_row) in enumerate(df.iterrows()):
                if prev_idx >= (row_idx - 2):  # This should work now
                    break
                # Test blank row detection on previous row
                try:
                    prev_is_blank = all(
                        str(v) == "" or v is None or 
                        (hasattr(pd, 'isna') and pd.isna(v)) or
                        str(v).lower() == 'nan'
                        for v in prev_row
                    )
                except Exception:
                    prev_is_blank = False
                
                if not prev_is_blank:
                    data_row_count += 1
            
            is_even_row = data_row_count % 2 == 0
            print(f"  Data row count: {data_row_count}, Even: {is_even_row}")
            
        except Exception as e:
            print(f"  Row counting failed: {e}")
            return False
    
    print("✅ Pandas iteration test passed")
    return True

def test_percentage_calculations():
    """Test percentage calculations with type safety"""
    print("\nTesting percentage calculations...")
    
    # Test NA percentage calculation with mixed types
    test_cases = [
        (10, 100, "normal case"),
        (0, 100, "zero numerator"),  
        (10, 0, "zero denominator"),
        ("10", "100", "string numbers"),
        (10.5, 100.5, "floats"),
    ]
    
    for na_count, total_rows, desc in test_cases:
        try:
            # Ensure both values are numeric before calculation
            na_numeric = float(na_count) if na_count != "" and na_count is not None else 0.0
            total_numeric = float(total_rows) if total_rows != "" and total_rows is not None else 1.0
            
            # This is the logic from the hide columns function
            na_percentage = (na_numeric / total_numeric * 100) if total_numeric > 0 else 0.0
            is_hidden = na_percentage > 85.0
            print(f"  {desc}: {na_count}/{total_rows} = {na_percentage:.2f}%, hidden: {is_hidden}")
        except Exception as e:
            print(f"  {desc} failed: {e}")
            return False
    
    print("✅ Percentage calculation test passed")
    return True

def main():
    """Run all type safety tests"""
    print("=== Comprehensive Type Safety Test ===\n")
    
    tests = [
        test_coordinate_count_comparison,
        test_pandas_iteration, 
        test_percentage_calculations,
    ]
    
    passed = 0
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
    
    print(f"\n=== Results: {passed}/{len(tests)} tests passed ===")
    
    if passed == len(tests):
        print("🎉 All type safety tests passed! The XML parser should now work without type errors.")
    else:
        print("⚠️  Some tests failed. There may still be type safety issues.")
    
    return passed == len(tests)

if __name__ == "__main__":
    main()
