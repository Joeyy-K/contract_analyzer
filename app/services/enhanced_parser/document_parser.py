import os
import mimetypes
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .txt_parser import TXTParser
from .text_preprocessor import TextPreprocessor
from .section_detector import SectionDetector


class DocumentParser:
    """
    Unified document parser that handles multiple file formats with a single interface.
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']
        self.format_parsers = {
            '.pdf': PDFParser(),
            '.docx': DOCXParser(),
            '.txt': TXTParser()
        }
        self.preprocessor = TextPreprocessor()
        self.section_detector = SectionDetector()
    
    def is_supported(self, file_path: str) -> bool:
        """Check if the file format is supported."""
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.supported_formats
    
    def _detect_format(self, file_path: str) -> str:
        """Auto-detect file format from extension and MIME type."""
        _, ext = os.path.splitext(file_path.lower())
        
        # Verify with MIME type as backup
        mime_type, _ = mimetypes.guess_type(file_path)
        
        format_mapping = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.txt': 'txt'
        }
        
        if ext in format_mapping:
            return format_mapping[ext]
        
        # Fallback to MIME type detection
        if mime_type:
            if 'pdf' in mime_type:
                return 'pdf'
            elif 'word' in mime_type or 'officedocument' in mime_type:
                return 'docx'
            elif 'text' in mime_type:
                return 'txt'
        
        raise ValueError(f"Unsupported file format: {ext}")
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse document with auto-format detection.
        
        Returns:
            Dict containing:
            - text: str (extracted text)
            - metadata: dict (file metadata)
            - sections: list (detected sections)
            - format: str (detected format)
            - success: bool
            - errors: list (any errors encountered)
        """
        result = {
            'text': '',
            'metadata': {},
            'sections': [],
            'format': '',
            'success': False,
            'errors': []
        }
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check if supported
            if not self.is_supported(file_path):
                raise ValueError(f"Unsupported file format: {file_path}")
            
            # Detect format
            format_type = self._detect_format(file_path)
            result['format'] = format_type
            
            # Get appropriate parser
            ext = '.' + format_type
            parser = self.format_parsers[ext]
            
            # Parse document
            parsed_data = parser.parse(file_path)
            
            if not parsed_data['success']:
                result['errors'].extend(parsed_data.get('errors', []))
                return result
            
            # Extract raw text and metadata
            raw_text = parsed_data['text']
            result['metadata'] = parsed_data.get('metadata', {})
            
            # Preprocess text
            cleaned_text = self.preprocessor.clean_text(raw_text)
            result['text'] = cleaned_text
            
            # Detect sections
            sections = self.section_detector.detect_sections(cleaned_text)
            result['sections'] = sections
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"Error parsing document: {str(e)}")
            result['success'] = False
        
        return result
    
    def parse_bytes(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse document from bytes content.
        Useful for uploaded files without saving to disk.
        """
        result = {
            'text': '',
            'metadata': {},
            'sections': [],
            'format': '',
            'success': False,
            'errors': []
        }
        
        try:
            # Detect format from filename
            format_type = self._detect_format(filename)
            result['format'] = format_type
            
            # Get appropriate parser
            ext = '.' + format_type
            parser = self.format_parsers[ext]
            
            # Parse from bytes if parser supports it
            if hasattr(parser, 'parse_bytes'):
                parsed_data = parser.parse_bytes(file_content)
            else:
                # Save temporarily and parse
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
                    tmp_file.write(file_content)
                    tmp_file.flush()
                    parsed_data = parser.parse(tmp_file.name)
                    os.unlink(tmp_file.name)
            
            if not parsed_data['success']:
                result['errors'].extend(parsed_data.get('errors', []))
                return result
            
            # Process the same way as file parsing
            raw_text = parsed_data['text']
            result['metadata'] = parsed_data.get('metadata', {})
            
            cleaned_text = self.preprocessor.clean_text(raw_text)
            result['text'] = cleaned_text
            
            sections = self.section_detector.detect_sections(cleaned_text)
            result['sections'] = sections
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"Error parsing document: {str(e)}")
            result['success'] = False
        
        return result