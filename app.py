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
import re

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
redis_url = os.getenv('AH_REDIS_STACKHERO_RED_URL_TLS')
if not redis_url:
    raise ValueError("Redis URL not found. Make sure AH_REDIS_STACKHERO_RED_URL_TLS is set in your environment variables.")
app.config['SESSION_REDIS'] = redis.from_url(redis_url)


# Initialize server-side session handling
Session(app)

# Add other app routes and functionalities below this line

from dotenv import load_dotenv

load_dotenv()
def send_postmark_forgot_password(to_email, reset_url):

    api_key = os.getenv("POSTMARK_API_KEY")
    headers = {
        "X-Postmark-Server-Token": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "From": "kgawrinauth1@pride.hofstra.edu",  # Replace with your Postmark verified sender
        "To": to_email,
        "TemplateId": 38145706,  # Replace with your Postmark Template ID for forgot password
        "TemplateModel": {
            "reset_url": reset_url,  # Dynamic variable in your Postmark template
            "support_email": "support@example.com",  # Example additional variable
            "product_name": "GreenGrocer App"  # Example additional variable
        }
    }
    try:
        response = requests.post(
            "https://api.postmarkapp.com/email/withTemplate", headers=headers, json=data
        )
        if response.status_code == 200:
            print("Password reset email sent successfully.")
        else:
            print(f"Failed to send email: {response.text}")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_postmark_order_confirmation(to_email, name, order_details):
    

    api_key = os.getenv("POSTMARK_API_KEY")
    headers = {
        "X-Postmark-Server-Token": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "From": "kgawrinauth1@pride.hofstra.edu",  # Replace with your Postmark verified sender
        "To": to_email,
        "TemplateId": 38149527,  # Replace with your Postmark Template ID for order confirmation
        "TemplateModel": {
            "customer_name": name,  # Dynamic variable for customer name
            "order_details": "".join(
                f"<li>{item['quantity']}x {item['name']} at ${item['price']} each</li>"
                for item in order_details
            ),
            "total_price": sum(item['price'] * item['quantity'] for item in order_details),
            "company_name": "GreenGrocer Team",
            "support_email": "support@example.com"  # Example additional variable
        }
    }
    try:
        response = requests.post(
            "https://api.postmarkapp.com/email/withTemplate", headers=headers, json=data
        )
        if response.status_code == 200:
            print("Order confirmation email sent successfully.")
        else:
            print(f"Failed to send email: {response.text}")
    except Exception as e:
        print(f"Error sending email: {e}") 

#good from here onwards, testing sg above now
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_page():
    if request.method == 'POST':
        # Parse JSON data from the request
        data = request.get_json()  # Fixed: Get JSON payload
        email = data.get('email')
        new_password = data.get('new_password')

        # Load user data
        users = read_users()
        user_found = False

        # Check if email exists and update password
        for key, user_info in users.items():
            if key == email or user_info.get('email') == email:
                # Update the password
                if key == email:
                    users[key]['password'] = new_password
                else:
                    user_info['password'] = new_password
                user_found = True
                break
        
        if user_found:
            write_users(users)  # Save changes
            return jsonify({"message": "Password updated successfully!", "redirect_url": url_for('login')})
        else:
            return jsonify({"message": "Email not found. Please check and try again."}),  # Not found

    return render_template('reset_password_updated.html')
    
# We created a file to store user data (this simulates a database using mysql lite) x
USER_FILE = 'user_storage.json'

# Our Kroger API credentials 
client_id = 'kevingawrinauth-b1629c2310698a009e85d726fbc0e9aa8264849196508842534'
client_secret = 'fpfEnrPkQnQcWGySAoig8G6Up1ZosRbV8u0LrKSd'

def load_user_storage():
    try:
        # Load and return the user data from user_Storage.json
        with open("user_storage.json", "r") as f:
            users = json.load(f)
            print("Users loaded successfully:", users)  # Debugging line
            return users
    except FileNotFoundError:
        print("Error: user_storage.json file not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: user_storage.json is not a valid JSON file.")
        return {}

@app.context_processor
def inject_username():
    user_id = session.get("user_id")
    if user_id:
        users = load_user_storage()  # Load users from JSON file
        user = users.get(user_id)
        if user:
            return {"username": user.get("name", user_id)}
    return {"username": "Guest"}


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
def get_kroger_token(client_id, client_secret):
    token_url = "https://api.kroger.com/v1/connect/oauth2/token"
    data = {
        'grant_type': 'client_credentials',
        'scope': 'product.compact'
    }
    auth = (client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(token_url, headers=headers, data=data, auth=auth)

    # Log full response for debugging
    print("Token Response Status Code:", response.status_code)
    print("Token Response Text:", response.text)

    # Check for JSON format response
    if response.status_code == 200:
        try:
            return response.json().get('access_token')
        except ValueError:
            # In case JSON decoding fails
            raise Exception("Error decoding JSON response while fetching access token.")
    else:
        # Handle error case explicitly
        raise Exception("Error fetching access token: Response Code " + str(response.status_code) + ", Response Text: " + response.text)

@app.route('/locations')
def fetch_locations():
    # Get access token
    access_token = get_kroger_token(client_id, client_secret)
    location_url = "https://api.kroger.com/v1/locations"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    params = {
        'filter.radiusInMiles': 50,  # Adjusted radius
        'filter.limit': 250          # Limit to 250 locations
    }
    # Make the API call
    response = requests.get(location_url, headers=headers, params=params)
    
    # Logging response for debugging
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)

    # Check and parse response
    if response.status_code == 200:
        locations = response.json().get('data', [])
        return render_template('index.html', locations=locations)
    else:
        flash("Error fetching locations.", "danger")
        return redirect(url_for('home'))

