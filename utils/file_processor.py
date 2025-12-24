"""File processing utilities for multiple formats."""
import io
from typing import Optional
from pathlib import Path


class FileProcessor:
    """Handle resume file parsing for various formats."""
    
    @staticmethod
    def process_file(file_content: bytes, file_type: str) -> str:
        """Convert various file formats to text."""
        
        if file_type.lower() == "pdf":
            return FileProcessor._extract_pdf(file_content)
        elif file_type.lower() == "docx":
            return FileProcessor._extract_docx(file_content)
        elif file_type.lower() == "txt":
            return file_content.decode('utf-8', errors='ignore')
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    @staticmethod
    def _extract_pdf(file_content: bytes) -> str:
        """Extract text from PDF."""
        try:
            from PyPDF2 import PdfReader
            
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text()
            
            return text
        except ImportError:
            raise ImportError("Install PyPDF2: pip install PyPDF2")
    
    @staticmethod
    def _extract_docx(file_content: bytes) -> str:
        """Extract text from DOCX."""
        try:
            from docx import Document
            
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
        except ImportError:
            raise ImportError("Install python-docx: pip install python-docx")
