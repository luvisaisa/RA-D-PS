#!/usr/bin/env python3
"""
Query and display contents of the ra_d_ps PostgreSQL database.
Shows keywords, sectors, text blocks, and statistics.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ra_d_ps.database.keyword_repository import KeywordRepository
from sqlalchemy import text

def main():
    print("=" * 80)
    print("RA-D-PS DATABASE INSPECTION")
    print("=" * 80)
    print()
    
    # Initialize repository
    try:
        repo = KeywordRepository()
        print("✓ Connected to database: ra_d_ps@localhost:5432")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1
    
    # Get database session
    session = repo._get_session()
    
    try:
        # 1. Database Overview
        print("-" * 80)
        print("DATABASE OVERVIEW")
        print("-" * 80)
        
        # Count total keywords
        total_keywords = session.execute(
            text("SELECT COUNT(*) FROM keywords")
        ).scalar()
        print(f"Total Keywords: {total_keywords}")
        
        # Count total keyword sources
        total_sources = session.execute(
            text("SELECT COUNT(*) FROM keyword_sources")
        ).scalar()
        print(f"Total Keyword Sources: {total_sources}")
        
        # Count total text blocks
        total_text_blocks = session.execute(
            text("SELECT COUNT(*) FROM keyword_sources WHERE sector = 'text_storage'")
        ).scalar()
        print(f"Total Text Blocks: {total_text_blocks}")
        
        print()
        
        # 2. Sectors Breakdown
        print("-" * 80)
        print("SECTORS BREAKDOWN")
        print("-" * 80)
        
        sectors = session.execute(
            text("""
                SELECT sector, COUNT(*) as count, 
                       COUNT(DISTINCT keyword_id) as unique_keywords
                FROM keyword_sources 
                GROUP BY sector 
                ORDER BY count DESC
            """)
        ).fetchall()
        
        print(f"{'Sector':<25} {'Total Entries':<15} {'Unique Keywords':<15}")
        print("-" * 80)
        for sector, count, unique_kw in sectors:
            print(f"{sector:<25} {count:<15} {unique_kw:<15}")
        
        print()
        
        # 3. Keywords by Category
        print("-" * 80)
        print("KEYWORDS BY CATEGORY")
        print("-" * 80)
        
        categories = session.execute(
            text("""
                SELECT category, COUNT(*) as count
                FROM keywords
                GROUP BY category
                ORDER BY count DESC
            """)
        ).fetchall()
        
        print(f"{'Category':<20} {'Count':<10}")
        print("-" * 80)
        for category, count in categories:
            cat_display = category if category else "(null)"
            print(f"{cat_display:<20} {count:<10}")
        
        print()
        
        # 4. Top 20 Keywords (by frequency)
        print("-" * 80)
        print("TOP 20 KEYWORDS BY FREQUENCY")
        print("-" * 80)
        
        top_keywords = session.execute(
            text("""
                SELECT k.keyword_text, k.category, 
                       SUM(ks.frequency) as total_freq,
                       COUNT(DISTINCT ks.source_file) as source_count
                FROM keywords k
                JOIN keyword_sources ks ON k.keyword_id = ks.keyword_id
                GROUP BY k.keyword_id, k.keyword_text, k.category
                ORDER BY total_freq DESC
                LIMIT 20
            """)
        ).fetchall()
        
        print(f"{'Rank':<6} {'Keyword':<30} {'Category':<15} {'Frequency':<12} {'Sources':<10}")
        print("-" * 80)
        for i, (kw_text, category, freq, sources) in enumerate(top_keywords, 1):
            cat_display = category if category else "N/A"
            print(f"{i:<6} {kw_text[:28]:<30} {cat_display:<15} {freq:<12} {sources:<10}")
        
        print()
        
        # 5. Recently Added Keywords (last 20)
        print("-" * 80)
        print("RECENTLY ADDED KEYWORDS (Last 20)")
        print("-" * 80)
        
        recent_keywords = session.execute(
            text("""
                SELECT k.keyword_text, k.category, k.created_at
                FROM keywords k
                ORDER BY k.created_at DESC
                LIMIT 20
            """)
        ).fetchall()
        
        print(f"{'Keyword':<35} {'Category':<15} {'Created':<25}")
        print("-" * 80)
        for kw_text, category, created_at in recent_keywords:
            cat_display = category if category else "N/A"
            created_str = str(created_at) if created_at else "N/A"
            print(f"{kw_text[:33]:<35} {cat_display:<15} {created_str:<25}")
        
        print()
        
        # 6. PDF Keywords Sector (if exists)
        print("-" * 80)
        print("PDF_KEYWORDS SECTOR")
        print("-" * 80)
        
        pdf_keywords = session.execute(
            text("""
                SELECT k.keyword_text, k.category, ks.frequency, ks.source_file
                FROM keywords k
                JOIN keyword_sources ks ON k.keyword_id = ks.keyword_id
                WHERE ks.sector = 'pdf_keywords'
                ORDER BY ks.frequency DESC
                LIMIT 20
            """)
        ).fetchall()
        
        if pdf_keywords:
            print(f"{'Keyword':<30} {'Category':<12} {'Freq':<6} {'Source File':<30}")
            print("-" * 80)
            for kw_text, category, freq, source in pdf_keywords:
                cat_display = category if category else "N/A"
                source_display = source[:28] if source else "N/A"
                print(f"{kw_text[:28]:<30} {cat_display:<12} {freq:<6} {source_display:<30}")
        else:
            print("No keywords found in pdf_keywords sector.")
        
        print()
        
        # 7. Text Storage Sector Sample
        print("-" * 80)
        print("TEXT_STORAGE SECTOR (Sample - First 10)")
        print("-" * 80)
        
        text_blocks = session.execute(
            text("""
                SELECT k.keyword_text, ks.source_file, 
                       LENGTH(ks.context) as text_length
                FROM keywords k
                JOIN keyword_sources ks ON k.keyword_id = ks.keyword_id
                WHERE ks.sector = 'text_storage'
                ORDER BY ks.keyword_source_id DESC
                LIMIT 10
            """)
        ).fetchall()
        
        if text_blocks:
            print(f"{'Keyword':<30} {'Source':<30} {'Text Length':<12}")
            print("-" * 80)
            for kw_text, source, length in text_blocks:
                source_display = source[:28] if source else "N/A"
                length_display = f"{length} chars" if length else "N/A"
                print(f"{kw_text[:28]:<30} {source_display:<30} {length_display:<12}")
        else:
            print("No text blocks found in text_storage sector.")
        
        print()
        
        # 8. Search for specific terms
        print("-" * 80)
        print("SEARCH FOR 'perinodular' and 'intranodular'")
        print("-" * 80)
        
        for search_term in ['perinodular', 'intranodular']:
            result = session.execute(
                text("""
                    SELECT k.keyword_text, k.category, 
                           COUNT(ks.keyword_source_id) as source_count
                    FROM keywords k
                    LEFT JOIN keyword_sources ks ON k.keyword_id = ks.keyword_id
                    WHERE k.keyword_text ILIKE :term
                    GROUP BY k.keyword_id, k.keyword_text, k.category
                """),
                {"term": f"%{search_term}%"}
            ).fetchall()
            
            if result:
                print(f"\n✓ Found '{search_term}':")
                for kw_text, category, count in result:
                    cat_display = category if category else "N/A"
                    print(f"  - {kw_text} (category: {cat_display}, sources: {count})")
            else:
                print(f"\n✗ '{search_term}' NOT FOUND in database")
        
        print()
        
        # 9. Source Files
        print("-" * 80)
        print("SOURCE FILES IN DATABASE")
        print("-" * 80)
        
        source_files = session.execute(
            text("""
                SELECT DISTINCT source_file, sector, 
                       COUNT(*) as keyword_count
                FROM keyword_sources
                GROUP BY source_file, sector
                ORDER BY keyword_count DESC
                LIMIT 10
            """)
        ).fetchall()
        
        print(f"{'Source File':<40} {'Sector':<20} {'Keywords':<10}")
        print("-" * 80)
        for source, sector, count in source_files:
            source_display = source[:38] if source else "N/A"
            sector_display = sector if sector else "N/A"
            print(f"{source_display:<40} {sector_display:<20} {count:<10}")
        
        print()
        print("=" * 80)
        print("DATABASE INSPECTION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
