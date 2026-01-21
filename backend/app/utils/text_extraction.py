"""
Text Extraction Utility
Extracts text from various file formats (PDF, DOCX, TXT, MD)
"""
import os
from pathlib import Path
from typing import Optional


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text content from a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text content
    """
    print(f"[Text Extraction] Extracting text from: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"[Text Extraction] ✗ ERROR: File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_ext = Path(file_path).suffix.lower()
    print(f"[Text Extraction] File extension: {file_ext}")
    
    try:
        if file_ext == '.txt' or file_ext == '.md':
            print(f"[Text Extraction] Reading text file...")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            print(f"[Text Extraction] ✓ Text extracted: {len(content)} characters")
            return content
        
        elif file_ext == '.pdf':
            print(f"[Text Extraction] Extracting from PDF...")
            try:
                import PyPDF2
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    page_count = len(pdf_reader.pages)
                    print(f"[Text Extraction] PDF has {page_count} pages")
                    for i, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        if (i + 1) % 10 == 0:
                            print(f"[Text Extraction] Processed {i + 1}/{page_count} pages...")
                print(f"[Text Extraction] ✓ PDF extracted: {len(text)} characters")
                return text
            except ImportError as ie:
                error_msg = "PyPDF2 not installed. Install with: pip install PyPDF2"
                print(f"[Text Extraction] ✗ ERROR: {error_msg}")
                raise ImportError(error_msg)
            except Exception as e:
                error_str = str(e).lower()
                # Check if it's a PyCryptodome/AES encryption issue
                if "pycryptodome" in error_str or "aes" in error_str or "cryptography" in error_str:
                    print(f"[Text Extraction] ⚠️ PDF encryption detected. Trying alternative extraction method...")
                    # Try using pdfplumber as fallback (handles encrypted PDFs better)
                    try:
                        import pdfplumber
                        text = ""
                        with pdfplumber.open(file_path) as pdf:
                            page_count = len(pdf.pages)
                            print(f"[Text Extraction] PDF has {page_count} pages (using pdfplumber)")
                            for i, page in enumerate(pdf.pages):
                                page_text = page.extract_text()
                                if page_text:
                                    text += page_text + "\n"
                                if (i + 1) % 10 == 0:
                                    print(f"[Text Extraction] Processed {i + 1}/{page_count} pages...")
                        print(f"[Text Extraction] ✓ PDF extracted (pdfplumber): {len(text)} characters")
                        return text
                    except ImportError:
                        error_msg = (
                            "PDF requires PyCryptodome for AES encryption. "
                            "Install with: pip install pycryptodome\n"
                            "OR install pdfplumber as alternative: pip install pdfplumber"
                        )
                        print(f"[Text Extraction] ✗ ERROR: {error_msg}")
                        raise ImportError(error_msg)
                    except Exception as pdfplumber_error:
                        error_msg = (
                            f"Error extracting encrypted PDF with pdfplumber: {str(pdfplumber_error)}. "
                            "The PDF may be password-protected or corrupted."
                        )
                        print(f"[Text Extraction] ✗ ERROR: {error_msg}")
                        raise Exception(error_msg)
                else:
                    # Other PDF extraction errors
                    error_msg = f"Error extracting PDF: {str(e)}"
                    print(f"[Text Extraction] ✗ ERROR: {error_msg}")
                    raise Exception(error_msg)
        
        elif file_ext in ['.docx', '.doc']:
            print(f"[Text Extraction] Extracting from DOCX...")
            try:
                from docx import Document
                doc = Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                print(f"[Text Extraction] ✓ DOCX extracted: {len(text)} characters")
                return text
            except ImportError:
                error_msg = "python-docx not installed. Install with: pip install python-docx"
                print(f"[Text Extraction] ✗ ERROR: {error_msg}")
                raise ImportError(error_msg)
            except Exception as e:
                error_msg = f"Error extracting DOCX: {str(e)}"
                print(f"[Text Extraction] ✗ ERROR: {error_msg}")
                raise Exception(error_msg)
        
        else:
            error_msg = f"Unsupported file type: {file_ext}"
            print(f"[Text Extraction] ✗ ERROR: {error_msg}")
            raise ValueError(error_msg)
            
    except Exception as e:
        print(f"[Text Extraction] ✗ ERROR extracting text: {str(e)}")
        raise

