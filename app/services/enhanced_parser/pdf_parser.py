import io
from typing import Dict, Any, Optional
import logging

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


class PDFParser:
    """
    Enhanced PDF parser with multiple extraction strategies and OCR fallback.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.extraction_methods = []
        
        # Register available extraction methods in order of preference
        if HAS_PDFPLUMBER:
            self.extraction_methods.append(self._parse_with_pdfplumber)
        if HAS_PYMUPDF:
            self.extraction_methods.append(self._parse_with_pymupdf)
        if HAS_PYPDF2:
            self.extraction_methods.append(self._parse_with_pypdf2)
        
        if not self.extraction_methods:
            raise ImportError("No PDF parsing libraries available. Install pdfplumber, PyMuPDF, or PyPDF2")
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF file and extract text with metadata."""
        result = {
            'text': '',
            'metadata': {},
            'success': False,
            'errors': [],
            'method_used': None
        }
        
        # Try each extraction method until one succeeds
        for method in self.extraction_methods:
            try:
                method_result = method(file_path)
                if method_result['success'] and method_result['text'].strip():
                    result.update(method_result)
                    break
            except Exception as e:
                self.logger.warning(f"Method {method.__name__} failed: {str(e)}")
                result['errors'].append(f"{method.__name__}: {str(e)}")
        
        # If no method succeeded and OCR is available, try OCR
        if not result['success'] and HAS_OCR:
            try:
                ocr_result = self._parse_with_ocr(file_path)
                if ocr_result['success']:
                    result.update(ocr_result)
            except Exception as e:
                result['errors'].append(f"OCR failed: {str(e)}")
        
        return result
    
    def parse_bytes(self, file_content: bytes) -> Dict[str, Any]:
        """Parse PDF from bytes content."""
        result = {
            'text': '',
            'metadata': {},
            'success': False,
            'errors': [],
            'method_used': None
        }
        
        # Try pdfplumber first (best for structured PDFs)
        if HAS_PDFPLUMBER:
            try:
                result = self._parse_bytes_with_pdfplumber(file_content)
                if result['success']:
                    return result
            except Exception as e:
                result['errors'].append(f"pdfplumber: {str(e)}")
        
        # Try PyMuPDF
        if HAS_PYMUPDF:
            try:
                result = self._parse_bytes_with_pymupdf(file_content)
                if result['success']:
                    return result
            except Exception as e:
                result['errors'].append(f"PyMuPDF: {str(e)}")
        
        # Try PyPDF2
        if HAS_PYPDF2:
            try:
                result = self._parse_bytes_with_pypdf2(file_content)
                if result['success']:
                    return result
            except Exception as e:
                result['errors'].append(f"PyPDF2: {str(e)}")
        
        return result
    
    def _parse_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF using pdfplumber (best for structured PDFs)."""
        import pdfplumber
        
        result = {'text': '', 'metadata': {}, 'success': False, 'method_used': 'pdfplumber'}
        
        with pdfplumber.open(file_path) as pdf:
            # Extract metadata
            result['metadata'] = {
                'pages': len(pdf.pages),
                'author': pdf.metadata.get('Author', ''),
                'title': pdf.metadata.get('Title', ''),
                'creator': pdf.metadata.get('Creator', ''),
                'creation_date': pdf.metadata.get('CreationDate', ''),
                'subject': pdf.metadata.get('Subject', '')
            }
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                
                # Also extract tables if present
                tables = page.extract_tables()
                for table_num, table in enumerate(tables):
                    table_text = f"\n--- Table {table_num + 1} on Page {page_num + 1} ---\n"
                    for row in table:
                        table_text += " | ".join([cell or "" for cell in row]) + "\n"
                    text_parts.append(table_text)
            
            result['text'] = "\n\n".join(text_parts)
            result['success'] = bool(result['text'].strip())
        
        return result
    
    def _parse_bytes_with_pdfplumber(self, file_content: bytes) -> Dict[str, Any]:
        """Parse PDF bytes using pdfplumber."""
        import pdfplumber
        
        result = {'text': '', 'metadata': {}, 'success': False, 'method_used': 'pdfplumber'}
        
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            result['metadata'] = {
                'pages': len(pdf.pages),
                'author': pdf.metadata.get('Author', ''),
                'title': pdf.metadata.get('Title', ''),
                'creator': pdf.metadata.get('Creator', ''),
                'creation_date': pdf.metadata.get('CreationDate', ''),
                'subject': pdf.metadata.get('Subject', '')
            }
            
            text_parts = []
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                
                tables = page.extract_tables()
                for table_num, table in enumerate(tables):
                    table_text = f"\n--- Table {table_num + 1} on Page {page_num + 1} ---\n"
                    for row in table:
                        table_text += " | ".join([cell or "" for cell in row]) + "\n"
                    text_parts.append(table_text)
            
            result['text'] = "\n\n".join(text_parts)
            result['success'] = bool(result['text'].strip())
        
        return result
    
    def _parse_with_pymupdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF using PyMuPDF (fitz)."""
        result = {'text': '', 'metadata': {}, 'success': False, 'method_used': 'PyMuPDF'}
        
        with fitz.open(file_path) as doc:
            # Extract metadata
            metadata = doc.metadata
            result['metadata'] = {
                'pages': doc.page_count,
                'author': metadata.get('author', ''),
                'title': metadata.get('title', ''),
                'creator': metadata.get('creator', ''),
                'creation_date': metadata.get('creationDate', ''),
                'subject': metadata.get('subject', '')
            }
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
            
            result['text'] = "\n\n".join(text_parts)
            result['success'] = bool(result['text'].strip())
        
        return result
    
    def _parse_bytes_with_pymupdf(self, file_content: bytes) -> Dict[str, Any]:
        """Parse PDF bytes using PyMuPDF."""
        result = {'text': '', 'metadata': {}, 'success': False, 'method_used': 'PyMuPDF'}
        
        with fitz.open(stream=file_content, filetype="pdf") as doc:
            metadata = doc.metadata
            result['metadata'] = {
                'pages': doc.page_count,
                'author': metadata.get('author', ''),
                'title': metadata.get('title', ''),
                'creator': metadata.get('creator', ''),
                'creation_date': metadata.get('creationDate', ''),
                'subject': metadata.get('subject', '')
            }
            
            text_parts = []
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
            
            result['text'] = "\n\n".join(text_parts)
            result['success'] = bool(result['text'].strip())
        
        return result
    
    def _parse_with_pypdf2(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF using PyPDF2."""
        result = {'text': '', 'metadata': {}, 'success': False, 'method_used': 'PyPDF2'}
        
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Extract metadata
            metadata = reader.metadata
            result['metadata'] = {
                'pages': len(reader.pages),
                'author': metadata.get('/Author', '') if metadata else '',
                'title': metadata.get('/Title', '') if metadata else '',
                'creator': metadata.get('/Creator', '') if metadata else '',
                'creation_date': metadata.get('/CreationDate', '') if metadata else '',
                'subject': metadata.get('/Subject', '') if metadata else ''
            }
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
            
            result['text'] = "\n\n".join(text_parts)
            result['success'] = bool(result['text'].strip())
        
        return result
    
    def _parse_bytes_with_pypdf2(self, file_content: bytes) -> Dict[str, Any]:
        """Parse PDF bytes using PyPDF2."""
        result = {'text': '', 'metadata': {}, 'success': False, 'method_used': 'PyPDF2'}
        
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        
        metadata = reader.metadata
        result['metadata'] = {
            'pages': len(reader.pages),
            'author': metadata.get('/Author', '') if metadata else '',
            'title': metadata.get('/Title', '') if metadata else '',
            'creator': metadata.get('/Creator', '') if metadata else '',
            'creation_date': metadata.get('/CreationDate', '') if metadata else '',
            'subject': metadata.get('/Subject', '') if metadata else ''
        }
        
        text_parts = []
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
        
        result['text'] = "\n\n".join(text_parts)
        result['success'] = bool(result['text'].strip())
        
        return result
    
    def _parse_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF using OCR (for scanned documents)."""
        result = {'text': '', 'metadata': {}, 'success': False, 'method_used': 'OCR'}
        
        # Convert PDF pages to images and OCR them
        with fitz.open(file_path) as doc:
            result['metadata'] = {'pages': doc.page_count}
            
            text_parts = []
            for page_num in range(doc.page_count):
                page = doc[page_num]
                # Convert page to image
                pix = page.get_pixmap()
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                
                # OCR the image
                page_text = pytesseract.image_to_string(img)
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num + 1} (OCR) ---\n{page_text}")
            
            result['text'] = "\n\n".join(text_parts)
            result['success'] = bool(result['text'].strip())
        
        return result
