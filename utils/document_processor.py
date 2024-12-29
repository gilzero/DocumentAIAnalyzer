import os
import logging
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from markitdown import MarkItDown
from openai import OpenAI

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client for MarkItDown
try:
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    md = MarkItDown(llm_client=openai_client, llm_model="gpt-4o")
    logger.debug("Successfully initialized MarkItDown with OpenAI integration")
except Exception as e:
    logger.error(f"Failed to initialize MarkItDown: {str(e)}", exc_info=True)
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

def check_file_size(file_path, max_size_mb=16):
    """Check if file size is within acceptable limits."""
    try:
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValueError(f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)")
        if file_size == 0:
            raise ValueError("File is empty")
        return file_size
    except OSError as e:
        raise ValueError(f"Error checking file size: {str(e)}")

def extract_text_from_word(file_path):
    """Extract text content from a Word document using MarkItDown."""
    logger.debug(f"Attempting to extract text from Word document: {file_path}")
    try:
        # Verify file exists and is readable
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Word document not found at path: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"No read permission for file: {file_path}")

        # Check file size
        file_size = check_file_size(file_path)
        logger.debug(f"File size: {file_size / 1024:.1f}KB")

        # Convert document using MarkItDown
        logger.debug("Starting MarkItDown conversion")
        try:
            # Optional memory usage logging if psutil is available
            try:
                import psutil
                process = psutil.Process(os.getpid())
                logger.debug(f"Memory usage before conversion: {process.memory_info().rss / 1024 / 1024:.1f}MB")
            except ImportError:
                logger.debug("psutil not available - skipping memory usage logging")

            result = md.convert(file_path)

            # Log memory usage after conversion if psutil is available
            try:
                import psutil
                process = psutil.Process(os.getpid())
                logger.debug(f"Memory usage after conversion: {process.memory_info().rss / 1024 / 1024:.1f}MB")
            except ImportError:
                pass

            logger.debug("MarkItDown conversion completed")

        except Exception as e:
            logger.error("MarkItDown conversion failed", exc_info=True)
            logger.error(f"Error details: {str(e)}")
            if "codec can't decode" in str(e):
                raise ValueError("Document appears to be corrupted or using unsupported encoding")
            elif "memory" in str(e).lower():
                raise ValueError("Document processing exceeded memory limits")
            else:
                raise ValueError(f"Document conversion failed: {str(e)}")

        if not result:
            logger.error("MarkItDown returned None result")
            raise ValueError("Document conversion failed - no result returned")

        if not hasattr(result, 'text_content'):
            logger.error("MarkItDown result missing text_content attribute")
            raise ValueError("Document conversion failed - no text content attribute")

        if not result.text_content or not result.text_content.strip():
            logger.error("MarkItDown returned empty content")
            raise ValueError("Document conversion resulted in empty content")

        logger.info("Word document text extraction successful")
        return result.text_content

    except Exception as e:
        logger.error(f"Failed to extract text from Word document: {str(e)}", exc_info=True)
        # Clean up any temporary files that might have been created
        try:
            temp_dir = os.path.join(os.path.dirname(file_path), '.markitdown_temp')
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up temporary files: {str(cleanup_error)}")
        raise

def extract_text_from_pdf(file_path):
    """Extract text content from a PDF file."""
    logger.debug(f"Attempting to extract text from PDF: {file_path}")
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"Cannot read PDF file: {file_path}")

        # Check file size
        check_file_size(file_path)

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

        # Verify file is not empty
        if os.path.getsize(file_path) == 0:
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
        # Clean up the file if there was an error
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up file {file_path} after error")
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up file: {str(cleanup_error)}")
        raise