# Disable CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False
# implemented a helper functions to manage user data in a file
def read_users(source='regular'):
    file_path = 'google_accounts.json' if source == 'google' else USER_FILE
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(f"Error: {file_path} contains invalid JSON.")
        return {}

def read_user(username):
    users = read_users()
    return users.get(username)

def write_users(users, source='regular'):


    file_path = 'google_accounts.json' if source == 'google' else USER_FILE

#Initialize the existing_users as empty
    existing_users = {}

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                # Read existing user data
                existing_users = json.load(file)
                if not isinstance(existing_users, dict):
                    raise ValueError("Invalid JSON format: Expected a dictionary.")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: {file_path} contains invalid JSON or is not a dictionary. Overwriting. Error: {e}")
            existing_users = {}  # Reset to empty if invalid

#Update existing users with the new user data
    if not isinstance(users, dict):
        raise ValueError("The 'users' parameter must be a dictionary.")
    existing_users.update(users)

    try:
        with open(file_path, 'w') as file:
            # Write updated data back to the file
            json.dump(existing_users, file, indent=4)
        print(f"Successfully updated {file_path}")
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# now we will configure the user using Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Now we will try to create the Form class for login and registration
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

# Form for the logout button 
class LogoutForm(FlaskForm):
    submit = SubmitField('Sign Out')
    
@app.route('/update_user', methods=['POST'])
@login_required
def update_user():
    # Get user ID
    user_id = current_user.id

#Read all users
    users = read_users()
    user_data = users.get(user_id, {})

#Update user data with form data
    user_data['name'] = request.form.get('name', '').strip()
    user_data['email'] = request.form.get('email', '').strip()
    user_data['phone'] = request.form.get('phone', '').strip()
    user_data['address'] = request.form.get('address', '').strip()

#Write updated data back to storage
    users[user_id] = user_data
    write_users(users)

#Flash success message and redirect back to account_info
    flash('Account information updated successfully.', 'success')
    return redirect(url_for('account_info'))


@app.route('/order_history')
@login_required
def order_history():
    user_id = session.get("user_id")
    user_data = read_user(user_id)

    # Fetch order history or initialize an empty list if not found
    order_history = user_data.get("order_history", []) if isinstance(user_data, dict) else []

    return render_template('orderhistory.html', order_history=order_history)



@app.route('/settings')
@login_required
def settings():
    users = read_users()
    user_data = users.get(current_user.id, {})
    return render_template('settings.html', user_data=user_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # implementing the login form to be displaed
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        users = read_users()  # allow us to read the users from the file saved from mysql lite
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            cart_data = read_cart(username)
            session['user_id'] = username  # Store user ID in session
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart_data['cart_items'])  # Calculate total quantity
            session.modified = True 
            return jsonify({"message": "Right", "redirect_url": url_for('home')})
        
            #return redirect(url_for('home'))  # redirect to home after login
        else:
           return jsonify({"message": "Wrong"})
    return render_template('login.html', form=form)
@app.route('/save_for_later/<int:index>', methods=['POST'])
@login_required
def save_for_later(index):
    username = session.get('user_id')

    if username:
        # Retrieve the user's data (cart_items and saved_items) from JSON
        user_data = read_cart(username)
        cart = user_data.get('cart_items', [])
        saved_items = user_data.get('saved_items', [])

        # Ensure index is valid before moving the item
        if 0 <= index < len(cart):
            item = cart.pop(index)  # Remove the item from cart
            saved_items.append(item)  # Add it to saved items

            # Update the user's data in the JSON file
            write_cart(username, {'cart_items': cart, 'saved_items': saved_items})

            # Recalculate cart counter based on remaining items in the cart
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart)
            session.modified = True  # Mark session as modified

            flash("Item saved for later.", "info")
        else:
            flash("Item not found in cart.", "danger")
    else:
        flash("User not logged in.", "danger")

    return redirect(url_for('view_cart'))

@app.route('/move_to_cart/<int:index>', methods=['POST'])
@login_required
def move_to_cart(index):
    user_id = session.get("user_id")
    user_data = read_cart(user_id)
    cart = user_data.get('cart_items', [])
    saved_items = user_data.get('saved_items', [])
    if 0 <= index < len(saved_items):
        item = saved_items.pop(index)
        cart.append(item)
        write_cart(user_id, {"cart_items": cart, "saved_items": saved_items})
        session['cart_count'] = sum(item['quantity'] for item in cart)
        flash("Item moved back to cart.", "success")
    return redirect(url_for('view_cart'))


# our guest login route
@app.route('/guest_login')
def guest_login():
    # automatically log in as a guest
    guest_user = User('guest')
    login_user(guest_user)
    return redirect(url_for('home'))  # should allow us redirect to home after guest login


