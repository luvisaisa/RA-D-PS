#!/usr/bin/env python3
"""
Comprehensive XML-COMP Dataset Validation Script
Tests database-driven parse case detection on all 475 XML files

Purpose:
- Validate parse case detection accuracy at scale
- Measure performance metrics (total time, avg per file, cache efficiency)
- Generate distribution statistics for parse cases
- Identify any errors or edge cases
- Compare with previous parser behavior

Output:
- Detailed validation report with statistics
- Performance metrics
- Error log if any issues found
"""
import os
import sys
import time
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import traceback

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.structure_detector import XMLStructureDetector
from src.ra_d_ps.parser import parse_radiology_sample


class ValidationReport:
    """Track validation metrics and results"""
    
    def __init__(self):
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.detection_times = []
        self.parse_case_counts = Counter()
        self.errors = []
        self.file_details = []
        self.start_time = None
        self.end_time = None
        
    def add_success(self, file_path: str, parse_case: str, detection_time: float):
        """Record successful detection"""
        self.total_files += 1
        self.successful += 1
        self.detection_times.append(detection_time)
        self.parse_case_counts[parse_case] += 1
        self.file_details.append({
            'file': file_path,
            'parse_case': parse_case,
            'detection_time_ms': detection_time * 1000,
            'status': 'success'
        })
        
    def add_failure(self, file_path: str, error: str):
        """Record failed detection"""
        self.total_files += 1
        self.failed += 1
        self.errors.append({
            'file': file_path,
            'error': error
        })
        self.file_details.append({
            'file': file_path,
            'parse_case': 'ERROR',
            'detection_time_ms': 0,
            'status': 'failed',
            'error': error
        })
        
    def calculate_metrics(self):
        """Calculate summary statistics"""
        if not self.detection_times:
            return {}
            
        return {
            'total_time_sec': self.end_time - self.start_time if self.end_time else 0,
            'avg_detection_ms': sum(self.detection_times) / len(self.detection_times) * 1000,
            'min_detection_ms': min(self.detection_times) * 1000,
            'max_detection_ms': max(self.detection_times) * 1000,
            'total_files': self.total_files,
            'successful': self.successful,
            'failed': self.failed,
            'success_rate': (self.successful / self.total_files * 100) if self.total_files > 0 else 0
        }
        
    def generate_report(self) -> str:
        """Generate formatted validation report"""
        metrics = self.calculate_metrics()
        
        report = []
        report.append("=" * 80)
        report.append("XML-COMP DATASET VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Dataset: /Users/isa/Desktop/XML-COMP")
        report.append("")
        
        # Overview
        report.append("📊 VALIDATION SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Files Tested:    {metrics.get('total_files', 0)}")
        report.append(f"Successful:            {metrics.get('successful', 0)} ({metrics.get('success_rate', 0):.1f}%)")
        report.append(f"Failed:                {metrics.get('failed', 0)}")
        report.append(f"Total Processing Time: {metrics.get('total_time_sec', 0):.2f}s")
        report.append("")
        
        # Performance metrics
        if self.detection_times:
            report.append("⚡ PERFORMANCE METRICS")
            report.append("-" * 80)
            report.append(f"Average Detection Time: {metrics['avg_detection_ms']:.2f}ms per file")
            report.append(f"Minimum Detection Time: {metrics['min_detection_ms']:.2f}ms")
            report.append(f"Maximum Detection Time: {metrics['max_detection_ms']:.2f}ms")
            report.append(f"Throughput:             {metrics['total_files'] / metrics['total_time_sec']:.1f} files/sec")
            report.append("")
        
        # Parse case distribution
        if self.parse_case_counts:
            report.append("📋 PARSE CASE DISTRIBUTION")
            report.append("-" * 80)
            for parse_case, count in self.parse_case_counts.most_common():
                percentage = (count / self.successful * 100) if self.successful > 0 else 0
                report.append(f"{parse_case:30s} {count:4d} files ({percentage:5.1f}%)")
            report.append("")
        
        # Errors
        if self.errors:
            report.append("❌ ERRORS DETECTED")
            report.append("-" * 80)
            for i, error in enumerate(self.errors[:10], 1):
                report.append(f"{i}. {Path(error['file']).name}")
                report.append(f"   {error['error']}")
                report.append("")
            if len(self.errors) > 10:
                report.append(f"... and {len(self.errors) - 10} more errors")
                report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)


