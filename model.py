# models.py
from datetime import datetime
from db import db

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(20), nullable=False)  # 'user' | 'bot'
    text = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(50), nullable=True)   # 'gemini' | 'rules' | 'fallback'
    meta = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "text": self.text,
            "source": self.source,
            "meta": self.meta,
            "created_at": self.created_at.isoformat()
        }
class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    salary = db.Column(db.Float, nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "designation": self.designation,
            "salary": self.salary,
            "joined_at": self.joined_at.isoformat()
        }

    