@app.route('/api/product/<product_id>', methods=['GET'])
def get_product(product_id):
    access_token = get_kroger_token(client_id, client_secret)
    search_url = f"https://api.kroger.com/v1/products/{product_id}"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        product = response.json().get('data')
        if product:
            return jsonify(product)
    return jsonify({"error": "Product not found"}), 404

FAVORITES_FILE = "favorites.json"

def read_favorites(user_id):
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, 'r') as file:
            try:
                favorites = json.load(file)
                return favorites.get(user_id, [])  # Return favorites for the specific user
            except json.JSONDecodeError:
                print("Error reading favorites file: malformed JSON.")
                return []
    return []

def write_favorites(user_id, user_favorites):
    favorites = {}
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, 'r') as file:
            try:
                favorites = json.load(file)
            except json.JSONDecodeError:
                print("Error reading favorites file. Overwriting with new data.")

    favorites[user_id] = user_favorites  # Update the user's favorites
    with open(FAVORITES_FILE, 'w') as file:
        json.dump(favorites, file, indent=4)


@app.route('/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Unauthorized access", "status": "error"}), 401

    data = request.get_json()
    required_fields = ['name', 'price', 'image_url']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"message": f"Missing field: {field}", "status": "error"}), 400

    favorites = read_favorites(user_id)
    item_exists = any(fav['name'] == data['name'] for fav in favorites)

    if item_exists:
        favorites = [fav for fav in favorites if fav['name'] != data['name']]  # Remove favorite
        status = "removed"
    else:
        favorites.append({
            'name': data['name'],
            'price': data['price'],
            'image_url': data['image_url']
        })  # Add favorite
        status = "added"

    write_favorites(user_id, favorites)
    return jsonify({"message": f"Favorite {status} successfully", "status": status})


 

@app.route('/get_favorites', methods=['GET'])
@login_required
def get_favorites():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Unauthorized access", "status": "error"}), 401

    favorites = read_favorites(user_id)
    return jsonify(favorites)

# the route for our user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  #  registration form
    if form.validate_on_submit():
        new_username = form.username.data
        new_password = form.password.data
        users = read_users()  # reads users from the file saved in db 
        if (len(new_username) < 5 or len(new_username) > 20):
            flash(message=Markup("Username must be at least 5 characters."))
        if new_username in users: 
            flash(message = Markup("Username already exists, please choose another."))
        else:
            users[new_username] = {'password': new_password}
            write_users(users)  # saves new user to the file
            flash('User registered successfully! Please log in.',category="success")
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/validate', methods=['POST'])
def validate():
    # Access form data from JavaScript
    data = request.get_json()  # Read JSON payload
    username = data.get('username')
    password = data.get('password')
    users = read_users()
    # Perform validation (this is a basic example)
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters long."})
    if not any(char.isupper() for char in password):
        return jsonify({"message": "Password must contain an uppercase letter."})
    if not any(char.isdigit() for char in password):
        return jsonify({"message": "Password must contain a number."})
    if not any(char.islower() for char in password):
        return jsonify({"message": "Password must contain a lowercase letter."})
    special_char_pattern = r'[!@#$%^&*()\-_=+{}\[\]|\\:;"\'<>,.?/~`]'
    
    # Check if password contains at least one special character
    if not re.search(special_char_pattern, password):
        return jsonify({"message": "Password must contain at least one special character (@$!%*?&_-)"})
    # If all checks pass
    if username in users:
        return jsonify({"message": "Already an existing user"})
    users[username] = {'password': password}
    write_users(users)  # saves new user to the file
    return jsonify({"message": "Valid"})

@app.route('/validate_checkout', methods=['POST'])
def validate_checkout():
    user_id = session.get("user_id")
    cart = []

    if user_id:
        # Retrieve cart data for the logged-in user
        user_data = read_cart(user_id)
        cart = user_data.get('cart_items', [])
    else:
        # Retrieve cart data for the guest user
        cart = session.get('guest_cart', [])

    if not cart or len(cart) == 0:
        return jsonify({"message": "Empty"})  # Return error if cart is empty

    return jsonify({"message": "Proceed", "redirect_url": url_for('checkout')})


@app.route('/check_username')
def check_username():
    username = request.args.get('username')
    users = read_users()  # Assuming this reads all registered users from your database or file
    
    # Check if the username already exists
    is_taken = username in users

    return jsonify({'is_taken': is_taken})

