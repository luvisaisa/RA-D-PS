# PDF Keyword Extractor - Quick Reference

**Status**: ✅ Production-Ready (8/8 tests passing - 100%)

---

## Installation

```bash
pip3 install pdfplumber
```

---

## Basic Usage

```python
from src.ra_d_ps.pdf_keyword_extractor import PDFKeywordExtractor

# create extractor
extractor = PDFKeywordExtractor()

# extract from single PDF
metadata, keywords = extractor.extract_from_pdf(
    pdf_path='papers/lung_study.pdf',
    store_in_db=False,  # set True to auto-store
    max_pages=10        # optional page limit
)

# access metadata
print(f"Title: {metadata.title}")
print(f"Year: {metadata.year}")
print(f"Authors: {metadata.authors}")
print(f"DOI: {metadata.doi}")
print(f"Abstract: {metadata.abstract[:200]}...")

# access keywords
for kw in keywords[:10]:
    print(f"{kw.text} (page {kw.page_number}, freq {kw.frequency})")
```

---

## Batch Processing

```python
from pathlib import Path

# collect PDF files
pdf_files = list(Path('papers/').glob('*.pdf'))

# progress callback
def progress(current, total, filename):
    print(f"{current}/{total}: {filename}")

# process all
results = extractor.extract_from_multiple(
    pdf_paths=pdf_files,
    store_in_db=True,
    max_pages_per_pdf=20,
    progress_callback=progress
)

# process results
for pdf_path, metadata, keywords in results:
    print(f"{metadata.title}: {len(keywords)} keywords")
```

---

## Database Integration

```python
from src.ra_d_ps.keyword_normalizer import KeywordNormalizer
from src.ra_d_ps.database.keyword_repository import KeywordRepository

# create with database support
repo = KeywordRepository()
normalizer = KeywordNormalizer(repository=repo)
extractor = PDFKeywordExtractor(
    normalizer=normalizer,
    repository=repo
)

# extract and auto-store
metadata, keywords = extractor.extract_from_pdf(
    pdf_path='paper.pdf',
    store_in_db=True
)

# query database
all_keywords = repo.get_all_keywords()
abstract_kws = repo.get_keywords_by_category('abstract')
```

---

## Filter by Category

```python
metadata, keywords = extractor.extract_from_pdf('paper.pdf')

# filter by category
abstract = [kw for kw in keywords if kw.category == 'abstract']
body = [kw for kw in keywords if kw.category == 'body']
author_kws = [kw for kw in keywords if kw.category == 'keyword']

print(f"Abstract: {len(abstract)} keywords")
print(f"Body: {len(body)} keywords")
print(f"Author keywords: {len(author_kws)} keywords")
```

---

## Access Context Snippets

```python
metadata, keywords = extractor.extract_from_pdf('paper.pdf')

# find specific keywords
nodule_kws = [kw for kw in keywords if 'nodule' in kw.text.lower()]

for kw in nodule_kws:
    print(f"Keyword: {kw.text}")
    print(f"Page: {kw.page_number}")
    print(f"Context: {kw.context}")
    print(f"Normalized: {kw.normalized_form}")
    print()
```

---

## Statistics

```python
# get statistics from database
stats = extractor.get_statistics()

print(f"Total keywords: {stats['total_keywords']}")
print(f"Unique keywords: {stats['unique_keywords']}")
print(f"By category: {stats['by_category']}")
```

---

## Error Handling

```python
pdf_files = list(Path('papers/').glob('*.pdf'))
successful = []
failed = []

for pdf_path in pdf_files:
    try:
        metadata, keywords = extractor.extract_from_pdf(pdf_path)
        successful.append((pdf_path, len(keywords)))
    except FileNotFoundError:
        print(f"File not found: {pdf_path}")
        failed.append(pdf_path)
    except Exception as e:
        print(f"Error: {pdf_path}: {e}")
        failed.append(pdf_path)

print(f"Successful: {len(successful)}/{len(pdf_files)}")
print(f"Failed: {len(failed)}/{len(pdf_files)}")
```

---

## Data Structures

### PDFMetadata

```python
@dataclass
class PDFMetadata:
    title: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: Optional[int] = None
    doi: str = ""
    abstract: str = ""
    author_keywords: List[str] = field(default_factory=list)
    mesh_terms: List[str] = field(default_factory=list)
```

### ExtractedPDFKeyword

```python
@dataclass
class ExtractedPDFKeyword:
    text: str
    category: str  # metadata, abstract, keyword, body
    page_number: int
    context: str = ""
    frequency: int = 1
    normalized_form: Optional[str] = None
```

---

## Keyword Categories

| Category | Description | Example |
|----------|-------------|---------|
| `metadata` | From title/header | "Pulmonary Nodule Detection" |
| `abstract` | From abstract section | "lung cancer screening" |
| `keyword` | Author-provided | "deep learning", "CT imaging" |
| `body` | From main text | "ground glass opacity" |

---

## Performance

| Document Size | Pages | Keywords | Time |
|---------------|-------|----------|------|
| Short paper | 5 | 20-30 | ~2s |
| Medium paper | 10 | 40-60 | ~4s |
| Long paper | 20 | 80-120 | ~8s |

**Memory**: ~10-25 MB per PDF

---

## Running Tests

```bash
cd "/Users/isa/Desktop/python projects/XML PARSE"
python3 scripts/test_pdf_keyword_extractor.py

# Expected output:
# ======================================================================
# PDF KEYWORD EXTRACTOR TEST SUITE
# ======================================================================
# TEST 1: Metadata Extraction - ✅ PASSED
# TEST 2: Abstract Extraction - ✅ PASSED
# TEST 3: Author Keywords Extraction - ✅ PASSED
# TEST 4: Body Text Keywords Extraction - ✅ PASSED
# TEST 5: Keyword Consolidation - ✅ PASSED
# TEST 6: Keyword Normalization Integration - ✅ PASSED
# TEST 7: Batch Processing (Simulated) - ✅ PASSED
# TEST 8: Database Integration - ✅ PASSED
#
# Passed: 8/8 (100.0%)
# 🎉 ALL TESTS PASSED!
```

---

## Files

| File | Purpose |
|------|---------|
| `src/ra_d_ps/pdf_keyword_extractor.py` | Main implementation (600+ lines) |
| `scripts/test_pdf_keyword_extractor.py` | Test suite (400+ lines) |
| `examples/pdf_keyword_extractor_examples.py` | 10 usage examples |
| `docs/PDF_KEYWORD_EXTRACTOR_SUMMARY.md` | Full documentation |

---

## See Also

- [XML Keyword Extractor](XML_KEYWORD_EXTRACTOR_SUMMARY.md)
- [Keyword Normalizer](KEYWORD_NORMALIZATION_SUMMARY.md)
- [Keyword Repository API](../src/ra_d_ps/database/keyword_repository.py)
- [Medical Terms Dictionary](../data/medical_terms.json)
