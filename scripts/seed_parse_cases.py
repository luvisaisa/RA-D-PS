#!/usr/bin/env python3
"""
Parse Case Seeding Script for RA-D-PS
Populates PostgreSQL database with all known parse case definitions
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.database import ParseCaseRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Parse case definitions based on structure_detector.py
PARSE_CASE_DEFINITIONS = [
    {
        "name": "Complete_Attributes",
        "description": "Full LIDC-IDRI structure with all characteristics and complete header",
        "version": "1.0.0",
        "format_type": "LIDC",
        "detection_priority": 100,
        "detection_criteria": {
            "min_chars": 3,
            "requires_reason": True,
            "requires_header": True,
            "requires_modality": True,
            "expected_fields": ["confidence", "subtlety", "obscuration", "reason"]
        },
        "field_mappings": {
            "confidence": {
                "xml_path": "readingSession/nodule/characteristics/confidence",
                "canonical_field": "nodule.confidence",
                "data_type": "integer",
                "required": True
            },
            "subtlety": {
                "xml_path": "readingSession/nodule/characteristics/subtlety",
                "canonical_field": "nodule.subtlety",
                "data_type": "integer",
                "required": True
            },
            "obscuration": {
                "xml_path": "readingSession/nodule/characteristics/obscuration",
                "canonical_field": "nodule.obscuration",
                "data_type": "integer",
                "required": True
            },
            "reason": {
                "xml_path": "readingSession/nodule/characteristics/reason",
                "canonical_field": "nodule.reason",
                "data_type": "string",
                "required": True
            }
        },
        "characteristic_fields": ["confidence", "subtlety", "obscuration", "reason"],
        "requires_header": True,
        "requires_modality": True,
        "is_legacy_format": True
    },
    {
        "name": "With_Reason_Partial",
        "description": "Partial structure but includes reason field",
        "version": "1.0.0",
        "format_type": "LIDC",
        "detection_priority": 90,
        "detection_criteria": {
            "min_chars": 2,
            "requires_reason": True,
            "requires_header": False,
            "requires_modality": False,
            "expected_fields": ["subtlety", "reason"]
        },
        "field_mappings": {
            "subtlety": {
                "xml_path": "readingSession/nodule/characteristics/subtlety",
                "canonical_field": "nodule.subtlety",
                "data_type": "integer",
                "required": True
            },
            "reason": {
                "xml_path": "readingSession/nodule/characteristics/reason",
                "canonical_field": "nodule.reason",
                "data_type": "string",
                "required": True
            }
        },
        "characteristic_fields": ["subtlety", "reason"],
        "requires_header": False,
        "requires_modality": False,
        "is_legacy_format": True
    },
    {
        "name": "Core_Attributes_Only",
        "description": "Core characteristics without reason field",
        "version": "1.0.0",
        "format_type": "LIDC",
        "detection_priority": 80,
        "detection_criteria": {
            "min_chars": 2,
            "requires_reason": False,
            "requires_header": False,
            "requires_modality": False,
            "required_chars": ["confidence", "subtlety"],
            "expected_fields": ["confidence", "subtlety", "obscuration"]
        },
        "field_mappings": {
            "confidence": {
                "xml_path": "readingSession/nodule/characteristics/confidence",
                "canonical_field": "nodule.confidence",
                "data_type": "integer",
                "required": True
            },
            "subtlety": {
                "xml_path": "readingSession/nodule/characteristics/subtlety",
                "canonical_field": "nodule.subtlety",
                "data_type": "integer",
                "required": True
            },
            "obscuration": {
                "xml_path": "readingSession/nodule/characteristics/obscuration",
                "canonical_field": "nodule.obscuration",
                "data_type": "integer",
                "required": False
            }
        },
        "characteristic_fields": ["confidence", "subtlety", "obscuration"],
        "requires_header": False,
        "requires_modality": False,
        "is_legacy_format": True
    },
    {
        "name": "LIDC_v2_Standard",
        "description": "Modern LIDC-IDRI format with extended characteristics (v2): malignancy, calcification, sphericity, margin, lobulation, spiculation, texture",
        "version": "1.0.0",
        "format_type": "LIDC_v2",
        "detection_priority": 95,
        "detection_criteria": {
            "min_chars": 5,
            "requires_reason": False,
            "requires_header": True,
            "requires_modality": False,
            "v2_fields": ["subtlety", "malignancy", "internalStructure", "calcification", "sphericity", "margin", "lobulation", "spiculation", "texture"],
            "min_v2_count": 5,
            "expected_fields": ["malignancy", "internalStructure", "calcification"]
        },
        "field_mappings": {
            "subtlety": {
                "xml_path": "readingSession/nodule/characteristics/subtlety",
                "canonical_field": "nodule.subtlety",
                "data_type": "integer",
                "required": True
            },
            "malignancy": {
                "xml_path": "readingSession/nodule/characteristics/malignancy",
                "canonical_field": "nodule.malignancy",
                "data_type": "integer",
                "required": True
            },
            "internalStructure": {
                "xml_path": "readingSession/nodule/characteristics/internalStructure",
                "canonical_field": "nodule.internal_structure",
                "data_type": "integer",
                "required": False
            },
            "calcification": {
                "xml_path": "readingSession/nodule/characteristics/calcification",
                "canonical_field": "nodule.calcification",
                "data_type": "integer",
                "required": False
            },
            "sphericity": {
                "xml_path": "readingSession/nodule/characteristics/sphericity",
                "canonical_field": "nodule.sphericity",
                "data_type": "integer",
                "required": False
            },
            "margin": {
                "xml_path": "readingSession/nodule/characteristics/margin",
                "canonical_field": "nodule.margin",
                "data_type": "integer",
                "required": False
            },
            "lobulation": {
                "xml_path": "readingSession/nodule/characteristics/lobulation",
                "canonical_field": "nodule.lobulation",
                "data_type": "integer",
                "required": False
            },
            "spiculation": {
                "xml_path": "readingSession/nodule/characteristics/spiculation",
                "canonical_field": "nodule.spiculation",
                "data_type": "integer",
                "required": False
            },
            "texture": {
                "xml_path": "readingSession/nodule/characteristics/texture",
                "canonical_field": "nodule.texture",
                "data_type": "integer",
                "required": False
            }
        },
        "characteristic_fields": ["subtlety", "malignancy", "internalStructure", "calcification", "sphericity", "margin", "lobulation", "spiculation", "texture"],
        "requires_header": True,
        "requires_modality": False,
        "is_legacy_format": False
    },
    {
        "name": "Minimal_Attributes",
        "description": "Single characteristic only",
        "version": "1.0.0",
        "format_type": "LIDC",
        "detection_priority": 70,
        "detection_criteria": {
            "min_chars": 1,
            "max_chars": 1,
            "requires_reason": False,
            "requires_header": False,
            "requires_modality": False
        },
        "field_mappings": {
            "subtlety": {
                "xml_path": "readingSession/nodule/characteristics/subtlety",
                "canonical_field": "nodule.subtlety",
                "data_type": "integer",
                "required": False
            }
        },
        "characteristic_fields": ["subtlety"],
        "requires_header": False,
        "requires_modality": False,
        "is_legacy_format": True
    },
    {
        "name": "No_Characteristics",
        "description": "No characteristics section found",
        "version": "1.0.0",
        "format_type": "LIDC",
        "detection_priority": 60,
        "detection_criteria": {
            "min_chars": 0,
            "max_chars": 0,
            "requires_reason": False,
            "requires_header": False,
            "requires_modality": False
        },
        "field_mappings": {},
        "characteristic_fields": [],
        "requires_header": False,
        "requires_modality": False,
        "is_legacy_format": True
    },
    {
        "name": "LIDC_Single_Session",
        "description": "Single session LIDC format",
        "version": "1.0.0",
        "format_type": "LIDC",
        "detection_priority": 50,
        "detection_criteria": {
            "session_count": 1,
            "common_chars": ["subtlety"],
            "requires_header": False
        },
        "field_mappings": {
            "subtlety": {
                "xml_path": "readingSession/nodule/characteristics/subtlety",
                "canonical_field": "nodule.subtlety",
                "data_type": "integer",
                "required": True
            }
        },
        "characteristic_fields": ["subtlety"],
        "requires_header": False,
        "requires_modality": False,
        "min_session_count": 1,
        "max_session_count": 1,
        "is_legacy_format": True
    },
    {
        "name": "LIDC_Multi_Session_2",
        "description": "Two-session LIDC format",
        "version": "1.0.0",
        "format_type": "LIDC",
        "detection_priority": 49,
        "detection_criteria": {
            "session_count": 2,
            "common_chars": ["subtlety"],
            "requires_header": False
        },
        "field_mappings": {
            "subtlety": {
                "xml_path": "readingSession/nodule/characteristics/subtlety",
                "canonical_field": "nodule.subtlety",
                "data_type": "integer",
                "required": True
            }
        },
        "characteristic_fields": ["subtlety"],
        "requires_header": False,
        "requires_modality": False,
        "min_session_count": 2,
        "max_session_count": 2,
        "is_legacy_format": True
    },
    {
        "name": "LIDC_Multi_Session_3",
        "description": "Three-session LIDC format",
        "version": "1.0.0",
        "format_type": "LIDC",
        "detection_priority": 48,
        "detection_criteria": {
            "session_count": 3,
            "common_chars": ["subtlety"],
            "requires_header": False
        },
        "field_mappings": {
            "subtlety": {
                "xml_path": "readingSession/nodule/characteristics/subtlety",
                "canonical_field": "nodule.subtlety",
                "data_type": "integer",
                "required": True
            }
        },
        "characteristic_fields": ["subtlety"],
        "requires_header": False,
        "requires_modality": False,
        "min_session_count": 3,
        "max_session_count": 3,
        "is_legacy_format": True
    },
    {
        "name": "LIDC_Multi_Session_4",
        "description": "Four-session LIDC format",
        "version": "1.0.0",
        "format_type": "LIDC",
        "detection_priority": 47,
        "detection_criteria": {
            "session_count": 4,
            "common_chars": ["subtlety"],
            "requires_header": False
        },
        "field_mappings": {
            "subtlety": {
                "xml_path": "readingSession/nodule/characteristics/subtlety",
                "canonical_field": "nodule.subtlety",
                "data_type": "integer",
                "required": True
            }
        },
        "characteristic_fields": ["subtlety"],
        "requires_header": False,
        "requires_modality": False,
        "min_session_count": 4,
        "max_session_count": 4,
        "is_legacy_format": True
    }
]


def seed_parse_cases(repo: ParseCaseRepository, overwrite: bool = False):
    """
    Seed database with parse case definitions
    
    Args:
        repo: ParseCaseRepository instance
        overwrite: If True, update existing parse cases; if False, skip existing
    """
    print("\n" + "=" * 70)
    print("Parse Case Seeding")
    print("=" * 70)
    
    seeded_count = 0
    updated_count = 0
    skipped_count = 0
    
    for case_def in PARSE_CASE_DEFINITIONS:
        case_name = case_def["name"]
        
        # Check if parse case already exists
        existing = repo.get_parse_case_by_name(case_name)
        
        if existing:
            if overwrite:
                logger.info(f"Updating existing parse case: {case_name}")
                print(f"   🔄 Updating: {case_name}")
                
                repo.update_parse_case(
                    name=case_name,
                    description=case_def.get("description"),
                    version=case_def.get("version"),
                    detection_criteria=case_def.get("detection_criteria"),
                    field_mappings=case_def.get("field_mappings"),
                    characteristic_fields=case_def.get("characteristic_fields"),
                    requires_header=case_def.get("requires_header"),
                    requires_modality=case_def.get("requires_modality"),
                    min_session_count=case_def.get("min_session_count"),
                    max_session_count=case_def.get("max_session_count"),
                    detection_priority=case_def.get("detection_priority"),
                    format_type=case_def.get("format_type"),
                    is_legacy_format=case_def.get("is_legacy_format", True),
                    notes=f"Updated on {datetime.now().isoformat()}"
                )
                updated_count += 1
            else:
                logger.info(f"Parse case already exists, skipping: {case_name}")
                print(f"   ⏭️  Skipping: {case_name} (already exists)")
                skipped_count += 1
        else:
            logger.info(f"Creating new parse case: {case_name}")
            print(f"   ✅ Creating: {case_name} (priority: {case_def['detection_priority']})")
            
            repo.create_parse_case(
                name=case_name,
                description=case_def.get("description"),
                version=case_def.get("version", "1.0.0"),
                detection_criteria=case_def.get("detection_criteria", {}),
                field_mappings=case_def.get("field_mappings", {}),
                characteristic_fields=case_def.get("characteristic_fields", []),
                requires_header=case_def.get("requires_header", False),
                requires_modality=case_def.get("requires_modality", False),
                min_session_count=case_def.get("min_session_count"),
                max_session_count=case_def.get("max_session_count"),
                detection_priority=case_def.get("detection_priority", 50),
                is_legacy_format=case_def.get("is_legacy_format", True),
                format_type=case_def.get("format_type", "LIDC"),
                created_by="seed_script",
                notes=f"Seeded on {datetime.now().isoformat()}"
            )
            seeded_count += 1
    
    return seeded_count, updated_count, skipped_count


def verify_seeding(repo: ParseCaseRepository):
    """
    Verify that all parse cases were seeded correctly
    """
    print("\n" + "=" * 70)
    print("Verification")
    print("=" * 70)
    
    # Fetch fresh data from database
    with repo.get_session() as session:
        from src.ra_d_ps.database.models import ParseCase
        from sqlalchemy import select
        
        # Query all parse cases
        stmt = select(ParseCase).where(ParseCase.is_active == True).order_by(ParseCase.detection_priority.desc())
        result = session.execute(stmt)
        all_cases = result.scalars().all()
        
        print(f"\n📊 Total active parse cases in database: {len(all_cases)}")
        print("\n   Parse Cases (sorted by priority):")
        print("   " + "-" * 66)
        
        for case in all_cases:
            active_marker = "✅" if case.is_active else "❌"
            v2_marker = " [v2]" if case.format_type == "LIDC_v2" else ""
            print(f"   {active_marker} {case.name:30s} | Priority: {case.detection_priority:3d} | {case.format_type}{v2_marker}")
        
        # Check for LIDC_v2_Standard specifically
        v2_stmt = select(ParseCase).where(ParseCase.name == "LIDC_v2_Standard")
        v2_result = session.execute(v2_stmt)
        v2_case = v2_result.scalar_one_or_none()
        
        if v2_case:
            print("\n   ✅ LIDC_v2_Standard found with:")
            print(f"      - Priority: {v2_case.detection_priority}")
            print(f"      - Format: {v2_case.format_type}")
            print(f"      - Characteristic fields: {len(v2_case.characteristic_fields or [])}")
            v2_fields = v2_case.detection_criteria.get("v2_fields", [])
            print(f"      - V2 fields in detection criteria: {len(v2_fields)}")
            if v2_fields:
                print(f"        {', '.join(v2_fields[:3])}...")
        else:
            print("\n   ❌ LIDC_v2_Standard NOT found!")
        
        # Summary by format type
        format_counts = {}
        for case in all_cases:
            fmt = case.format_type or "Unknown"
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        print("\n   Parse Cases by Format Type:")
        for fmt, count in sorted(format_counts.items()):
            print(f"      {fmt}: {count}")


def main():
    """
    Main seeding script
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed parse cases into PostgreSQL database")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing parse cases (default: skip existing)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing parse cases, don't seed"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("RA-D-PS Parse Case Seeding Script")
    print("=" * 70)
    print(f"\nMode: {'Verify Only' if args.verify_only else 'Seed'}")
    print(f"Overwrite: {'Yes' if args.overwrite else 'No'}")
    
    try:
        # Initialize repository
        print("\n🔌 Connecting to database...")
        repo = ParseCaseRepository()
        
        if not args.verify_only:
            # Seed parse cases
            print(f"\n📦 Seeding {len(PARSE_CASE_DEFINITIONS)} parse cases...")
            seeded, updated, skipped = seed_parse_cases(repo, overwrite=args.overwrite)
            
            print("\n" + "=" * 70)
            print("Seeding Summary")
            print("=" * 70)
            print(f"   ✅ Created: {seeded}")
            print(f"   🔄 Updated: {updated}")
            print(f"   ⏭️  Skipped: {skipped}")
            print(f"   📊 Total: {seeded + updated + skipped}")
        
        # Verify seeding
        verify_seeding(repo)
        
        print("\n" + "=" * 70)
        print("✅ Parse case seeding complete!")
        print("=" * 70)
        
        # Next steps
        print("\n💡 Next Steps:")
        print("   1. Test detection: python scripts/test_detection.py")
        print("   2. Refactor structure_detector.py to use database")
        print("   3. Test with XML-COMP dataset")
        
        repo.close()
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
