from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSON

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_complete = db.Column(db.Boolean, default=False)
    summary = db.Column(db.Text)
    insights = db.Column(db.JSON)
    doc_metadata = db.Column(JSON)  # Renamed from metadata to doc_metadata
    processing_attempts = db.Column(db.Integer, default=1)  # Track conversion attempts
    processing_method = db.Column(db.String(50))  # Store which method succeeded

class ErrorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    error_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    stack_trace = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    error_metadata = db.Column(JSON)