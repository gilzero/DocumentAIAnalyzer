import os
import logging
import json
from datetime import datetime
from flask import render_template, request, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Document, ErrorLog
from utils.document_processor import process_document, allowed_file, check_file_size

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/error-dashboard')
def error_dashboard():
    return render_template('error_dashboard.html')

@app.route('/api/errors')
def get_errors():
    errors = ErrorLog.query.order_by(ErrorLog.timestamp.desc()).limit(100).all()
    return jsonify([{
        'id': error.id,
        'error_type': error.error_type,
        'message': error.message,
        'stack_trace': error.stack_trace,
        'timestamp': error.timestamp.isoformat(),
        'metadata': error.error_metadata
    } for error in errors])

def log_error(error_type, message, stack_trace=None, metadata=None):
    """Log error to database and console."""
    try:
        error_log = ErrorLog(
            error_type=error_type,
            message=str(message),
            stack_trace=stack_trace,
            error_metadata=metadata or {}
        )
        db.session.add(error_log)
        db.session.commit()
        logger.error(f"Error logged: {error_type} - {message}")
    except Exception as e:
        logger.error(f"Failed to log error to database: {str(e)}")

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle document upload and processing."""
    try:
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({
                'error': 'No file provided',
                'details': {'request_files': list(request.files.keys())}
            }), 400

        file = request.files['file']

        # Validate filename
        if not file.filename:
            logger.warning("No selected file")
            return jsonify({'error': 'No selected file'}), 400

        if '.' not in file.filename:
            error_msg = "Invalid filename structure"
            log_error("ValidationError", error_msg, metadata={'filename': file.filename})
            return jsonify({
                'error': error_msg,
                'details': {'filename': file.filename}
            }), 400

        if not allowed_file(file.filename):
            error_msg = "Invalid file type. Please upload a PDF or Word document"
            log_error("ValidationError", error_msg, metadata={'filename': file.filename})
            return jsonify({
                'error': error_msg,
                'details': {'filename': file.filename}
            }), 400

        try:
            # Save and process file
            original_filename = file.filename
            file_extension = os.path.splitext(original_filename)[1].lower()
            secure_base = secure_filename(os.path.splitext(original_filename)[0])

            if not secure_base:
                error_msg = "Invalid filename characters"
                log_error("ValidationError", error_msg, metadata={'original_filename': original_filename})
                return jsonify({
                    'error': error_msg,
                    'details': {'original_filename': original_filename}
                }), 400

            filename = f"{secure_base}{file_extension}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Ensure upload directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            logger.debug(f"Attempting to save file at: {file_path}")
            file.save(file_path)
            logger.info(f"File saved successfully at: {file_path}")

            try:
                # Process document and extract text/metadata
                text_content, metadata = process_document(file_path)
                logger.info(f"Document processed successfully with metadata: {metadata}")

                # Analyze content with AI
                from utils.ai_analyzer import analyze_document
                logger.debug("Starting AI analysis")
                analysis_results = analyze_document(text_content)
                logger.info("AI analysis completed successfully")

                # Save to database with metadata
                document = Document(
                    filename=filename,
                    original_filename=original_filename,
                    file_type=file_extension[1:],
                    analysis_complete=True,
                    summary=analysis_results.get('summary', ''),
                    insights=analysis_results,
                    doc_metadata=metadata,
                    processing_method='markitdown' if 'markdown_content' in metadata else 'python-docx'
                )
                db.session.add(document)
                db.session.commit()
                logger.info(f"Document {filename} saved to database with metadata")

                # Clean up uploaded file
                os.remove(file_path)
                logger.debug(f"Temporary file {file_path} removed")

                return jsonify({
                    'success': True,
                    'document_type': analysis_results.get('document_type', 'Unknown'),
                    'structure': analysis_results.get('structure', []),
                    'type_confidence': analysis_results.get('type_confidence', 0),
                    'summary': analysis_results.get('summary', ''),
                    'insights': analysis_results.get('key_points', []),
                    'topics': analysis_results.get('main_topics', []),
                    'entities': analysis_results.get('important_entities', []),
                    'metadata': metadata
                })

            except Exception as e:
                error_msg = f"Error processing document content: {str(e)}"
                log_error(
                    "ProcessingError",
                    error_msg,
                    stack_trace=str(e.__traceback__),
                    metadata={
                        'file_type': file_extension,
                        'filename': filename,
                        'original_filename': original_filename,
                        'error_type': type(e).__name__
                    }
                )
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({
                    'error': str(e),
                    'message': 'Failed to process document content',
                    'details': {
                        'file_type': file_extension,
                        'filename': filename,
                        'original_filename': original_filename,
                        'error_type': type(e).__name__
                    }
                }), 500

        except Exception as e:
            error_msg = f"Error handling upload: {str(e)}"
            log_error(
                "UploadError",
                error_msg,
                stack_trace=str(e.__traceback__),
                metadata={'original_filename': file.filename}
            )
            return jsonify({
                'error': str(e),
                'message': 'Error uploading document',
                'details': {
                    'original_filename': file.filename,
                    'error_type': type(e).__name__
                }
            }), 500

    except Exception as e:
        error_msg = f"Unexpected error in upload route: {str(e)}"
        log_error(
            "UnexpectedError",
            error_msg,
            stack_trace=str(e.__traceback__),
            metadata={'error_type': type(e).__name__}
        )
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'details': {
                'error_type': type(e).__name__
            }
        }), 500