import os
import logging
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from markitdown import MarkItDown

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize MarkItDown with error handling
try:
    md = MarkItDown()
except Exception as e:
    logger.error(f"Failed to initialize MarkItDown: {str(e)}")
    raise

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS and \
           os.path.splitext(filename)[0]  # Ensure there's a filename part

def extract_text_from_pdf(file_path):
    """Extract text content from a PDF file."""
    logger.debug(f"Attempting to extract text from PDF: {file_path}")
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                logger.debug(f"Processing page {page_num + 1}")
                text += page.extract_text()
        logger.debug("PDF text extraction successful")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {str(e)}")
        raise

def extract_text_from_word(file_path):
    """Extract text content from a Word document using MarkItDown."""
    logger.debug(f"Attempting to extract text from Word document: {file_path}")
    try:
        # Verify file exists and is readable
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Word document not found at path: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"No read permission for file: {file_path}")

        # Convert document using MarkItDown
        logger.debug("Starting MarkItDown conversion")
        result = md.convert(file_path)

        if not result or not result.text_content:
            raise ValueError("MarkItDown conversion resulted in empty content")

        logger.debug("Word document text extraction successful")
        return result.text_content
    except Exception as e:
        logger.error(f"Failed to extract text from Word document: {str(e)}")
        raise

def process_document(file_path):
    """Process a document file and extract its text content."""
    logger.debug(f"Starting document processing for: {file_path}")
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        file_extension = os.path.splitext(file_path)[1].lower()
        logger.debug(f"Detected file extension: {file_extension}")

        if not file_extension:
            logger.error("No file extension detected")
            raise ValueError("Unable to determine file type - no extension found")

        if not os.path.getsize(file_path):
            logger.error("Empty file detected")
            raise ValueError("The uploaded file is empty")

        if file_extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension in ['.doc', '.docx']:
            return extract_text_from_word(file_path)
        else:
            logger.error(f"Unsupported file type: {file_extension}")
            raise ValueError(f"Unsupported file type: {file_extension}")
    except Exception as e:
        logger.error(f"Error in process_document: {str(e)}")
        raise