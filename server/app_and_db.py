
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from elasticsearch import Elasticsearch
from flask_user import UserManager, SQLAlchemyAdapter

# internal imports
from config import ConfigClass

app = Flask(__name__)

app.config.from_object(ConfigClass) 			# load config

db = SQLAlchemy(app)

es = Elasticsearch(ConfigClass.es_nodes)

from users.model import User

db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model

user_manager = UserManager(db_adapter, app)     # Initialize Flask-User

