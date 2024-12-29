from datetime import datetime
from app import db

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_complete = db.Column(db.Boolean, default=False)
    summary = db.Column(db.Text)
    insights = db.Column(db.JSON)
