from flask_user import UserMixin

# internal imports 
from app_and_db import db
from config import ConfigClass

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # User authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    is_enabled = db.Column(db.Boolean(), nullable=False, default=True)
    apikey = db.Column(db.String(100), nullable=False, index=True, server_default='')

    # Relationships
    roles = db.relationship('Role', secondary='user_roles', 
        backref=db.backref('users', lazy='dynamic'))

    def is_active(self):
        return self.is_enabled

# Define the Role data model
class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

# Define the UserRoles data model
class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

