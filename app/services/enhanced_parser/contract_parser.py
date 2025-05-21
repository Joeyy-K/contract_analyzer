import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from .document_parser import DocumentParser
from .text_preprocessor import TextPreprocessor
from .section_detector import SectionDetector


class ContractParser:
    """
    Main contract parsing interface that ties together all parsing components.
    Provides a unified interface for parsing contracts from various file formats.
    """
    
    def __init__(self):
        self.document_parser = DocumentParser()
        self.preprocessor = TextPreprocessor()
        self.section_detector = SectionDetector()
    
    def process_contract(self, file_path: str) -> Dict[str, Any]:
        """
        Process a contract document from start to finish.
        
        Args:
            file_path: Path to the contract file
            
        Returns:
            Comprehensive parsing results with all extracted information
        """
        result = {
            'success': False,
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'raw_text': '',
            'cleaned_text': '',
            'sections': [],
            'metadata': {},
            'processing_info': {},
            'errors': []
        }
        
        try:
            # Step 1: Parse the document
            parsing_result = self.document_parser.parse(file_path)
            
            if not parsing_result['success']:
                result['errors'].extend(parsing_result['errors'])
                return result
            
            # Store raw text and metadata
            result['raw_text'] = parsing_result['text']
            result['metadata'] = parsing_result['metadata']
            result['processing_info']['format'] = parsing_result['format']
            
            # Step 2: Preprocess the text
            cleaned_text = self.preprocessor.clean_text(parsing_result['text'])
            result['cleaned_text'] = cleaned_text
            
            # Step 3: Detect sections
            sections = self.section_detector.detect_sections(cleaned_text)
            result['sections'] = sections
            
            # Step 4: Add processing statistics
            result['processing_info'].update({
                'raw_text_length': len(result['raw_text']),
                'cleaned_text_length': len(result['cleaned_text']),
                'sections_detected': len(sections),
                'processing_method': 'enhanced_parser'
            })
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"Error processing contract: {str(e)}")
            result['success'] = False
        
        return result
    
    def process_contract_bytes(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process a contract document from bytes content.
        Useful for uploaded files without saving to disk.
        
        Args:
            file_content: File content as bytes
            filename: Original filename for format detection
            
        Returns:
            Comprehensive parsing results
        """
        result = {
            'success': False,
            'file_name': filename,
            'raw_text': '',
            'cleaned_text': '',
            'sections': [],
            'metadata': {},
            'processing_info': {},
            'errors': []
        }
        
        try:
            # Step 1: Parse the document from bytes
            parsing_result = self.document_parser.parse_bytes(file_content, filename)
            
            if not parsing_result['success']:
                result['errors'].extend(parsing_result['errors'])
                return result
            
            # Store results from parsing
            result['raw_text'] = parsing_result['text']
            result['metadata'] = parsing_result['metadata']
            result['processing_info']['format'] = parsing_result['format']
            
            # Step 2: Preprocess the text
            cleaned_text = self.preprocessor.clean_text(parsing_result['text'])
            result['cleaned_text'] = cleaned_text
            
            # Step 3: Detect sections
            sections = self.section_detector.detect_sections(cleaned_text)
            result['sections'] = sections
            
            # Step 4: Add processing statistics
            result['processing_info'].update({
                'raw_text_length': len(result['raw_text']),
                'cleaned_text_length': len(result['cleaned_text']),
                'sections_detected': len(sections),
                'processing_method': 'enhanced_parser'
            })
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"Error processing contract: {str(e)}")
            result['success'] = False
        
        return result
    
    def get_section_by_type(self, sections: List[Dict[str, Any]], section_type: str) -> Optional[Dict[str, Any]]:
        """
        Find a specific section by its type.
        
        Args:
            sections: List of detected sections
            section_type: Type of section to find (e.g., 'definitions', 'payment')
            
        Returns:
            Section dictionary if found, None otherwise
        """
        for section in sections:
            if section.get('type') == section_type:
                return section
        return None
    
    def get_sections_by_level(self, sections: List[Dict[str, Any]], level: int) -> List[Dict[str, Any]]:
        """
        Get all sections at a specific hierarchical level.
        
        Args:
            sections: List of detected sections
            level: Hierarchical level (1 = top level, 2 = second level, etc.)
            
        Returns:
            List of sections at the specified level
        """
        return [section for section in sections if section.get('level') == level]
    
    def search_sections(self, sections: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Search for sections containing specific keywords.
        
        Args:
            sections: List of detected sections
            query: Search query (keywords)
            
        Returns:
            List of matching sections
        """
        query_lower = query.lower()
        matching_sections = []
        
        for section in sections:
            # Search in title and content
            title_match = query_lower in section.get('title', '').lower()
            content_match = query_lower in section.get('content', '').lower()
            
            if title_match or content_match:
                matching_sections.append(section)
        
        return matching_sections
    
    def validate_contract_structure(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate the structure and completeness of a parsed contract.
        
        Args:
            sections: List of detected sections
            
        Returns:
            Validation results with recommendations
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'recommendations': [],
            'statistics': {}
        }
        
        # Check for essential sections
        essential_sections = ['definitions', 'obligations', 'payment', 'termination']
        missing_sections = []
        
        found_types = [section.get('type') for section in sections]
        
        for essential in essential_sections:
            if essential not in found_types:
                missing_sections.append(essential)
        
        if missing_sections:
            validation['warnings'].append(f"Missing essential sections: {', '.join(missing_sections)}")
            validation['recommendations'].append("Consider adding missing essential sections for completeness")
        
        # Check section hierarchy
        levels = [section.get('level', 1) for section in sections]
        if levels and max(levels) > 3:
            validation['warnings'].append("Deep section nesting detected (more than 3 levels)")
            validation['recommendations'].append("Consider flattening section structure for clarity")
        
        # Check section content length
        short_sections = [s for s in sections if len(s.get('content', '')) < 50]
        if len(short_sections) > len(sections) * 0.3:  # More than 30% are too short
            validation['warnings'].append("Many sections have very short content")
            validation['recommendations'].append("Review section content for completeness")
        
        # Statistics
        validation['statistics'] = {
            'total_sections': len(sections),
            'top_level_sections': len(self.get_sections_by_level(sections, 1)),
            'average_content_length': sum(len(s.get('content', '')) for s in sections) / len(sections) if sections else 0,
            'section_types_found': list(set(found_types))
        }
        
        # Overall validation
        if not missing_sections and len(validation['warnings']) == 0:
            validation['is_valid'] = True
        else:
            validation['is_valid'] = len(missing_sections) <= 1  # Allow one missing section
        
        return validation
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return self.document_parser.supported_formats
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if a file format is supported."""
        return self.document_parser.is_supported(file_path)