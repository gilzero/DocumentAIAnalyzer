import os
import logging
from flask import render_template, request, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Document
from utils.document_processor import process_document, allowed_file, check_file_size

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle document upload and processing."""
    try:
        # Validate request has file
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
            logger.error("Invalid filename structure")
            return jsonify({
                'error': 'Invalid filename structure',
                'details': {'filename': file.filename}
            }), 400

        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({
                'error': 'Invalid file type. Please upload a PDF or Word document',
                'details': {'filename': file.filename}
            }), 400

        try:
            # Secure and validate filename
            original_filename = file.filename
            file_extension = os.path.splitext(original_filename)[1].lower()

            # Create secure filename
            secure_base = secure_filename(os.path.splitext(original_filename)[0])
            if not secure_base:
                logger.error("Could not create secure filename from: " + original_filename)
                return jsonify({
                    'error': 'Invalid filename characters',
                    'details': {'original_filename': original_filename}
                }), 400

            filename = f"{secure_base}{file_extension}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Ensure upload directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            logger.debug(f"Attempting to save file at: {file_path}")
            file.save(file_path)
            logger.info(f"File saved successfully at: {file_path}")

            # Verify file size
            try:
                check_file_size(file_path)
            except ValueError as e:
                os.remove(file_path)
                return jsonify({
                    'error': str(e),
                    'details': {'filename': filename}
                }), 400

            try:
                # Extract text from document
                logger.debug(f"Starting document processing for {filename}")
                text_content = process_document(file_path)
                logger.info(f"Text extracted successfully from {filename}")

                # Analyze content with AI
                from utils.ai_analyzer import analyze_document
                logger.debug("Starting AI analysis")
                analysis_results = analyze_document(text_content)
                logger.info("AI analysis completed successfully")

                # Save to database
                document = Document(
                    filename=filename,
                    original_filename=original_filename,
                    file_type=file_extension[1:],  # Remove the leading dot
                    analysis_complete=True,
                    summary=analysis_results.get('summary', ''),
                    insights=analysis_results
                )
                db.session.add(document)
                db.session.commit()
                logger.info(f"Document {filename} saved to database")

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
                    'entities': analysis_results.get('important_entities', [])
                })

            except Exception as e:
                logger.error(f"Error processing document content: {str(e)}", exc_info=True)
                # Clean up the file if there was an error
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up file {file_path} after error")
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
            logger.error(f"Error handling upload: {str(e)}", exc_info=True)
            return jsonify({
                'error': str(e),
                'message': 'Error uploading document',
                'details': {
                    'original_filename': file.filename,
                    'error_type': type(e).__name__
                }
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error in upload route: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'details': {
                'error_type': type(e).__name__
            }
        }), 500