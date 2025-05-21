import chardet
from typing import Dict, Any, Optional


class TXTParser:
    """
    Enhanced text file parser with encoding detection and basic metadata extraction.
    """
    
    def __init__(self):
        # Common encodings to try
        self.encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'ascii']
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse text file with automatic encoding detection."""
        result = {
            'text': '',
            'metadata': {},
            'success': False,
            'errors': []
        }
        
        try:
            # First, try to detect encoding
            encoding = self._detect_encoding(file_path)
            
            # Read file with detected encoding
            with open(file_path, 'r', encoding=encoding) as file:
                text = file.read()
            
            # Extract metadata
            result['metadata'] = self._extract_metadata(text, file_path, encoding)
            
            # Clean and process text
            result['text'] = self._clean_text(text)
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"Error parsing text file: {str(e)}")
            result['success'] = False
        
        return result
    
    def parse_bytes(self, file_content: bytes) -> Dict[str, Any]:
        """Parse text from bytes content."""
        result = {
            'text': '',
            'metadata': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Detect encoding from bytes
            encoding = self._detect_encoding_from_bytes(file_content)
            
            # Decode bytes to text
            text = file_content.decode(encoding)
            
            # Extract metadata
            result['metadata'] = self._extract_metadata(text, '', encoding)
            
            # Clean and process text
            result['text'] = self._clean_text(text)
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"Error parsing text file: {str(e)}")
            result['success'] = False
        
        return result
    
    def _detect_encoding(self, file_path: str) -> str:
        """Detect file encoding using multiple methods."""
        # First try chardet
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                return self._detect_encoding_from_bytes(raw_data)
        except:
            pass
        
        # Fallback: try common encodings
        for encoding in self.encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    file.read()
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Last resort
        return 'utf-8'
    
    def _detect_encoding_from_bytes(self, raw_data: bytes) -> str:
        """Detect encoding from raw bytes."""
        # Use chardet if available
        try:
            import chardet
            detected = chardet.detect(raw_data)
            if detected['encoding'] and detected['confidence'] > 0.7:
                return detected['encoding']
        except ImportError:
            pass
        
        # Fallback: try common encodings
        for encoding in self.encodings:
            try:
                raw_data.decode(encoding)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return 'utf-8'
    
    def _extract_metadata(self, text: str, file_path: str, encoding: str) -> Dict[str, Any]:
        """Extract basic metadata from text content."""
        import os
        
        metadata = {
            'encoding': encoding,
            'lines': len(text.splitlines()),
            'characters': len(text),
            'words': len(text.split()),
            'paragraphs': len([p for p in text.split('\n\n') if p.strip()])
        }
        
        # Add file stats if file_path is provided
        if file_path and os.path.exists(file_path):
            stat = os.stat(file_path)
            metadata.update({
                'file_size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime
            })
        
        return metadata
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove BOM if present
        if text.startswith('\ufeff'):
            text = text[1:]
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive whitespace but preserve structure
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip trailing whitespace but keep leading whitespace for indentation
            cleaned_line = line.rstrip()
            cleaned_lines.append(cleaned_line)
        
        # Join lines back and remove excessive blank lines
        text = '\n'.join(cleaned_lines)
        
        # Remove more than 2 consecutive newlines
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()