@app.route('/forgot-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        # Get the email entered in the form
        email = request.form.get('email')
        print(f"Email entered for reset: {email}")

        # Load the users and search for the email in the JSON structure
        users = read_users()
        user_found = False
        for username, user_data in users.items():
            if user_data.get('email') == email:
                user_found = True
                
                # Set the reset URL
                reset_url = f"https://www.the-greengrocer.com/reset-password?email={email}"
                
                # Send the password reset email
                try:
                    send_postmark_forgot_password(email, reset_url)
                    flash('Password reset instructions have been sent to your email.', 'info')
                except Exception as e:
                    print(f"Error sending email: {str(e)}")
                    flash('An error occurred while sending the email. Please try again later.', 'danger')
                
                return jsonify({"message": "Valid", "redirect_url": url_for('login')})
                
        if not user_found:
            return jsonify({"message": "Invalid"})

        # Redirect to the login page or another confirmation page
        return redirect(url_for('login'))

    # Render the forgot password page for GET requests
    return render_template('forgot_password.html')   
@app.route('/')
def home():
    selected_location = read_selected_location()  # Get the selected location from locations.json
    locations = get_locations()  # Fetch all available locations

    form = LogoutForm()
    username = "Guest" if not current_user.is_authenticated else current_user.id

    # Pass selected_location to the index.html template
    return render_template('index.html', username=username, form=form, locations=locations, selected_location=selected_location)

@app.route('/favorites')
def view_favorites():
    user_id = session.get("user_id")  # Get the logged-in user's ID from the session
    if not user_id:
        flash("Please log in to view your favorites.", "danger")
        return redirect(url_for("login"))

    favorites = read_favorites(user_id)  # Pass the user_id to read_favorites
    return render_template('favorites.html', favorites=favorites)
def get_locations():
    access_token = get_kroger_token(client_id, client_secret)
    location_url = "https://api.kroger.com/v1/locations"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    params = {'filter.radiusInMiles': 50}
    response = requests.get(location_url, headers=headers, params=params)
    return response.json().get('data', []) if response.status_code == 200 else []

import os
import json

LOCATION_FILE = 'locations.json'

def read_selected_location():
    if not os.path.exists(LOCATION_FILE):
        return None
    with open(LOCATION_FILE, 'r') as file:
        data = json.load(file)
    return data.get('selected_location', None)

def write_selected_location(location_id):
    with open(LOCATION_FILE, 'w') as file:
        json.dump({'selected_location': location_id}, file)
import json
import os

CART_FILE = "cart.json"
import os
import json

CART_FILE = 'cart.json'  # File to store cart data

def read_cart(user_id):
    """Read cart and saved items for a specific user."""
    if os.path.exists(CART_FILE):
        with open(CART_FILE, 'r') as file:
            try:
                data = json.load(file)  # Load all cart data
                user_cart = data.get(user_id, {})  # Get cart for specific user
                return {
                    'cart_items': user_cart.get('cart_items', []),  # Ensure cart_items is a list
                    'saved_items': user_cart.get('saved_items', [])  # Ensure saved_items is a list
                }
            except json.JSONDecodeError:
                print("Error decoding JSON from cart file.")
    # Return empty structure if file doesn't exist or user has no cart
    return {'cart_items': [], 'saved_items': []}

def write_cart(user_id, cart):
    """Write cart and saved items for a specific user."""
    data = {}
    # Load existing cart data if the file exists
    if os.path.exists(CART_FILE):
        with open(CART_FILE, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                print("Error decoding JSON. Overwriting file.")
    # Update the user's cart
    data[user_id] = cart
    # Save the updated data back to the file
    with open(CART_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def get_user_cart(username):
    """Retrieve the cart for a specific user from the JSON data."""
    cart_data = read_cart(username)  # Pass `username` to read_cart to get specific user's data
    return cart_data

def add_item_to_cart(username, item):
    """Add an item to the user's cart in the JSON data."""
    cart_data = read_cart()
    user_cart = cart_data.get(username, [])

    # Check if item is already in the cart; update quantity if so
    for existing_item in user_cart:
        if existing_item['name'] == item['name']:
            existing_item['quantity'] += item['quantity']
            break
    else:
        # If not found, add new item
        user_cart.append(item)

    # Save updated cart data
    cart_data[username] = user_cart
    write_cart(cart_data)

def remove_item_from_cart(username, item_name):
    """Remove an item from the user's cart in the JSON data."""
    cart_data = read_cart(username)  # Retrieve the user's specific cart directly from cart.json
    
    # Ensure we have a valid dictionary and user cart exists
    if isinstance(cart_data, dict):
        user_cart = cart_data.get(username, [])

        # Filter out the item to remove
        user_cart = [item for item in user_cart if item['name'] != item_name]
        
        # Update the user's cart in the overall cart data and save to cart.json
        cart_data[username] = user_cart
        write_cart(username, user_cart)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    user_id = session.get("user_id")

    # Check the request content type
    if request.content_type == 'application/json':
        # Retrieve product details from a JSON request
        data = request.get_json()
        product_name = data.get('product_name')
        product_price = data.get('product_price')
        product_image = data.get('product_image')
        product_quantity = data.get('product_quantity', 1)
        category = data.get('category')  # This may be missing for items added from favorites
    else:
        # Retrieve product details from a form submission
        product_name = request.form.get('product_name')
        product_price = request.form.get('product_price')
        product_image = request.form.get('product_image')
        product_quantity = request.form.get('product_quantity', 1)
        category = request.form.get('category')  # This may be missing for items added from favorites

    # Validate inputs
    if not product_name or product_price is None or not product_image:
        return jsonify({"message": "Invalid product data"}), 400

    # Convert price and quantity to appropriate types
    try:
        product_price = float(product_price)
        product_quantity = int(product_quantity)
    except ValueError:
        return jsonify({"message": "Invalid price or quantity"}), 400

    if user_id:
        # Add to the user's cart
        cart_data = read_cart(user_id)
        cart = cart_data.get('cart_items', [])

        # Check if the item already exists in the cart
        item_exists = next((item for item in cart if item['name'] == product_name), None)
        if item_exists:
            item_exists['quantity'] += product_quantity
        else:
            cart.append({
                'name': product_name,
                'price': product_price,
                'image': product_image,
                'quantity': product_quantity
            })

        # Save the updated cart
        write_cart(user_id, {'cart_items': cart, 'saved_items': cart_data.get('saved_items', [])})
        session['cart_count'] = sum(item['quantity'] for item in cart)
        session.modified = True
    else:
        # Handle guest cart
        if 'guest_cart' not in session:
            session['guest_cart'] = []

        cart = session['guest_cart']
        item_exists = next((item for item in cart if item['name'] == product_name), None)
        if item_exists:
            item_exists['quantity'] += product_quantity
        else:
            cart.append({
                'name': product_name,
                'price': product_price,
                'image': product_image,
                'quantity': product_quantity
            })

        session['cart_count'] = sum(item['quantity'] for item in cart)
        session.modified = True

    # If category is provided, redirect to the products page; otherwise, return JSON
    if category:
        return redirect(url_for('get_products', category=category))
    else:
        return jsonify({"message": f"{product_name} added to cart", "cart_count": session['cart_count']}), 200

from urllib.parse import unquote

@app.route('/remove_item/<int:index>', methods=['POST'])
def remove_item(index):
    user_id = session.get('user_id')  # Get the user_id from the session

    if user_id:
        # Retrieve the user's cart data (cart_items)
        user_cart_data = read_cart(user_id)
        cart_items = user_cart_data.get('cart_items', [])

        # Validate index range
        if 0 <= index < len(cart_items):
            cart_items.pop(index)  # Remove the item
            user_cart_data['cart_items'] = cart_items
            write_cart(user_id, user_cart_data)

            # Update session cart count
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart_items)
            session.modified = True
            flash("Item removed from cart.", "success")
        else:
            flash("Invalid item index. Please try again.", "danger")
    else:
        # Handle guest cart
        cart = session.get('guest_cart', [])

        # Validate index range
        if 0 <= index < len(cart):
            cart.pop(index)  # Remove the item
            session['guest_cart'] = cart
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart)
            session.modified = True
            flash("Item removed from cart.", "success")
        else:
            flash("Invalid item index. Please try again.", "danger")

    return redirect(url_for('view_cart'))


@app.route('/update_quantity/<int:index>/<operation>', methods=['POST'])
def update_quantity(index, operation):
    user_id = session.get('user_id')  # Get the user_id from the session

    if user_id:
        # Retrieve the user's cart data from JSON
        user_cart_data = read_cart(user_id)
        cart_items = user_cart_data.get('cart_items', [])

        # Ensure the index is within bounds
        if 0 <= index < len(cart_items):
            item = cart_items[index]  # Access the specific cart item

            # Handle quantity updates based on the operation
            if operation == 'increase':
                item['quantity'] += 1  # Increment the quantity
            elif operation == 'decrease' and item['quantity'] > 1:
                item['quantity'] -= 1  # Decrement the quantity only if > 1

            # Update the user's cart data in JSON
            user_cart_data['cart_items'] = cart_items
            write_cart(user_id, user_cart_data)

            # Recalculate the total cart count for the session
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart_items)
            session.modified = True
            flash("Item quantity updated successfully.", "success")
        else:
            flash("Invalid item index. Please try again.", "danger")
    else:
        # Handle guest cart
        cart = session.get('guest_cart', [])

        # Ensure the index is within bounds
        if 0 <= index < len(cart):
            item = cart[index]

            # Handle quantity updates for guest cart
            if operation == 'increase':
                item['quantity'] += 1
            elif operation == 'decrease' and item['quantity'] > 1:
                item['quantity'] -= 1

            # Update session cart
            session['guest_cart'] = cart
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart)
            session.modified = True
            flash("Item quantity updated successfully.", "success")
        else:
            flash("Invalid item index. Please try again.", "danger")

    return redirect(url_for('view_cart'))

