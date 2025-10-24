"""
Example: Using the New Excel Exporters

Demonstrates how to use the extracted Excel export functionality
without the GUI.
"""

from pathlib import Path
from src.ra_d_ps.exporters import RADPSExcelFormatter, TemplateExcelFormatter


def example_radps_export():
    """Example: Export data in RA-D-PS format"""
    print("📊 RA-D-PS Excel Export Example")
    print("=" * 50)
    
    # Sample data (would come from parser in real usage)
    records = [
        {
            "file_number": "001",
            "study_uid": "1.2.840.113619.2.55.3.12345",
            "nodule_id": "Nodule001",
            "radiologists": {
                "1": {
                    "subtlety": 3,
                    "confidence": 4,
                    "obscuration": 2,
                    "reason": "ground glass opacity",
                    "coordinates": "100.5, 200.3, 50.2"
                },
                "2": {
                    "subtlety": 4,
                    "confidence": 5,
                    "obscuration": 1,
                    "reason": "well-circumscribed",
                    "coordinates": "102.1, 198.7, 51.0"
                }
            }
        },
        {
            "file_number": "002",
            "study_uid": "1.2.840.113619.2.55.3.54321",
            "nodule_id": "Nodule002",
            "radiologists": {
                "1": {
                    "subtlety": 2,
                    "confidence": 3,
                    "obscuration": 3,
                    "reason": "partially obscured by vessel",
                    "coordinates": "150.0, 250.5, 60.3"
                },
                "2": {
                    "subtlety": 3,
                    "confidence": 4,
                    "obscuration": 2,
                    "reason": "",
                    "coordinates": "151.2, 249.8, 59.9"
                },
                "3": {
                    "subtlety": 2,
                    "confidence": 3,
                    "obscuration": 3,
                    "reason": "small nodule",
                    "coordinates": "149.5, 251.0, 60.5"
                }
            }
        }
    ]
    
    # Export to RA-D-PS format
    output_folder = Path.home() / "Desktop"
    exporter = RADPSExcelFormatter()
    
    print(f"\n✅ Exporting {len(records)} records...")
    print(f"📁 Output folder: {output_folder}")
    
    output_path = exporter.export(records, output_folder)
    
    print(f"\n✨ Export complete!")
    print(f"📄 File: {output_path.name}")
    print(f"📊 Records: {len(records)}")
    print(f"👥 Max radiologists: {max(len(r.get('radiologists', {})) for r in records)}")
    print(f"\n💡 Features:")
    print(f"   • Auto-named with timestamp")
    print(f"   • Dynamic radiologist blocks (1-3 in this example)")
    print(f"   • Spacer columns for visual separation")
    print(f"   • Alternating row colors")
    print(f"   • Frozen header row")
    
    return output_path


def example_template_export():
    """Example: Export data in template format"""
    print("\n\n📋 Template Excel Export Example")
    print("=" * 50)
    
    # Sample template data
    template_data = [
        {
            'FileID': 'file001',
            'NoduleID': 'N1',
            'ParseCase': 'Complete_Attributes',
            'SessionType': 'Standard',
            'Radiologist 1': 'Conf:4 | Sub:3 | Obs:2',
            'Radiologist 2': 'Conf:5 | Sub:4',
            'Radiologist 3': '',
            'Radiologist 4': '',
            'SOP_UID': '1.2.840.1.12345',
            'StudyInstanceUID': '1.2.840.113619.2.55',
            'X_coord': '100.5',
            'Y_coord': '200.3',
            'Z_coord': '50.2',
            'CoordCount': '3',
        },
        {
            'FileID': 'file002',
            'NoduleID': 'N2',
            'ParseCase': 'Core_Attributes_Only',
            'SessionType': 'Standard',
            'Radiologist 1': 'Conf:3 | Sub:2',
            'Radiologist 2': 'Conf:4 | Sub:3 | Obs:2',
            'Radiologist 3': 'Conf:3 | Sub:2',
            'Radiologist 4': '',
            'SOP_UID': '1.2.840.1.54321',
            'StudyInstanceUID': '1.2.840.113619.2.56',
            'X_coord': '150.0',
            'Y_coord': '250.5',
            'Z_coord': '60.3',
            'CoordCount': '3',
        }
    ]
    
    # Export to template format
    output_path = Path.home() / "Desktop" / "radiology_template.xlsx"
    exporter = TemplateExcelFormatter()
    
    print(f"\n✅ Exporting {len(template_data)} records...")
    print(f"📁 Output: {output_path}")
    
    result_path = exporter.export(template_data, output_path)
    
    print(f"\n✨ Export complete!")
    print(f"📄 File: {result_path.name}")
    print(f"\n💡 Features:")
    print(f"   • Repeating Radiologist 1-4 columns")
    print(f"   • Color-coded by radiologist")
    print(f"   • Compact rating strings")
    print(f"   • Borders for visual separation")
    
    return result_path


def example_custom_styling():
    """Example: Custom styling configuration"""
    print("\n\n🎨 Custom Styling Example")
    print("=" * 50)
    
    # Create exporter with custom colors
    exporter = RADPSExcelFormatter(config={
        'blue_color': 'FF0066CC',      # Custom dark blue
        'light_blue_color': 'FFCCDDFF' # Custom light blue
    })
    
    records = [
        {
            "file_number": "001",
            "study_uid": "1.2.3.4.5",
            "nodule_id": "N1",
            "radiologists": {
                "1": {"subtlety": 3, "confidence": 4, "obscuration": 2, 
                      "reason": "test", "coordinates": "100, 200, 50"}
            }
        }
    ]
    
    output_folder = Path.home() / "Desktop"
    output_path = exporter.export(records, output_folder)
    
    print(f"✅ Exported with custom styling")
    print(f"📄 File: {output_path.name}")
    print(f"🎨 Custom colors applied!")
    
    return output_path


def example_forced_radiologist_blocks():
    """Example: Force specific number of radiologist blocks"""
    print("\n\n🔢 Forced Radiologist Blocks Example")
    print("=" * 50)
    
    # Data with only 2 radiologists
    records = [
        {
            "file_number": "001",
            "study_uid": "1.2.3.4.5",
            "nodule_id": "N1",
            "radiologists": {
                "1": {"subtlety": 3, "confidence": 4, "obscuration": 2,
                      "reason": "", "coordinates": "100, 200, 50"},
                "2": {"subtlety": 2, "confidence": 5, "obscuration": 1,
                      "reason": "", "coordinates": "105, 205, 52"}
            }
        }
    ]
    
    # Force 4 radiologist columns (creates empty columns for R3, R4)
    exporter = RADPSExcelFormatter()
    output_folder = Path.home() / "Desktop"
    output_path = exporter.export(records, output_folder, force_blocks=4)
    
    print(f"✅ Exported with forced 4 radiologist blocks")
    print(f"📄 File: {output_path.name}")
    print(f"💡 Created columns for R1, R2, R3, R4 (R3 and R4 are empty)")
    
    return output_path


if __name__ == "__main__":
    print("\n" + "="*50)
    print("RA-D-PS Excel Exporter Examples")
    print("="*50)
    
    try:
        # Run examples
        example_radps_export()
        example_template_export()
        example_custom_styling()
        example_forced_radiologist_blocks()
        
        print("\n" + "="*50)
        print("✅ All examples completed successfully!")
        print("📁 Check your Desktop for the exported files")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
