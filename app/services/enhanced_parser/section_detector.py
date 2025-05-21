import re
from typing import List, Dict, Any, Tuple


class SectionDetector:
    """
    Detects and extracts sections from contract documents.
    """
    
    def __init__(self):
        # Patterns for different section header styles
        self.section_patterns = [
            # Numbered sections: "1.", "1.1", "Section 1"
            re.compile(r'^(\d+(?:\.\d+)*\.)\s+(.+)$', re.MULTILINE),
            re.compile(r'^(?:Section|Article)\s+(\d+(?:\.\d+)*)[:\.]?\s*(.*)$', re.MULTILINE | re.IGNORECASE),
            
            # Roman numerals: "I.", "II.", "III."
            re.compile(r'^([IVX]+\.)\s+(.+)$', re.MULTILINE),
            
            # Lettered sections: "A.", "B.", "(a)", "(b)"
            re.compile(r'^([A-Z]\.)\s+(.+)$', re.MULTILINE),
            re.compile(r'^\(([a-z])\)\s+(.+)$', re.MULTILINE),
            
            # ALL CAPS headers
            re.compile(r'^([A-Z\s]{3,})$', re.MULTILINE),
            
            # Title case headers (likely section headers)
            re.compile(r'^([A-Z][a-z\s]+(?:[A-Z][a-z\s]+)*):?\s*$', re.MULTILINE),
        ]
        
        # Common contract section keywords
        self.section_keywords = [
            'definitions', 'interpretation', 'parties', 'scope', 'term', 'duration',
            'obligations', 'payment', 'fees', 'termination', 'confidentiality',
            'warranty', 'liability', 'indemnification', 'dispute', 'governing law',
            'amendment', 'assignment', 'force majeure', 'severability', 'entire agreement',
            'notices', 'counterparts', 'execution', 'representations', 'covenants'
        ]
    
    def detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect and extract sections from text.
        
        Args:
            text: Cleaned document text
            
        Returns:
            List of section dictionaries with metadata
        """
        if not text:
            return []
        
        sections = []
        
        # Find all potential section headers
        potential_headers = self._find_section_headers(text)
        
        if not potential_headers:
            # If no headers found, treat whole text as one section
            return [{
                'number': '1',
                'title': 'Document Content',
                'content': text,
                'start_pos': 0,
                'end_pos': len(text),
                'level': 1,
                'type': 'content'
            }]
        
        # Extract sections based on headers
        for i, header in enumerate(potential_headers):
            section_start = header['start']
            section_end = potential_headers[i + 1]['start'] if i + 1 < len(potential_headers) else len(text)
            
            section_content = text[section_start:section_end].strip()
            
            # Remove the header from content
            header_text = header['full_match']
            if section_content.startswith(header_text):
                section_content = section_content[len(header_text):].strip()
            
            section = {
                'number': header['number'],
                'title': header['title'],
                'content': section_content,
                'start_pos': section_start,
                'end_pos': section_end,
                'level': self._determine_level(header['number']),
                'type': self._classify_section(header['title'])
            }
            
            sections.append(section)
        
        return sections
    
    def _find_section_headers(self, text: str) -> List[Dict[str, Any]]:
        """Find all potential section headers in text."""
        headers = []
        
        for pattern in self.section_patterns:
            for match in pattern.finditer(text):
                if len(match.groups()) >= 2:
                    number = match.group(1).strip()
                    title = match.group(2).strip()
                elif len(match.groups()) == 1:
                    # For ALL CAPS or title case patterns
                    title = match.group(1).strip()
                    number = str(len(headers) + 1)
                else:
                    continue
                
                headers.append({
                    'start': match.start(),
                    'end': match.end(),
                    'number': number,
                    'title': title,
                    'full_match': match.group(0),
                    'pattern_type': str(pattern.pattern)
                })
        
        # Sort by position in text
        headers.sort(key=lambda x: x['start'])
        
        # Remove duplicates and overlapping matches
        headers = self._deduplicate_headers(headers)
        
        return headers
    
    def _deduplicate_headers(self, headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate and overlapping headers."""
        if not headers:
            return []
        
        deduplicated = [headers[0]]
        
        for header in headers[1:]:
            last_header = deduplicated[-1]
            
            # Skip if too close to previous header (likely overlap)
            if header['start'] - last_header['end'] < 10:
                continue
            
            # Skip if title is too similar to previous
            if self._similar_titles(header['title'], last_header['title']):
                continue
            
            deduplicated.append(header)
        
        return deduplicated
    
    def _similar_titles(self, title1: str, title2: str) -> bool:
        """Check if two titles are similar (to avoid duplicates)."""
        # Simple similarity check - could be enhanced
        title1_clean = re.sub(r'[^\w\s]', '', title1.lower())
        title2_clean = re.sub(r'[^\w\s]', '', title2.lower())
        
        return title1_clean == title2_clean
    
    def _determine_level(self, number: str) -> int:
        """Determine the hierarchical level of a section."""
        if re.match(r'^\d+\.$', number):
            return 1  # Top level: "1.", "2."
        elif re.match(r'^\d+\.\d+\.$', number):
            return 2  # Second level: "1.1.", "2.3."
        elif re.match(r'^\d+\.\d+\.\d+\.$', number):
            return 3  # Third level: "1.1.1.", "2.3.4."
        elif re.match(r'^[IVX]+\.$', number):
            return 1  # Roman numerals at top level
        elif re.match(r'^[A-Z]\.$', number):
            return 2  # Letters at second level
        elif re.match(r'^\([a-z]\)$', number):
            return 3  # Parenthetical lowercase letters at third level
        else:
            return 1  # Default to top level
    
    def _classify_section(self, title: str) -> str:
        """Classify section type based on title."""
        title_lower = title.lower()
        
        for keyword in self.section_keywords:
            if keyword in title_lower:
                return keyword
        
        # Check for common patterns
        if any(word in title_lower for word in ['definition', 'meaning', 'interpretation']):
            return 'definitions'
        elif any(word in title_lower for word in ['payment', 'fee', 'cost', 'price']):
            return 'payment'
        elif any(word in title_lower for word in ['term', 'duration', 'period']):
            return 'term'
        elif any(word in title_lower for word in ['obligation', 'duty', 'requirement']):
            return 'obligations'
        elif any(word in title_lower for word in ['termination', 'expiration', 'end']):
            return 'termination'
        elif any(word in title_lower for word in ['confidential', 'non-disclosure', 'privacy']):
            return 'confidentiality'
        elif any(word in title_lower for word in ['dispute', 'resolution', 'arbitration']):
            return 'dispute'
        else:
            return 'general'