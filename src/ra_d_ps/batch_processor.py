"""
Batch Processing Optimizer for RA-D-PS XML Parsing

This module provides intelligent batch processing capabilities that optimize
parsing strategies based on detected XML structure types. It pre-analyzes
files to group them by structure type for more efficient processing.
"""

from typing import Dict, List, Tuple, Set, Optional
from pathlib import Path
import logging
from collections import defaultdict

from .structure_detector import XMLStructureDetector
from .parser import get_expected_attributes_for_case

logger = logging.getLogger(__name__)

class BatchProcessor:
    """
    Intelligent batch processor that optimizes parsing based on structure detection.
    
    This class pre-analyzes XML files to determine their structure types,
    then groups them for optimized batch processing with appropriate
    parsing strategies.
    """
    
    def __init__(self):
        """Initialize the batch processor."""
        self.detector = XMLStructureDetector()
        self.structure_cache = {}
        
    def analyze_batch(self, file_paths: List[str]) -> Dict:
        """
        Analyze a batch of files to determine optimal processing strategy.
        
        Args:
            file_paths: List of XML file paths to analyze
            
        Returns:
            Dictionary with batch analysis results and processing recommendations
        """
        logger.info(f"🔍 Analyzing batch of {len(file_paths)} files...")
        
        # Detect structures for all files
        structure_map = self.detector.batch_detect_structures(file_paths)
        
        # Group files by structure type
        structure_groups = defaultdict(list)
        for file_path, parse_case in structure_map.items():
            structure_groups[parse_case].append(file_path)
        
        # Calculate processing metrics
        total_files = len(file_paths)
        unique_structures = len(structure_groups)
        
        # Identify dominant structure type
        dominant_structure = max(structure_groups.items(), key=lambda x: len(x[1]))
        dominant_case, dominant_files = dominant_structure
        consistency_ratio = len(dominant_files) / total_files
        
        # Estimate processing complexity
        complexity_score = self._calculate_complexity_score(structure_groups)
        
        # Generate processing recommendations
        recommendations = self._generate_processing_recommendations(
            structure_groups, consistency_ratio, complexity_score
        )
        
        analysis = {
            'total_files': total_files,
            'unique_structures': unique_structures,
            'structure_groups': dict(structure_groups),
            'structure_distribution': {k: len(v) for k, v in structure_groups.items()},
            'dominant_structure': dominant_case,
            'dominant_count': len(dominant_files),
            'consistency_ratio': consistency_ratio,
            'complexity_score': complexity_score,
            'recommendations': recommendations,
            'structure_map': structure_map
        }
        
        self._log_analysis_summary(analysis)
        return analysis
    
    def _calculate_complexity_score(self, structure_groups: Dict[str, List[str]]) -> float:
        """
        Calculate processing complexity score based on structure diversity.
        
        Args:
            structure_groups: Groups of files by structure type
            
        Returns:
            Complexity score (0.0 = simple, 1.0 = highly complex)
        """
        # Base complexity on number of different structure types
        structure_count = len(structure_groups)
        
        # Weight by presence of complex structures
        complex_structures = {
            'Complete_Attributes': 0.3,
            'With_Reason_Partial': 0.2,
            'LIDC_Multi_Session_4': 0.4,
            'LIDC_Multi_Session_3': 0.3,
            'Unknown_Structure': 0.5,
            'XML_Parse_Error': 0.8
        }
        
        complexity_weight = 0.0
        total_files = sum(len(files) for files in structure_groups.values())
        
        for structure, files in structure_groups.items():
            weight = complex_structures.get(structure, 0.1)
            file_ratio = len(files) / total_files
            complexity_weight += weight * file_ratio
        
        # Normalize complexity score
        structure_diversity = min(structure_count / 5.0, 1.0)  # Max 5 structures
        final_score = (structure_diversity * 0.6) + (complexity_weight * 0.4)
        
        return min(final_score, 1.0)
    
    def _generate_processing_recommendations(
        self, 
        structure_groups: Dict[str, List[str]], 
        consistency_ratio: float,
        complexity_score: float
    ) -> Dict:
        """
        Generate processing recommendations based on analysis.
        
        Args:
            structure_groups: Groups of files by structure type
            consistency_ratio: Ratio of dominant structure to total files
            complexity_score: Calculated complexity score
            
        Returns:
            Dictionary with processing recommendations
        """
        recommendations = {
            'processing_strategy': 'standard',
            'batch_size': 50,
            'parallel_processing': False,
            'memory_optimization': True,
            'structure_specific_batching': False,
            'warnings': [],
            'optimizations': []
        }
        
        # High consistency - optimize for dominant structure
        if consistency_ratio >= 0.8:
            recommendations['processing_strategy'] = 'optimized_uniform'
            recommendations['optimizations'].append('Single structure optimization enabled')
            
        # High diversity - structure-specific batching
        elif len(structure_groups) > 3:
            recommendations['structure_specific_batching'] = True
            recommendations['processing_strategy'] = 'structure_grouped'
            recommendations['optimizations'].append('Structure-specific batching enabled')
        
        # High complexity - conservative approach
        if complexity_score >= 0.6:
            recommendations['batch_size'] = 25
            recommendations['memory_optimization'] = True
            recommendations['warnings'].append('High complexity detected - using smaller batch sizes')
        
        # Large batch - enable parallel processing
        total_files = sum(len(files) for files in structure_groups.values())
        if total_files > 100:
            recommendations['parallel_processing'] = True
            recommendations['optimizations'].append('Parallel processing recommended for large batch')
        
        # Check for problematic structures
        problematic = ['XML_Parse_Error', 'Unknown_Structure', 'No_Sessions_Found']
        problem_count = sum(len(structure_groups.get(s, [])) for s in problematic)
        
        if problem_count > 0:
            problem_ratio = problem_count / total_files
            recommendations['warnings'].append(
                f'{problem_count} files ({problem_ratio:.1%}) may have parsing issues'
            )
            
            if problem_ratio > 0.2:
                recommendations['batch_size'] = min(recommendations['batch_size'], 20)
                recommendations['warnings'].append('High error rate - reducing batch size')
        
        return recommendations
    
    def create_optimized_batches(
        self, 
        file_paths: List[str], 
        analysis: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Create optimized processing batches based on structure analysis.
        
        Args:
            file_paths: List of file paths to batch
            analysis: Pre-computed analysis (optional)
            
        Returns:
            List of batch dictionaries with processing instructions
        """
        if analysis is None:
            analysis = self.analyze_batch(file_paths)
        
        recommendations = analysis['recommendations']
        structure_groups = analysis['structure_groups']
        
        batches = []
        
        if recommendations['structure_specific_batching']:
            # Create structure-specific batches
            for structure_type, files in structure_groups.items():
                batches.extend(
                    self._create_structure_batches(structure_type, files, recommendations)
                )
        else:
            # Create standard batches
            batch_size = recommendations['batch_size']
            for i in range(0, len(file_paths), batch_size):
                batch_files = file_paths[i:i + batch_size]
                batches.append({
                    'id': len(batches) + 1,
                    'files': batch_files,
                    'size': len(batch_files),
                    'structure_type': 'mixed',
                    'processing_strategy': recommendations['processing_strategy'],
                    'memory_optimization': recommendations['memory_optimization']
                })
        
        logger.info(f"📦 Created {len(batches)} optimized processing batches")
        return batches
    
    def _create_structure_batches(
        self, 
        structure_type: str, 
        files: List[str], 
        recommendations: Dict
    ) -> List[Dict]:
        """Create batches for a specific structure type."""
        batch_size = recommendations['batch_size']
        batches = []
        
        # Adjust batch size based on structure complexity
        expected_attrs = get_expected_attributes_for_case(structure_type)
        attr_complexity = (
            len(expected_attrs.get('header', [])) +
            len(expected_attrs.get('characteristics', [])) +
            len(expected_attrs.get('roi', []))
        )
        
        # Reduce batch size for complex structures
        if attr_complexity > 10:
            batch_size = max(batch_size // 2, 10)
        
        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]
            batches.append({
                'id': f"{structure_type}_{len(batches) + 1}",
                'files': batch_files,
                'size': len(batch_files),
                'structure_type': structure_type,
                'processing_strategy': 'structure_optimized',
                'memory_optimization': recommendations['memory_optimization'],
                'expected_attributes': expected_attrs
            })
        
        return batches
    
    def _log_analysis_summary(self, analysis: Dict):
        """Log analysis summary for user information."""
        logger.info("📊 Batch Analysis Summary:")
        logger.info(f"  📁 Total files: {analysis['total_files']}")
        logger.info(f"  🏗️  Unique structures: {analysis['unique_structures']}")
        logger.info(f"  🎯 Dominant structure: {analysis['dominant_structure']} "
                   f"({analysis['dominant_count']} files)")
        logger.info(f"  📈 Consistency ratio: {analysis['consistency_ratio']:.1%}")
        logger.info(f"  🧩 Complexity score: {analysis['complexity_score']:.2f}")
        
        logger.info("📋 Structure Distribution:")
        for structure, count in analysis['structure_distribution'].items():
            percentage = (count / analysis['total_files']) * 100
            logger.info(f"  {structure}: {count} files ({percentage:.1f}%)")
        
        recs = analysis['recommendations']
        logger.info(f"🔧 Processing Strategy: {recs['processing_strategy']}")
        logger.info(f"📦 Recommended batch size: {recs['batch_size']}")
        
        if recs['warnings']:
            logger.warning("⚠️  Warnings:")
            for warning in recs['warnings']:
                logger.warning(f"  • {warning}")
        
        if recs['optimizations']:
            logger.info("✨ Optimizations:")
            for opt in recs['optimizations']:
                logger.info(f"  • {opt}")


# Convenience functions
def analyze_batch_structure(file_paths: List[str]) -> Dict:
    """
    Convenience function to analyze batch structure.
    
    Args:
        file_paths: List of XML file paths
        
    Returns:
        Batch analysis results
    """
    processor = BatchProcessor()
    return processor.analyze_batch(file_paths)


def create_optimized_processing_plan(file_paths: List[str]) -> Dict:
    """
    Create a complete optimized processing plan for a batch of files.
    
    Args:
        file_paths: List of XML file paths
        
    Returns:
        Complete processing plan with batches and recommendations
    """
    processor = BatchProcessor()
    analysis = processor.analyze_batch(file_paths)
    batches = processor.create_optimized_batches(file_paths, analysis)
    
    return {
        'analysis': analysis,
        'batches': batches,
        'total_batches': len(batches),
        'estimated_processing_time': len(file_paths) * 0.5,  # Rough estimate
        'memory_requirements': 'moderate' if len(file_paths) < 100 else 'high'
    }


if __name__ == "__main__":
    # Example usage
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        # Collect all XML files from provided paths
        file_paths = []
        for arg in sys.argv[1:]:
            path = Path(arg)
            if path.is_file() and path.suffix.lower() == '.xml':
                file_paths.append(str(path))
            elif path.is_dir():
                file_paths.extend(str(f) for f in path.glob('**/*.xml'))
        
        if file_paths:
            plan = create_optimized_processing_plan(file_paths)
            print(f"\n🎯 Processing Plan Created:")
            print(f"  📁 Total files: {len(file_paths)}")
            print(f"  📦 Total batches: {plan['total_batches']}")
            print(f"  ⏱️  Estimated time: {plan['estimated_processing_time']:.1f} seconds")
            print(f"  💾 Memory requirements: {plan['memory_requirements']}")
        else:
            print("No XML files found in provided paths.")
    else:
        print("Usage: python batch_processor.py <xml_file_or_directory> [...]")