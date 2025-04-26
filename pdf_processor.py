import PyPDF2
import pdfplumber
import logging
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_with_pdfplumber(file_path: str) -> str:
    """
    Extract text from PDF using pdfplumber (better at preserving layout)
    """
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
                text += "\n\n"  # Add separation between pages
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text with pdfplumber: {str(e)}")
        return ""

def extract_text_with_pypdf2(file_path: str) -> str:
    """
    Extract text from PDF using PyPDF2 (fallback method)
    """
    try:
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
                text += "\n\n"  # Add separation between pages
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text with PyPDF2: {str(e)}")
        return ""

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF using multiple methods for better accuracy
    """
    # Try pdfplumber first (better with formatting)
    text = extract_text_with_pdfplumber(file_path)
    print(f"Extracted text with pdfplumber: {text}...")  # Print first 100 characters for debugging
    
    # If that fails or returns empty text, try PyPDF2
    if not text:
        logger.info("pdfplumber extraction failed or returned empty text, trying PyPDF2...")
        text = extract_text_with_pypdf2(file_path)
    
    # If text is still empty, log an error
    if not text:
        logger.error(f"Failed to extract any text from {file_path}")
        return "ERROR: Could not extract text from the PDF. It may be a scanned document requiring OCR."
    
    return text

def chunk_text(text: str, max_chunk_size: int = 8000) -> List[str]:
    """
    Split text into manageable chunks for the LLM
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the limit, start a new chunk
        if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk if it has content
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks