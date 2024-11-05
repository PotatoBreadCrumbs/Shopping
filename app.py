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
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# First we are going to initialize the Flask app
app = Flask(__name__)
app.secret_key = b'\xef\xd4\x16\x98h\xc6\xdd\xc3\xc6\xce\x02\xd6@o\x8a|\x08\x1c\xd6\\X{\xeex'
csrf = CSRFProtect(app)  # Enable CSRF protection
# Configure Flask-Mail using environment variables
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize Flask-Mail
mail = Mail(app)
import os

import requests
import json
sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
def send_direct_email(to_email):
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {os.getenv('SENDGRID_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "dynamic_template_data": {
                    "reset_url": "http://127.0.0.1:5000/reset-password",  # Guys this is temporary url for local reset
                    "username": to_email  
                }
            }
        ],
        "from": {"email": "kgawrinauth1@pride.hofstra.edu"},
        "template_id": "d-9c2c93acfa0e40cbbeea3cf01582af1b"  # our custom template using the sendgrid api we made
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print("Direct API call status:", response.status_code)
    print("Response text:", response.text)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_page():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        
       
        users = read_users()
        

        for username, user_info in users.items():
            if user_info.get('email') == email:
               
                user_info['password'] = new_password
                write_users(users)  
                flash('Password updated successfully!', 'success')
                return redirect(url_for('login'))
        
        flash('Email not found. Please check and try again.', 'danger')


    return render_template('reset_password_updated.html')



# We created a file to store user data (this simulates a database using mysql lite) x
USER_FILE = 'user_storage.json'

# Our Kroger API credentials 
client_id = 'kevingawrinauth-b1629c2310698a009e85d726fbc0e9aa8264849196508842534'
client_secret = 'fpfEnrPkQnQcWGySAoig8G6Up1ZosRbV8u0LrKSd'

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'  
login_manager.init_app(app)

# Disable CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False
# implemented a helper functions to manage user data in a file
def read_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as file:
        return json.load(file)
def read_user(username):
    users = read_users()
    return users.get(username)

def write_users(users):
    with open(USER_FILE, 'w') as file:
        json.dump(users, file)

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
    
    

# Fetching our Kroger OAuth token
def get_kroger_token(client_id, client_secret):
    token_url = "https://api.kroger.com/v1/connect/oauth2/token"
    data = {
        'grant_type': 'client_credentials',
        'scope': 'product.compact'
    }
    auth = (client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(token_url, headers=headers, data=data, auth=auth)
    
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception("Error fetching access token: " + str(response.json()))


@app.route('/update_user', methods=['POST'])
@login_required
def update_user():
    # Get current user's ID and read their data
    username = current_user.id
    users = read_users()
    
    if username in users:
        # Update user information from form data
        users[username]['name'] = request.form['name']
        users[username]['email'] = request.form['email']
        users[username]['phone'] = request.form['phone']
        users[username]['address'] = request.form['address']
        
        # Write updated user data back to JSON file
        write_users(users)
        
        flash("User details updated successfully!", "success")
    else:
        flash("User not found.", "danger")
    
    return redirect(url_for('settings'))
import requests

@app.route('/orderhistory')
@login_required
def orderhistory():
    # Sample order data with renamed attribute to avoid conflict
    order_history = [
        {
            "date": "2024-10-12",
            "order_items": [
                {"name": "Sample Item 1", "price": 5.00},
                {"name": "Sample Item 2", "price": 7.50}
            ],
            "total_price": 12.50
        },
        {
            "date": "2024-10-13",
            "order_items": [
                {"name": "Sample Item 3", "price": 3.00},
                {"name": "Sample Item 4", "price": 6.50}
            ],
            "total_price": 9.50
        }
    ]

    return render_template('orderhistory.html', order_history=order_history)




@app.route('/settings')
@login_required
def settings():
    users = read_users()
    user_data = users.get(current_user.id, {})
    return render_template('settings.html', user_data=user_data)

# this is our user login route 
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
            return redirect(url_for('home'))  # redirect to home after login
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)


# our guest login route
@app.route('/guest_login')
def guest_login():
    # automatically log in as a guest
    guest_user = User('guest')
    login_user(guest_user)
    return redirect(url_for('home'))  # should allow us redirect to home after guest login


# the route for our user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  #  registration form
    if form.validate_on_submit():
        new_username = form.username.data
        new_password = form.password.data
        users = read_users()  # reads users from the file saved in db 
        
        if new_username in users:
            flash('Username already exists, please choose another.')
        else:
            users[new_username] = {'password': new_password}
            write_users(users)  # saves new user to the file
            flash('User registered successfully! Please log in.')
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

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
                send_direct_email(email)
                flash('Password reset instructions have been sent to your email.', 'info')
                break

        if not user_found:
            flash('Email address not found.', 'danger')

        # Redirect to the login page or another confirmation page
        return redirect(url_for('login'))

    # Render the forgot password page for GET requests
    return render_template('forgot_password.html')



