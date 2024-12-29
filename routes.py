import os
import logging
from flask import render_template, request, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Document
from utils.document_processor import process_document, allowed_file
from utils.ai_analyzer import analyze_document

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        app.logger.debug(f"File saved at: {file_path}")

        try:
            # Extract text from document
            text_content = process_document(file_path)
            app.logger.debug("Text extracted successfully")

            # Analyze content with AI
            analysis_results = analyze_document(text_content)
            app.logger.debug("AI analysis completed")

            # Save to database
            document = Document(
                filename=filename,
                original_filename=file.filename,
                file_type=filename.rsplit('.', 1)[1].lower(),
                analysis_complete=True,
                summary=analysis_results.get('summary', ''),
                insights=analysis_results
            )
            db.session.add(document)
            db.session.commit()

            # Clean up uploaded file
            os.remove(file_path)

            return jsonify({
                'summary': analysis_results.get('summary', ''),
                'insights': analysis_results.get('key_points', []),
                'topics': analysis_results.get('main_topics', []),
                'entities': analysis_results.get('important_entities', [])
            })

        except Exception as e:
            app.logger.error(f"Error processing document content: {str(e)}")
            # Clean up the file if there was an error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

    except Exception as e:
        app.logger.error(f"Error processing document: {str(e)}")
        return jsonify({'error': 'Error processing document'}), 500