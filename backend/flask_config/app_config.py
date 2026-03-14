# Flask app configuration for database
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/your_database_name'  # Replace with your actual credentials
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Ensure you have pymysql installed: pip install pymysql flask-sqlalchemy