@app.route('/')
@login_required
def home():
    form = LogoutForm()  # here im initializing the logout form with CSRF protection
    username = "Guest" if current_user.id == 'guest' else current_user.id
    locations = [
        {"id": 1, "name": "Long Island - Amityville", "zip_code": "11701"},
        {"id": 2, "name": "Long Island - Hicksville", "zip_code": "11801"},
        {"id": 3, "name": "Long Island - Commack", "zip_code": "11725"},
        {"id": 4, "name": "Long Island - Syosset", "zip_code": "11791"},
        {"id": 5, "name": "Long Island - Patchogue", "zip_code": "11772"}
    ]
    return render_template('index.html', username=username, form=form, locations=locations)



# route to view favorites page
@app.route('/favorites')
@login_required
def view_favorites():
    return render_template('favorites.html')

# our set predefined Long Island locations (Fake for demonstration)
locations = [
    {"id": 1, "name": "Long Island - Amityville", "zip_code": "11701"},
    {"id": 2, "name": "Long Island - Hicksville", "zip_code": "11801"},
    {"id": 3, "name": "Long Island - Commack", "zip_code": "11725"},
    {"id": 4, "name": "Long Island - Syosset", "zip_code": "11791"},
    {"id": 5, "name": "Long Island - Patchogue", "zip_code": "11772"},
]

# route to display store locations
@app.route('/locations')
@login_required
def get_locations():
    return render_template('locations.html', locations=locations)

@app.route('/products/<category>')
@login_required
def get_products(category):
    query = request.args.get('query', '').lower()
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    # Define a default location ID if none is provided (you can replace this with a valid ID)
    default_location_id = '70300209'  # Replace this with your valid Kroger location ID

    # Map display category to search terms
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
        "Personal Care": "personal care"
    }

    search_term = category_mapping.get(category, "")

    # Fetch products filtered by category and product name with location-specific pricing
    params = {
        'filter.term': f"{search_term} {query}" if query else search_term,
        'filter.locationId': default_location_id,  # Include the locationId for pricing
        'filter.limit': 50
    }

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = response.json().get('data')
        return render_template('products.html', products=products, category=category, query=query)
    else:
        flash("Error fetching products for the selected category.", "danger")
        return redirect(url_for('home'))


@app.route('/locations/<int:location_id>/products')
@login_required
def get_location_products(location_id):
    selected_location = next((loc for loc in locations if loc["id"] == location_id), None)
    if not selected_location:
        return jsonify({"error": "Invalid location selected"}), 404
    
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Fetch products with location-specific pricing
    params = {
        'filter.locationId': location_id,  # Include the locationId for store-specific pricing
        'filter.limit': 100
    }

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = response.json().get('data')
        return render_template('products.html', products=products, location=selected_location["name"])
    else:
        return jsonify({"error": "Error fetching products for the selected location"}), 500


@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    product_image = request.form.get('product_image')  # Retrieve image URL

    # Initialize cart if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []

    # Check if product is already in cart and update quantity
    for item in session['cart']:
        if item['name'] == product_name:
            item['quantity'] += 1
            session.modified = True
            return redirect(url_for('view_cart'))
        

    # Add new item to cart
    session['cart'].append({
        'name': product_name,
        'price': product_price,
        'image': product_image,  # Store image URL in the session
        'quantity': 1
    })
    session.modified = True
    return redirect(url_for('view_cart'))


@app.route('/update_quantity/<int:index>/<operation>', methods=['POST'])
@login_required
def update_quantity(index, operation):
    if 'cart' in session:
        try:
            item = session['cart'][index]
            if 'quantity' not in item:
                item['quantity'] = 1  # Initialize quantity if missing

            if operation == 'increase':
                item['quantity'] += 1
            elif operation == 'decrease':
                if item['quantity'] > 1:
                    item['quantity'] -= 1
                else:
                    # Optionally remove the item if quantity is 1 and trying to decrease
                    session['cart'].pop(index)
            
            session['cart_count'] = sum(item.get('quantity', 1) for item in session['cart'])
        except IndexError:
            flash("Item not found in the cart.", "danger")

    return redirect(url_for('view_cart'))


@app.route('/cart')
@login_required
def view_cart():
    cart = session.get('cart', [])

    # Convert price to float
    for item in cart:
        try:
            item['price'] = float(item['price'])  # Ensure price is a float
        except ValueError:
            item['price'] = 0.00  # Handle invalid prices

    total_amount = sum(item['price'] * item['quantity'] for item in cart)
    
    return render_template('cart.html', cart=cart, total_amount=total_amount)



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

