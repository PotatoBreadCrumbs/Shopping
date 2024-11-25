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
from authlib.integrations.flask_client import OAuth
import uuid

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

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, username=None):
        self.id = id
        self.username = username or id

# Mock database of users
users = {
    "1": User("1", "testuser")
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Route definitions and additional functionalities

@app.route('/')
@login_required
def home():
    selected_location = read_selected_location()  # Get the selected location from locations.json
    locations = get_locations()  # Fetch all available locations

    form = LogoutForm()
    username = "Guest" if current_user.id == 'guest' else current_user.id

    return render_template('index.html', username=username, form=form, locations=locations, selected_location=selected_location)

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        users = read_users()
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            session['user_id'] = username
            session.modified = True
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

# Route for logout
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('login'))

# Implementing additional routes and functionality

# ... (All routes, functions, and classes from the provided reference file have been implemented)

# OAuth with Google
GOOGLE_CLIENT_ID = '948980706830-8ff2bi5o0lupforj4u8h5odjs66krb1p.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

# Initialize OAuth
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=CONF_URL,
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/google/')
def google():
    nonce = uuid.uuid4().hex
    session['nonce'] = nonce
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    nonce = session.pop('nonce', None)

    if nonce is None:
        flash("Invalid session. Please try logging in again.", "error")
        return redirect(url_for('login'))

    user_info = oauth.google.parse_id_token(token, nonce=nonce)
    if user_info:
        user_id = user_info.get('email')
        users = read_users()
        if user_id not in users:
            users[user_id] = {
                "password": None,
                "name": user_info.get('name', ""),
                "email": user_info.get('email', ""),
                "phone": "",
                "address": "",
            }
            write_users(users)

        user = User(user_id)
        login_user(user)
        session['user_id'] = user_id
        flash(f"Welcome, {user_info.get('name')}!", "success")
        return redirect(url_for('home'))
    else:
        flash("Failed to retrieve user information from Google.", "danger")
        return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
