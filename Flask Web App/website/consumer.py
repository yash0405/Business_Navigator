from flask import Blueprint, session
from flask import render_template
from flask import request, jsonify
from flask import flash, redirect, url_for
from .models import Consumer, User, Inventory, Connection, Debt
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import cast, Integer
from sqlalchemy.sql import func

consumer = Blueprint('consumer',__name__)

def consumer_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, 'contact'):
            return redirect(url_for('consumer.login'))
        return func(*args, **kwargs)
    return decorated_view

@consumer.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form.get('email')
        password=request.form.get('password')

        consumer = Consumer.query.filter_by(email=email).first()
        if consumer:
            if check_password_hash(consumer.password, password):
                flash('Logged in Successfully',category='success')
                login_user(consumer, remember=True)
                return redirect(url_for('consumer.home'))
            else:
                flash('Incorrect password,try again.', category='error')
        else:
            flash('User Does not exist',category='error')
    return render_template("consumer_login.html", user=current_user)

@consumer.route('/logout')
@consumer_login_required
def logout():
    logout_user()
    return redirect(url_for('consumer.login'))

@consumer.route('/sign_up', methods=['GET','POST'])
def sign_up():
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        contact = request.form.get('contact')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
    
        consumer = Consumer.query.filter_by(email=email).first()
        if consumer:
            flash('Email Already exists',category='error')
        elif len(contact)!=10:
            flash('Kindly Recheck the mobile number', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(name)<2:
            flash('Length of name must be greater than 1', category='error')
        elif password1!=password2:
            flash('Passwords don\'t match', category='error')
        elif len(password1)<5:
            flash('Length of password must be at least 5 characters', category='error')
        else:
            # add user to the databse
            new_consumer = Consumer(email=email, name=name, contact=contact, password= generate_password_hash(password1, method ='scrypt'))
            db.session.add(new_consumer)
            db.session.commit()
            login_user(new_consumer, remember=True)
            flash('Account Created!', category='success')
            return redirect(url_for('consumer.home'))
    return render_template("consumer_sign_up.html", user=current_user)

@consumer.route('/home')
@consumer_login_required
def home():
    current_user_id = current_user.consumer_id

    # Get all shops
    shops = User.query.all()

    # For each shop, check if the current user is connected
    for shop in shops:
        connection = Connection.query.filter_by(consumer_id=current_user_id, shopkeeper_id=shop.id).first()
        shop.connected = bool(connection)

    # Render the page
    return render_template('consumer_home.html',user=current_user, shops=shops)

@consumer.route('/shop/details/<int:shop_id>')
@consumer_login_required
def shop_details(shop_id):
    # Fetch shop details for the selected shop
    shop = User.query.get(shop_id)
    if shop:
        inventory = Inventory.query.filter_by(user_id=shop_id).all()
        return render_template('shop_details.html', shop=shop, inventory=inventory, user=current_user)
    else:
        return "Shop not found."


@consumer.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        # Delete the account from the database
        db.session.delete(current_user)
        db.session.commit()

        # Log out the user
        logout_user()

        # Redirect to the login page
        return redirect(url_for('consumer.login'))
    else:
        # For 'GET' requests, return a confirmation form
        return render_template('consumer_delete_account.html')



@consumer.route('/shop/details/<int:shop_id>/search', methods=['GET'])
@consumer_login_required
def search_item(shop_id):
    item_name = request.args.get('item_name').lower()
    if not item_name:
        flash('Item name is required.', category='error')
        return redirect(url_for('consumer.shop_details', shop_id=shop_id))

    # Find item by name in the shop's inventory
    item = Inventory.query.filter_by(item_name=item_name, user_id=shop_id).first()
    if item:
        flash(f'Item found - Name: {item.item_name.capitalize()}, Quantity: {item.quantity}, Price: {item.price}', category='success')
    else:
        flash('Item not found.', category='error')

    return redirect(url_for('consumer.shop_details', shop_id=shop_id))



@consumer.route('/filter_shops', methods=['GET'])
@login_required
def filter_shops():
    # Get filter parameters from the request query parameters
    name = request.args.get('name').lower()
    location = request.args.get('location').lower()

    # Query shops based on the filter parameters
    filtered_shops = User.query

    # Apply filters if provided
    if name:
        filtered_shops = filtered_shops.filter(User.shop_name.ilike(f'%{name}%'))
    if location:
        filtered_shops = filtered_shops.filter(User.location.ilike(f'%{location}%'))

    # Execute the query and retrieve filtered shops
    filtered_shops = filtered_shops.all()

    # Render the home page template with filtered shops
    return render_template('consumer_home.html',user=current_user, shops=filtered_shops)


from flask import jsonify

@consumer.route('/connect_shop/<int:shop_id>', methods=['POST'])
@login_required
def connect_shop(shop_id):
    # Get the current user's ID
    current_user_id = current_user.consumer_id

    # Check if the connection already exists
    connection = Connection.query.filter_by(consumer_id=current_user_id, shopkeeper_id=shop_id).first()

    if not connection:
        # If the connection does not exist, create a new one
        new_connection = Connection(consumer_id=current_user_id, shopkeeper_id=shop_id)
        db.session.add(new_connection)
        db.session.commit()

    return jsonify({"status": "connected", "message": "You are now connected to this shop."})
    

@consumer.route('/disconnect_shop/<int:shop_id>', methods=['POST'])
@login_required
def disconnect_shop(shop_id):
    # Get the current user's ID
    current_user_id = current_user.consumer_id

    # Check if the connection exists
    connection = Connection.query.filter_by(consumer_id=current_user_id, shopkeeper_id=shop_id).first()

    if connection:
        # If the connection exists, delete it
        db.session.delete(connection)
        db.session.commit()

    return jsonify({"status": "disconnected", "message": "You are now disconnected from this shop."})


@consumer.route('/connected_shops')
@login_required
def shopkeeper_page():
    # Assuming the current user is logged in and their id is stored in session
    current_consumer_id = current_user.consumer_id

    # Get all connections for the current shopkeeper
    connections = Connection.query.filter_by(consumer_id=current_consumer_id).all()

    # Get the consumers connected to the current shopkeeper
    connected_shops = [connection.shopkeeper for connection in connections]

    # Render the page
    return render_template('connected_shops.html', connected_shops=connected_shops, user=current_user)

@consumer.route('/check_debt_record/<int:shopkeeper_id>/<int:consumer_id>')
@login_required
def debt_record(shopkeeper_id, consumer_id):
    # Get the consumer's debt records
    consumer_debts = Debt.query.filter_by(consumer_id=consumer_id, shopkeeper_id=shopkeeper_id).all()
    total_amount = db.session.query(func.sum(cast(Debt.amount,Integer))).filter_by(consumer_id=consumer_id, shopkeeper_id=shopkeeper_id).scalar()
    shopkeeper = User.query.filter_by(id=shopkeeper_id).first()
    return render_template('Consumer_side_debt.html',total_amount=total_amount, user=current_user, shopkeeper=shopkeeper, debts=consumer_debts, shopkeeper_id=shopkeeper_id)