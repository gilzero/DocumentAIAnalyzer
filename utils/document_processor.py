import os
import logging
import docx
import PyPDF2
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx'}

def extract_text_from_pdf(file_path):
    logger.debug(f"Attempting to extract text from PDF: {file_path}")
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                logger.debug(f"Processing page {page_num + 1}")
                text += page.extract_text()
        logger.debug("PDF text extraction successful")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {str(e)}")
        raise

def extract_text_from_docx(file_path):
    logger.debug(f"Attempting to extract text from DOCX: {file_path}")
    try:
        doc = docx.Document(file_path)
        text = []
        for para_num, paragraph in enumerate(doc.paragraphs):
            logger.debug(f"Processing paragraph {para_num + 1}")
            text.append(paragraph.text)
        logger.debug("DOCX text extraction successful")
        return '\n'.join(text)
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX: {str(e)}")
        raise

def process_document(file_path):
    """
    Process a document file and extract its text content
    """
    logger.debug(f"Starting document processing for: {file_path}")
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_extension = os.path.splitext(file_path)[1].lower()
        logger.debug(f"Detected file extension: {file_extension}")

        if file_extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension in ['.doc', '.docx']:
            return extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    except Exception as e:
        logger.error(f"Error in process_document: {str(e)}")
        raise