import os
import logging
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from markitdown import MarkItDown
from openai import OpenAI

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize OpenAI client for MarkItDown
try:
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    md = MarkItDown(llm_client=openai_client, llm_model="gpt-4o")
    logger.debug("Successfully initialized MarkItDown with OpenAI integration")
except Exception as e:
    logger.error(f"Failed to initialize MarkItDown: {str(e)}")
    raise

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    try:
        if '.' not in filename:
            logger.error("No file extension found")
            return False

        extension = filename.rsplit('.', 1)[1].lower()
        if not extension in ALLOWED_EXTENSIONS:
            logger.error(f"Extension {extension} not in allowed extensions")
            return False

        if not os.path.splitext(filename)[0]:
            logger.error("No filename part found")
            return False

        return True
    except Exception as e:
        logger.error(f"Error checking file extension: {str(e)}")
        return False

def extract_text_from_pdf(file_path):
    """Extract text content from a PDF file."""
    logger.debug(f"Attempting to extract text from PDF: {file_path}")
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"Cannot read PDF file: {file_path}")

        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                logger.debug(f"Processing page {page_num + 1}")
                text += page.extract_text()

        if not text.strip():
            raise ValueError("No text content extracted from PDF")

        logger.debug("PDF text extraction successful")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {str(e)}", exc_info=True)
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

        # Get file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("Word document is empty")

        logger.debug(f"File size: {file_size} bytes")

        # Convert document using MarkItDown
        logger.debug("Starting MarkItDown conversion")
        result = md.convert(file_path)

        if not result:
            raise ValueError("MarkItDown conversion failed - no result returned")

        if not hasattr(result, 'text_content'):
            raise ValueError("MarkItDown conversion failed - no text content attribute")

        if not result.text_content or not result.text_content.strip():
            raise ValueError("MarkItDown conversion resulted in empty content")

        logger.debug("Word document text extraction successful")
        return result.text_content

    except Exception as e:
        logger.error(f"Failed to extract text from Word document: {str(e)}", exc_info=True)
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
        logger.error(f"Error in process_document: {str(e)}", exc_info=True)
        raise