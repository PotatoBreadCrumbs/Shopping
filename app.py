
# Import necessary libraries
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import requests
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import json
import os
from flask_session import Session  # Added for server-side session storage
import redis  # Added for Redis support

# First we are going to initialize the Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
csrf = CSRFProtect(app)  # Enable CSRF protection

# Configure Flask-Mail using environment variables
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Redis and Flask-Session configuration
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'app-session:'
app.config['SESSION_REDIS'] = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# Initialize server-side session handling
Session(app)

# Add other app routes and functionalities below this line

# Example route
@app.route('/')
def home():
    return "Welcome to the Flask App with Redis Sessions!"

if __name__ == "__main__":
    app.run(debug=True)