@app.route('/cart')
def view_cart():
    user_id = session.get("user_id")
    cart = []  # Initialize cart
    saved_items = []  # Initialize saved items
    total_amount = 0  # Initialize total amount

    if user_id:
        # Retrieve user data (cart_items and saved_items) from JSON for logged-in users
        user_data = read_cart(user_id)
        cart = user_data.get('cart_items', [])
        saved_items = user_data.get('saved_items', [])

        # Ensure all prices in the cart are valid floats
        for item in cart:
            try:
                item['price'] = float(item.get('price', 0))  # Handle missing prices by defaulting to 0
            except (ValueError, TypeError):
                item['price'] = 0.00

        # Calculate the total amount in the cart
        total_amount = sum(item['price'] * item['quantity'] for item in cart)
    else:
        # For guest users, retrieve cart from session
        cart = session.get('guest_cart', [])

        # Ensure all prices in the guest cart are valid floats
        for item in cart:
            try:
                item['price'] = float(item.get('price', 0))  # Handle missing prices by defaulting to 0
            except (ValueError, TypeError):
                item['price'] = 0.00

        # Calculate the total amount in the guest cart
        total_amount = sum(item['price'] * item['quantity'] for item in cart)

    # Render the template, passing both cart and saved_items (empty for guests)
    return render_template(
        'cart.html',
        cart=cart,
        total_amount=total_amount,
        saved_items=saved_items
    )

@app.context_processor
def inject_cart_count():
    return {'cart_count': session.get('cart_count', 0)}

