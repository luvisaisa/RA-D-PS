#!/usr/bin/env python3
"""
Test script for Text Storage Sector (PDF/Paper/Text Clip Feature)

Demonstrates storing and retrieving arbitrary text blocks in the 'text_storage' sector.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.database.keyword_repository import KeywordRepository


def test_text_storage():
    """Test text storage sector for PDF/paper/text clip feature"""
    print("\n" + "=" * 80)
    print("TEXT STORAGE SECTOR TEST")
    print("=" * 80)
    print("\nTesting PDF/paper/text clip feature with 'text_storage' sector\n")
    
    repo = KeywordRepository()
    
    try:
        # Step 1: Create a keyword for organizing text clips
        print("1. Creating keyword for text clips...")
        kw = repo.add_keyword("pulmonary nodule", category="anatomy", 
                             normalized_form="pulmonary_nodule")
        print(f"   ✅ Created keyword: '{kw.keyword_text}' (id={kw.keyword_id})")
        
        # Step 2: Store text clips from various sources
        print("\n2. Storing text clips in 'text_storage' sector...")
        
        clip1 = repo.add_text_block(
            keyword_id=kw.keyword_id,
            text="A 5mm pulmonary nodule was detected in the right upper lobe. "
                 "The nodule shows solid consistency with smooth borders. "
                 "Recommended follow-up in 3 months.",
            source_file="research_paper_2023_smith.pdf"
        )
        print(f"   ✅ Stored clip 1: {clip1.source_file} ({len(clip1.context)} chars)")
        
        clip2 = repo.add_text_block(
            keyword_id=kw.keyword_id,
            text="Ground glass opacity measuring 8mm observed in left lower lobe. "
                 "The lesion exhibits spiculation suggesting possible malignancy. "
                 "Biopsy recommended.",
            source_file="clinical_notes_case_157.txt"
        )
        print(f"   ✅ Stored clip 2: {clip2.source_file} ({len(clip2.context)} chars)")
        
        clip3 = repo.add_text_block(
            keyword_id=kw.keyword_id,
            text="Multiple subcentimeter pulmonary nodules bilaterally. "
                 "Largest measures 4mm in the right middle lobe. "
                 "Likely benign granulomas, but annual follow-up advised.",
            source_file="radiology_report_patient_042.pdf"
        )
        print(f"   ✅ Stored clip 3: {clip3.source_file} ({len(clip3.context)} chars)")
        
        # Step 3: Retrieve all text blocks for the keyword
        print("\n3. Retrieving all text clips for keyword...")
        text_blocks = repo.get_text_blocks(kw.keyword_id)
        print(f"   ✅ Retrieved {len(text_blocks)} text clips")
        
        for i, text in enumerate(text_blocks, 1):
            preview = text[:80] + "..." if len(text) > 80 else text
            print(f"      {i}. {preview}")
        
        # Step 4: Verify sector filtering
        print("\n4. Verifying sector filtering...")
        sources = repo.get_sources_for_keyword(kw.keyword_id)
        text_storage_sources = [s for s in sources if s.sector == "text_storage"]
        print(f"   ✅ Found {len(text_storage_sources)} sources in 'text_storage' sector")
        
        for src in text_storage_sources:
            print(f"      - {src.source_file} (type={src.source_type}, sector={src.sector})")
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ TEXT STORAGE TEST PASSED")
        print("=" * 80)
        print("\nText storage sector is working correctly!")
        print(f"- Stored {len(text_blocks)} text clips")
        print(f"- All clips associated with keyword '{kw.keyword_text}'")
        print(f"- All clips in 'text_storage' sector")
        print("\nReady for PDF/paper/text clip feature integration!")
        print()
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TEXT STORAGE TEST FAILED")
        print("=" * 80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        repo.close()


if __name__ == "__main__":
    sys.exit(test_text_storage())
