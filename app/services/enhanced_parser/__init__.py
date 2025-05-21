"""
Enhanced document parser for contract processing.

This package provides comprehensive document parsing capabilities for contracts
in multiple formats (PDF, DOCX, TXT) with text preprocessing and section detection.
"""

from .contract_parser import ContractParser
from .document_parser import DocumentParser
from .text_preprocessor import TextPreprocessor
from .section_detector import SectionDetector
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .txt_parser import TXTParser

__all__ = [
    'ContractParser',
    'DocumentParser', 
    'TextPreprocessor',
    'SectionDetector',
    'PDFParser',
    'DOCXParser',
    'TXTParser'
]

# Version
__version__ = '1.0.0'