# Logout route (POST only with CSRF protection)
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()  # Explicitly clear the session
    logout_user()  # Log out the user
    
    return redirect(url_for('login'))




@app.route('/products/<category>')
@login_required
def get_products(category):
    # Get the saved location ID
    location_id = read_selected_location()  # Ensure this reads from locations.json

    if not location_id:
        flash("Please select a store location to view prices.", "warning")
        return redirect(url_for('home'))

    try:
        access_token = get_kroger_token(client_id, client_secret)
    except Exception as e:
        flash("Error fetching access token.", "danger")
        return redirect(url_for('home'))

    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    # Get the search query from request arguments (for free-text search)
    query = request.args.get('query', '').strip()
    page = int(request.args.get('page', 1))  # Default to page 1 if not provided

    # Map category to search terms if no custom query is provided
    if query:
        search_term = query  # Use the query as the search term
    else:
        category_mapping = {
            "Vegetables": "vegetables",
            "Fruits": "fruits",
            "Meats": "meat",
            "Frozen": "frozen",
            "Dairy": "dairy",
            "Bread": "bread",
            "Canned": "canned food",
            "Snacks": "snack",
            "Drinks": "beverage",
            "PersonalCare": "personal care"
        }
        search_term = category_mapping.get(category, "")

    # Set up page modifications
    params = {
        'filter.term': search_term,
        'filter.locationId': location_id,
        'filter.limit': 50,  # Page size set to 50
        'filter.start': (page - 1) * 50  # Offset calculated based on page number
    }

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = response.json().get('data', [])

        # Validate product data
        validated_products = []
        for product in products:
            product_data = {
                'description': product.get('description', 'No description'),
                'images': product.get('images', [{'sizes': [{'url': '/static/img/default_image.png'}]}]),
                'items': product.get('items', [{'price': {'regular': 'N/A'}}]),
                'delivery_date': product.get('delivery_date', 'Tomorrow'),
            }

            # Ensure all nested data exists
            if not product_data['images'][0].get('sizes'):
                product_data['images'][0]['sizes'] = [{'url': '/static/img/default_image.png'}]

            validated_products.append(product_data)

        has_next_page = len(validated_products) == 50  # Check if there's another page

        return render_template(
            'products.html',
            products=validated_products,
            category=category if not query else "Search Results",
            page=page,
            has_next_page=has_next_page,
            query=query
        )
    else:
        flash("Error fetching products.", "danger")
        return redirect(url_for('home'))


# Function to retrieve the cart count to use in templates
@app.context_processor
def cart_counter():
    cart_count = session.get('cart_count', 0)
    return {'cart_count': cart_count}

@app.route('/discounts', methods=['GET'])
@app.route('/discounts/<string:category>', methods=['GET'])
@login_required
def discounts(category=None):
    """
    Render discounts.html for general discounts or category_discounts.html for specific categories.
    """
    try:
        access_token = get_kroger_token(client_id, client_secret)
    except Exception as e:
        flash("Error fetching access token.", "danger")
        return redirect(url_for('home'))

    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    # Fetch the selected store location
    location_id = read_selected_location()
    if not location_id:
        flash("No store location selected. Please select a location first.", "warning")
        return redirect(url_for('home'))

    # Set API filter parameters
    params = {
        'filter.locationId': location_id,
        'filter.limit': 50,
       
    }

    # Add filter for category-specific discounts or general discounts
    if category:
        params['filter.term'] = category.lower()  # Filter by category
    else:
        params['filter.term'] = 'on sale'  # General filter for discounted items

    # Fetch discounted products
    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = []
        kroger_data = response.json().get('data', [])

        for product in kroger_data:
            item = product['items'][0] if product.get('items') else {}
            price = item.get('price', {})
            promo_price = price.get('promo', 'N/A')
            regular_price = price.get('regular', 'N/A')

            product_info = {
                'name': product.get('description', 'No description'),
                'price': promo_price,
                'original_price': regular_price,
                'imageUrl': product['images'][0]['sizes'][0]['url'] if product.get('images') else '/static/img/default_product.png'
            }
            products.append(product_info)

        # Render the correct template
        if category:
            return render_template('category_discounts.html', category=category.capitalize(), products=products)
        else:
            return render_template('discounts.html', products=products)
    else:
        flash("Error fetching discounted products. Please try again.", "danger")
        return redirect(url_for('home'))





from datetime import datetime  # Ensure this is imported at the top

