import re
from typing import str


class TextPreprocessor:
    """
    Text preprocessing class to clean and standardize extracted text.
    """
    
    def __init__(self):
        # Common patterns for cleaning
        self.patterns = {
            # Remove excessive whitespace
            'excessive_spaces': re.compile(r' {2,}'),
            'excessive_newlines': re.compile(r'\n{3,}'),
            
            # Fix common parsing artifacts
            'page_breaks': re.compile(r'---\s*Page\s+\d+\s*---'),
            'bullet_points': re.compile(r'^[\s]*[•·▪▫‣⁃]\s*', re.MULTILINE),
            'numbering': re.compile(r'^\s*\d+\.\s+', re.MULTILINE),
            
            # Clean up formatting
            'header_footer': re.compile(r'(?:Header|Footer):\s*', re.IGNORECASE),
            'table_markers': re.compile(r'---\s*Table\s+\d+.*?---'),
            
            # Fix encoding issues
            'smart_quotes': re.compile(r'[""''`]'),
            'unicode_dashes': re.compile(r'[–—]'),
            'weird_chars': re.compile(r'[^\x00-\x7F]+')
        }
        
        # Replacement patterns
        self.replacements = {
            self.patterns['smart_quotes']: '"',
            self.patterns['unicode_dashes']: '-',
            self.patterns['weird_chars']: ' '
        }
    
    def clean_text(self, raw_text: str) -> str:
        """
        Clean and standardize extracted text.
        
        Args:
            raw_text: Raw text extracted from document
            
        Returns:
            Cleaned and standardized text
        """
        if not raw_text:
            return ""
        
        text = raw_text
        
        # Step 1: Handle encoding issues
        text = self._fix_encoding_issues(text)
        
        # Step 2: Remove parsing artifacts
        text = self._remove_parsing_artifacts(text)
        
        # Step 3: Normalize whitespace
        text = self._normalize_whitespace(text)
        
        # Step 4: Clean up formatting
        text = self._clean_formatting(text)
        
        # Step 5: Final cleanup
        text = self._final_cleanup(text)
        
        return text.strip()
    
    def _fix_encoding_issues(self, text: str) -> str:
        """Fix common encoding and character issues."""
        for pattern, replacement in self.replacements.items():
            text = pattern.sub(replacement, text)
        return text
    
    def _remove_parsing_artifacts(self, text: str) -> str:
        """Remove common parsing artifacts like page markers."""
        # Remove page break markers
        text = self.patterns['page_breaks'].sub('\n', text)
        
        # Remove table markers
        text = self.patterns['table_markers'].sub('\n', text)
        
        # Clean header/footer markers
        text = self.patterns['header_footer'].sub('', text)
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize spacing and line breaks."""
        # Replace multiple spaces with single space
        text = self.patterns['excessive_spaces'].sub(' ', text)
        
        # Replace multiple newlines with double newline
        text = self.patterns['excessive_newlines'].sub('\n\n', text)
        
        # Fix spacing around line breaks
        text = re.sub(r'\s*\n\s*', '\n', text)
        
        return text
    
    def _clean_formatting(self, text: str) -> str:
        """Clean up bullet points and numbering."""
        # Standardize bullet points
        text = self.patterns['bullet_points'].sub('• ', text)
        
        # Clean up numbered lists
        text = re.sub(r'^\s*(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Final text cleanup steps."""
        # Remove leading/trailing whitespace from each line
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        
        # Remove empty lines at the beginning and end
        while cleaned_lines and not cleaned_lines[0]:
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        
        # Rejoin lines
        text = '\n'.join(cleaned_lines)
        
        # Final whitespace normalization
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text