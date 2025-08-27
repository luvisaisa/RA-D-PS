#!/usr/bin/env python3
"""
Debug script to identify type mismatch issues
"""
import pandas as pd

def test_enumerate_mismatch():
    """Test the enumerate issue with different start values"""
    print("Testing enumerate mismatch...")
    
    # Create sample data
    data = [
        {"col1": "val1", "col2": "val2"},
        {"col1": "val3", "col2": "val4"},
        {"col1": "val5", "col2": "val6"},
    ]
    df = pd.DataFrame(data)
    
    print("Simulating the problematic code...")
    
    # This simulates the problematic enumerate pattern
    for row_idx, (_, row_data) in enumerate(df.iterrows(), start=2):
        print(f"row_idx (starts at 2): {row_idx}, type: {type(row_idx)}")
        
        # Count data rows before this one (problematic logic)
        data_row_count = 0
        for prev_idx, (_, prev_row) in enumerate(df.iterrows()):
            print(f"  prev_idx (starts at 0): {prev_idx}, type: {type(prev_idx)}")
            print(f"  Comparing prev_idx ({prev_idx}) >= (row_idx - 2) ({row_idx - 2})")
            
            # This is where the type mismatch could occur if types were mixed
            if prev_idx >= (row_idx - 2):  # Both are integers, so this is safe
                break
            data_row_count += 1
        
        print(f"  data_row_count: {data_row_count}")
        print()

def test_mixed_type_operations():
    """Test operations with mixed types that could cause issues"""
    print("Testing mixed type operations...")
    
    # Test string-int comparisons
    test_values = ["5", 5, None, "", "MISSING", 3.14, "10.5"]
    
    for val in test_values:
        try:
            str_val = str(val)
            print(f"Value: {val} ({type(val)}) -> str: '{str_val}'")
            
            # Test length comparison (this should be safe)
            length = len(str_val)
            is_long = length > 10
            print(f"  Length: {length}, is_long: {is_long}")
            
        except Exception as e:
            print(f"  ERROR with {val}: {e}")
    
    print()

def test_percentage_calculations():
    """Test percentage calculations with different types"""
    print("Testing percentage calculations...")
    
    test_cases = [
        (10, 100),  # int/int
        (10.0, 100),  # float/int  
        (10, 100.0),  # int/float
        ("10", 100),  # string/int (this could cause issues)
        (10, "100"),  # int/string (this could cause issues)
    ]
    
    for numerator, denominator in test_cases:
        try:
            # Convert to ensure numeric types
            num_val = float(numerator) if numerator != "" and numerator is not None else 0.0
            denom_val = float(denominator) if denominator != "" and denominator is not None else 1.0
            
            percentage = (num_val / denom_val * 100) if denom_val > 0 else 0.0
            is_high = percentage > 85.0
            
            print(f"({numerator}, {denominator}) -> {num_val}/{denom_val} = {percentage:.2f}%, high: {is_high}")
            
        except Exception as e:
            print(f"ERROR with ({numerator}, {denominator}): {e}")

if __name__ == "__main__":
    test_enumerate_mismatch()
    test_mixed_type_operations()
    test_percentage_calculations()