def calculate_cart_totals(cart):
    """Helper function to calculate subtotal, sales tax, and total."""
    try:
        subtotal = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in cart)
    except (ValueError, TypeError):
        subtotal = 0.0

    sales_tax_rate = 0.08625  # Example tax rate
    sales_tax = round(subtotal * sales_tax_rate, 2)
    total_amount = round(subtotal + sales_tax, 2)

    return subtotal, sales_tax, total_amount

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user_id = session.get("user_id")
    cart = []
    subtotal = 0
    sales_tax = 0
    total_amount = 0

    # Retrieve cart for logged-in or guest user
    if user_id:
        user_data = read_cart(user_id)
        cart = user_data.get('cart_items', [])
    else:
        cart = session.get('guest_cart', [])

    # Calculate cart totals
    subtotal, sales_tax, total_amount = calculate_cart_totals(cart)

    if request.method == 'POST':
        # Validate required fields
        name = request.form.get('name')
        address = request.form.get('address')
        city = request.form.get('city')
        zip_code = request.form.get('zip')

        if not all([name, address, city, zip_code]):
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('checkout'))

        if not cart:
            flash("Your cart is empty. Please add items before checking out.", "warning")
            return redirect(url_for('home'))

        # Create order object
        order = {
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "order_items": cart,
            "subtotal": subtotal,
            "sales_tax": sales_tax,
            "total_price": total_amount,
            "shipping_details": {
                "name": name,
                "address": address,
                "city": city,
                "zip": zip_code
            }
        }

        if user_id:
            # Update user order history and clear cart
            user_data['order_history'] = user_data.get('order_history', [])
            user_data['order_history'].append(order)
            user_data['cart_items'] = []  # Clear cart
            write_cart(user_id, user_data)
        else:
            # Clear guest cart
            session['guest_cart'] = []

        # Send order confirmation email
        to_email = request.form.get('email')  # Optional email field
        if to_email:
            send_order_confirmation_email(to_email, name, address, city, zip_code, order)

        flash("Order placed successfully! A confirmation email has been sent.", "success")
        return redirect(url_for('home'))

    return render_template(
        'checkout.html',
        cart=cart,
        subtotal=subtotal,
        total_quantity=sum(item.get('quantity', 1) for item in cart),
        sales_tax=sales_tax,
        total_amount=total_amount
    )

@app.route('/api/order_history')
def api_order_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    with open('user_Storage.json', 'r') as f:
        users = json.load(f)
    
    user_data = users.get(user_id, {})
    order_history = user_data.get('order_history', [])
    
    return jsonify(order_history)

@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    from datetime import datetime

    # Retrieve form data
    name = request.form.get('name', '').strip()
    cvv = request.form.get('cvv','').strip()
    exp_date = request.form.get('expiry','').strip()
    cn = request.form.get('card_number','').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    zip_code = request.form.get('zip', '').strip()
    to_email = request.form.get('email', '').strip()

    # Validate required fields
    missing_fields = [field for field, value in {
        'Name on Card': name,
        'Card Number': cn,
        'Expiry Date': exp_date,
        'CVV': cvv,
        'Shipping Address': address,
        'City': city,
        'Zip Code': zip_code,
        'Email': to_email,
    }.items() if not value]

    if missing_fields:
        return jsonify({"message": "MissingFields", "errors": missing_fields})

    # Get user or guest cart
    user_id = session.get("user_id")
    cart_data = read_cart(user_id) if user_id else {'cart_items': session.get('guest_cart', [])}
    cart_items = cart_data.get('cart_items', [])

    if not cart_items:
        return jsonify({"message": "EmptyCart"})

    # Calculate totals
    subtotal, sales_tax, total_price = calculate_cart_totals(cart_items)

    # Calculate points earned
    points_earned = int(subtotal * 3)  # Assuming 3x multiplier for points

    # Create the order
    order = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "order_items": cart_items,
        "subtotal": subtotal,
        "sales_tax": sales_tax,
        "total_price": total_price,
        "points_earned": points_earned,
        "shipping_details": {
            "name": name,
            "address": address,
            "city": city,
            "zip": zip_code
        }
    }

    # Update user data or clear guest cart
    if user_id:
        users = load_user_storage()
        user_data = users.get(user_id, {})
        user_data.setdefault("order_history", []).append(order)

        # Update loyalty points
        user_data["loyalty_points"] = user_data.get("loyalty_points", 0) + points_earned

        # Save updated data
        users[user_id] = user_data
        write_users(users)
        write_cart(user_id, {'cart_items': []})
    else:
        # Clear guest cart
        session['guest_cart'] = []

    # Reset cart count in session
    session['cart_count'] = 0
    session.modified = True

    # Send confirmation email
    if to_email:
        try:
            send_postmark_order_confirmation(to_email, name, cart_items)
        except Exception as e:
            print(f"Error sending confirmation email: {str(e)}")
            return jsonify({"message": "EmailIssue"}), 500

    flash("Order placed successfully! You earned points immediately.", "success")
    return jsonify({"message": "OrderComplete", "redirect_url": url_for('home')})

@app.route('/account_info')
@login_required
def account_info():
    users = read_users()
    user_data = users.get(current_user.id, {})
    return render_template('account_info.html', user_data=user_data)

@app.route('/set_location')
def set_location():
    location_id = request.args.get('location_id')
    
    if location_id:
        write_selected_location(location_id)  # Update the JSON file with the new location
        flash("Location updated successfully.", "success")
    else:
        flash("No location ID provided.", "danger")
    
    return redirect(request.referrer or url_for('home'))

