from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    role = db.Column(db.String(50), nullable=False) 
    gid = db.Column(db.String(6), nullable=False)
    user_roles = db.relationship('UserRole', back_populates='user')
    
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    user_roles = db.relationship('UserRole', back_populates='role',foreign_keys='UserRole.role_id')
    
    
class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    name = db.Column(db.String(20), db.ForeignKey('role.name'), nullable=False)
    user = db.relationship('User', back_populates='user_roles')
    role = db.relationship('Role', back_populates='user_roles', foreign_keys=[role_id])   

class Category(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=1)
    extension_days = db.Column(db.Integer, default=0, nullable=False)

    def update_status(self):
        extended_end_date = self.end_date + timedelta(days=self.extension_days)
        if extended_end_date < datetime.utcnow():
            self.status = 0
            
    def is_deadline_extended(self):
        if self.extension_days is None:
            self.extension_days = 0
        return self.end_date + timedelta(days=self.extension_days) > datetime.utcnow()

class QuarterlyAward(db.Model):
    __tablename__ = 'quarterly_awards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class AnnuallyAward(db.Model):
    __tablename__ = 'annually_awards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

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
    status = db.Column(db.String(50), nullable=False, default='In-progress')
    submission_date = db.Column(db.DateTime, default=datetime.now())
    award_name = db.Column(db.String(150), nullable=False)
    team_member_name = db.Column(db.String(100), nullable=False)
    category = db.relationship('Category', backref='nominations')
    

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gid = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    