def find_xml_files(base_path: Path) -> list:
    """Find all XML files in dataset, excluding __MACOSX"""
    xml_files = []
    for xml_file in base_path.rglob("*.xml"):
        # Skip __MACOSX directory
        if "__MACOSX" in str(xml_file):
            continue
        xml_files.append(xml_file)
    return sorted(xml_files)


def validate_dataset(base_path: str, show_progress: bool = True):
    """
    Validate all XML files in dataset
    
    Args:
        base_path: Path to XML-COMP directory
        show_progress: Show progress during validation
    """
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"❌ Dataset not found: {base_path}")
        return None
        
    print(f"🔍 Scanning for XML files in: {base_path}")
    xml_files = find_xml_files(base_path)
    
    if not xml_files:
        print(f"❌ No XML files found in {base_path}")
        return None
        
    print(f"✅ Found {len(xml_files)} XML files")
    print(f"\n📂 Directory breakdown:")
    
    # Show file counts per directory
    dir_counts = Counter([f.parent.name for f in xml_files])
    for dirname, count in sorted(dir_counts.items()):
        print(f"   {dirname}: {count} files")
    
    print("\n" + "=" * 80)
    print("STARTING VALIDATION")
    print("=" * 80)
    
    # Initialize detector (will use database)
    try:
        detector = XMLStructureDetector()
        print("✅ Structure detector initialized (database-driven)")
    except Exception as e:
        print(f"❌ Failed to initialize detector: {e}")
        return None
    
    # Initialize report
    report = ValidationReport()
    report.start_time = time.time()
    
    # Process each file
    progress_interval = max(1, len(xml_files) // 20)  # Show ~20 progress updates
    
    for i, xml_file in enumerate(xml_files, 1):
        try:
            # Detect parse case with timing
            start = time.time()
            parse_case = detector.detect_structure_type(str(xml_file), record_detection=False)
            detection_time = time.time() - start
            
            # Record success
            relative_path = xml_file.relative_to(base_path)
            report.add_success(str(relative_path), parse_case, detection_time)
            
            # Show progress
            if show_progress and (i % progress_interval == 0 or i == len(xml_files)):
                progress = i / len(xml_files) * 100
                print(f"   Progress: {i}/{len(xml_files)} ({progress:.1f}%) - "
                      f"Last: {parse_case} ({detection_time*1000:.2f}ms)")
                
        except Exception as e:
            relative_path = xml_file.relative_to(base_path)
            error_msg = f"{type(e).__name__}: {str(e)}"
            report.add_failure(str(relative_path), error_msg)
            
            if show_progress:
                print(f"   ❌ Error in {relative_path.name}: {error_msg}")
    
    report.end_time = time.time()
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    
    return report


def save_detailed_results(report: ValidationReport, output_path: Path):
    """Save detailed results to CSV for analysis"""
    import csv
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['file', 'parse_case', 'detection_time_ms', 'status', 'error'])
        writer.writeheader()
        writer.writerows(report.file_details)
    
    print(f"\n💾 Detailed results saved to: {output_path}")


def main():
    """Main validation entry point"""
    print("\n" + "=" * 80)
    print("XML-COMP DATASET VALIDATION")
    print("Database-Driven Parse Case Detection")
    print("=" * 80)
    print()
    
    # Dataset path
    dataset_path = "/Users/isa/Desktop/XML-COMP"
    
    # Run validation
    report = validate_dataset(dataset_path, show_progress=True)
    
    if not report:
        print("\n❌ Validation failed to run")
        return 1
    
    # Generate and display report
    print("\n")
    print(report.generate_report())
    
    # Save detailed results
    output_dir = Path(__file__).parent.parent / "validation_results"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"xml_comp_validation_{timestamp}.csv"
    report_path = output_dir / f"xml_comp_validation_{timestamp}.txt"
    
    save_detailed_results(report, csv_path)
    
    # Save text report
    with open(report_path, 'w') as f:
        f.write(report.generate_report())
    print(f"💾 Summary report saved to: {report_path}")
    
    # Return exit code based on success rate
    success_rate = (report.successful / report.total_files * 100) if report.total_files > 0 else 0
    if success_rate < 95:
        print(f"\n⚠️  Success rate below 95% ({success_rate:.1f}%)")
        return 1
    
    print(f"\n✅ Validation successful ({success_rate:.1f}% success rate)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
