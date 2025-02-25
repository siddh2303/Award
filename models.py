from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    role = db.Column(db.String(50), nullable=False)  # 'admin' or 'employee'
    gid = db.Column(db.String(6), nullable=False)
    access_level = db.Column(db.String(20), nullable=False, default='view_only')
    
    
class Category(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=1)

class QuarterlyAward(db.Model):
    __tablename__ = 'quarterly_awards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

class AnnuallyAward(db.Model):
    __tablename__ = 'annually_awards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

class Nomination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    nominee_name = db.Column(db.String(150), nullable=False)
    nominee_global_id = db.Column(db.String(100), nullable=False)
    nominee_email = db.Column(db.String(150), nullable=False)
    nominated_by_name = db.Column(db.String(150), nullable=False)
    nominated_by_global_id = db.Column(db.String(100), nullable=False)
    nominated_by_email = db.Column(db.String(150), nullable=False)
    comments = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='In-progress')  # In-progress, Submitted, Rejected, Send-Back
    submission_date = db.Column(db.DateTime, default=datetime.now())
    award_name = db.Column(db.String(150), nullable=False)
    