@app.route('/discounts')
@login_required
def discounts():
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Fetch products with discount or promo
    params = {
        'filter.term': 'on sale',  # Filters for items on sale
        'filter.limit': 10  # Number of items to display
    }

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = []
        kroger_data = response.json().get('data')
        
        for product in kroger_data:
            # Handle missing price fields safely using get()
            item = product['items'][0] if product.get('items') else {}
            price = item.get('price', {})
            promo_price = price.get('promo', 'N/A')  # Default to 'N/A' if missing still trouble with this check with free time
            regular_price = price.get('regular', 'N/A')  # Default to 'N/A' if missing
            
            product_info = {
                'name': product.get('description', 'No description'),
                'price': promo_price,
                'original_price': regular_price,
                'imageUrl': product['images'][0]['sizes'][0]['url'] if product.get('images') else '/static/img/default_product.png'
            }
            products.append(product_info)
        
        return render_template('discounts.html', products=products)
    else:
        return jsonify({"error": "Error fetching discounted products"}), 500
    
    # Route to handle the search functionality with category filtering
@app.route('/search')
@login_required
def search():
    category = request.args.get('category')
    query = request.args.get('query')
    
    access_token = get_kroger_token(client_id, client_secret)
    search_url = "https://api.kroger.com/v1/products"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Adjust category mapping if necessary
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
        "Personal Care": "personal care"
    }

    # Prepare search term based on category
    category_search_term = category_mapping.get(category, "") if category != "All" else ""
    
    params = {
        'filter.term': query,
        'filter.limit': 60
    }
    if category_search_term:
        params['filter.term'] += f" {category_search_term}"

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        products = response.json().get('data')
        return render_template('products.html', products=products, category=category, query=query)
    else:
        flash("Error fetching products.", "danger")
        return redirect(url_for('home'))



# Function to retrieve the cart count to use in templates
@app.context_processor
def cart_counter():
    cart_count = session.get('cart_count', 0)
    return {'cart_count': cart_count}


@app.route('/checkout')
@login_required
def checkout():
    # Retrieve cart items from the session
    cart_items = session.get('cart', [])
    
    # Calculate subtotal
    subtotal = sum(float(item['price']) * item['quantity'] for item in cart_items)
    total_quantity = sum(item['quantity'] for item in cart_items)
    
    # Calculate sales tax (8.625% example)
    sales_tax_rate = 0.08625
    sales_tax = subtotal * sales_tax_rate
    
    # Calculate total cost
    total_cost = subtotal + sales_tax
    
    return render_template('checkout.html', cart_items=cart_items, total_quantity= total_quantity,subtotal=subtotal, sales_tax=sales_tax, total_cost=total_cost)
@app.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    # Here, you can handle the payment processing and order submission logic
    # For example, retrieve form data:
    name = request.form.get('name')
    card_number = request.form.get('card_number')
    expiry = request.form.get('expiry')
    cvv = request.form.get('cvv')
    address = request.form.get('address')
    city = request.form.get('city')
    zip_code = request.form.get('zip')

    # Dummy processing step - Replace with actual logic
    flash("Order placed successfully!", "success")

    # Clear the cart after checkout
    session.pop('cart', None)
    session['cart_count'] = 0
    return redirect(url_for('home'))

@app.route('/account_info')
@login_required
def account_info():
    users = read_users()
    user_data = users.get(current_user.id, {})
    return render_template('account_info.html', user_data=user_data)



@app.route('/loyalty_rewards')
@login_required
def loyalty_rewards():
    rewards_info = {
        "points": 1200,
        "tier": "Gold",
        "next_tier_points": 3000
    }
    return render_template('loyalty_rewards.html', rewards_info=rewards_info)

@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/remove_item/<int:index>', methods=['POST'])
@login_required
def remove_item(index):
    if 'cart' in session:
        try:
            session['cart'].pop(index)
            session.modified = True
            flash("Item removed from cart.", "success")
        except IndexError:
            flash("Item not found in the cart.", "danger")
    
    return redirect(url_for('view_cart'))

@app.before_request

def initialize_session():

    if 'cart' not in session:

        session['cart'] = []

    if 'saved_items' not in session:

        session['saved_items'] = []  # Store saved items here



@app.route('/save_for_later/<int:index>', methods=['POST'])

@login_required

def save_for_later(index):

    cart = session.get('cart', [])

    saved_items = session.get('saved_items', [])



    try:

        # Move the item from the cart to the saved items list

        item = cart.pop(index)

        saved_items.append(item)



        # Update session data

        session['cart'] = cart

        session['saved_items'] = saved_items

        session.modified = True

        flash("Item saved for later.", "info")

    except IndexError:

        flash("Item not found in the cart.", "danger")



    return redirect(url_for('view_cart'))



@app.route('/move_to_cart/<int:index>', methods=['POST'])

@login_required

def move_to_cart(index):

    cart = session.get('cart', [])

    saved_items = session.get('saved_items', [])



    try:

        # Move the item from the saved items list back to the cart

        item = saved_items.pop(index)

        cart.append(item)



        # Update session data

        session['cart'] = cart

        session['saved_items'] = saved_items

        session.modified = True

        flash("Item moved back to cart.", "success")

    except IndexError:

        flash("Item not found in saved items.", "danger")
    return redirect(url_for('view_cart')) #edited this line to redirect to view_cart 


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