@app.route('/loyalty_rewards')
@login_required
def loyalty_rewards():
    # Fetch the user ID from the session and user data
    user_id = session.get("user_id")
    user_data = read_user(user_id)

    # Get rewards history from user data (order history)
    rewards_history = user_data.get("order_history", [])

    # Recalculate loyalty points from the order history
    total_loyalty_points = sum(
        int(order.get('points_earned', 0)) for order in rewards_history
    )

    # Ensure every order in rewards history has 'points_earned'
    for order in rewards_history:
        if 'points_earned' not in order:
            # Calculate points earned for the order based on subtotal (example: 3x multiplier)
            order['points_earned'] = int(order.get('subtotal', 0) * 3)

    # Update the user data with the calculated points if necessary
    user_data["loyalty_points"] = total_loyalty_points
    user_data["order_history"] = rewards_history
    write_users({user_id: user_data})  # Save the updated user data

    # Define the initial tier and next tier points
    tier = "Bronze"
    next_tier_points = 1000

    # Update tier based on loyalty points
    if total_loyalty_points >= 1000:
        tier = "Silver"
        next_tier_points = 3000
    if total_loyalty_points >= 3000:
        tier = "Gold"
        next_tier_points = 5000
    if total_loyalty_points >= 5000:
        tier = "Platinum"
        next_tier_points = None

    # Prepare rewards info
    rewards_info = {
        "points": total_loyalty_points,
        "tier": tier,
        "next_tier_points": next_tier_points,
        "points_to_next_tier": next_tier_points - total_loyalty_points if next_tier_points else 0,
    }

    # Render the loyalty rewards page with the updated rewards info and history
    return render_template(
        'loyalty_rewards.html',
        rewards_info=rewards_info,
        rewards_history=rewards_history
    )
@app.context_processor
def inject_locations():
    # Only fetch locations if not already in the session
    if 'locations' not in session:
        try:
            access_token = get_kroger_token(client_id, client_secret)
            location_url = "https://api.kroger.com/v1/locations"
            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
            params = {'filter.radiusInMiles': 50, 'filter.limit': 900}
            response = requests.get(location_url, headers=headers, params=params)
            
            if response.status_code == 200:
                session['locations'] = response.json().get('data', [])
            else:
                session['locations'] = []
        except Exception as e:
            session['locations'] = []
            print(f"Error fetching locations: {e}")
    
    return {'locations': session.get('locations', [])}

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    text = data.get('text', '')
    target_language = data.get('target', 'es')  # Default to Spanish

    if text:
        result = translate_client.translate(text, target_language=target_language)
        return jsonify(result['translatedText'])
    return jsonify({"error": "No text provided"}), 400

@app.context_processor
def inject_selected_location_and_locations():
    selected_location = read_selected_location()  # Retrieves selected location if stored
    
    # Access token and Kroger API endpoint
    access_token = get_kroger_token(client_id, client_secret)
    location_url = "https://api.kroger.com/v1/locations"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    params = {
        'filter.radiusInMiles': 50,
        'filter.limit': 350
    }

    # Fetch locations
    try:
        response = requests.get(location_url, headers=headers, params=params)
        if response.status_code == 200:
            locations = response.json().get('data', [])
        else:
            print(f"Error fetching locations: {response.status_code} - {response.text}")
            locations = []  # Fallback to empty list if fetch fails
    except Exception as e:
        print("Exception occurred while fetching locations:", e)
        locations = []  # Fallback in case of exception

    # Inject selected location and locations data into the template context
    return {'selected_location': selected_location, 'locations': locations}

GOOGLE_CLIENT_ID = '948980706830-8ff2bi5o0lupforj4u8h5odjs66krb1p.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

from authlib.integrations.flask_client import OAuth
import uuid

# Initialize OAuth
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=CONF_URL,
    client_kwargs={'scope': 'openid email profile'}
)


# Google Authentication
@app.route('/google/')
def google():
    # Redirect to google_auth function
    nonce = uuid.uuid4().hex
    session['nonce'] = nonce
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri,nonce=nonce)

@app.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    nonce = session.pop('nonce', None)

    if nonce is None:
        flash("Invalid session. Please try logging in again.", "error")
        return redirect(url_for('login'))

    user_info = oauth.google.parse_id_token(token, nonce=nonce)
    if user_info:
        user_id = user_info.get('email')  # Use email as the unique identifier
        users = read_users()  # Load users from user_storage.json

        # If the user doesn't exist, create a new entry in user_storage.json
        if user_id not in users:
            users[user_id] = {
                "password": None,  # Google accounts don't use passwords
                "name": user_info.get('name', ""),
                "email": user_info.get('email', ""),
                "phone": "",  # Default empty phone field
                "address": "",  # Default empty address field
            }
            write_users(users)  # Save to user_storage.json

        # Log the user in
        user = User(user_id)
        login_user(user)
        session['user_id'] = user_id

        # Initialize cart count in session
        user_data = read_cart(user_id)  # Read the user's cart
        cart = user_data.get('cart_items', [])

        # Validate that cart is a list of dictionaries
        if isinstance(cart, list) and all(isinstance(item, dict) for item in cart):
            session['cart_count'] = sum(item.get('quantity', 1) for item in cart)
        else:
            session['cart_count'] = 0  # Default to 0 if cart structure is invalid

        flash(f"Welcome, {user_info.get('name')}!", "success")
        return redirect(url_for('home'))
    else:
        flash("Failed to retrieve user information from Google.", "danger")
        return redirect(url_for('login'))

    
    app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

@app.route('/saved_items')
@login_required
def view_saved_items():
    user_id = session.get("user_id")
    cart_data = read_cart(user_id)
    saved_items = cart_data.get("saved_items", [])

    return render_template('saved_items.html', saved_items=saved_items)


if __name__ == "__main__":
    app.run(debug=True)
