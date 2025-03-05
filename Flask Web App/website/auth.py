from flask import Blueprint, jsonify
from flask import render_template
from flask import request
from flask import flash, redirect, url_for
from .models import User, Consumer, Inventory, Connection, Debt
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import cast, Integer
from sqlalchemy.sql import func

auth = Blueprint('auth',__name__)

def shopkeeper_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, 'shop_name'):
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return decorated_view

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form.get('email')
        password=request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in Successfully',category='success')
                login_user(user, remember=True) 
                return redirect(url_for('auth.home'))
            else:
                flash('Incorrect password,try again.', category='error')
        else:
            flash('User Does not exist',category='error')
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@shopkeeper_login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign_up', methods=['GET','POST'])
def sign_up():
    if(request.method == 'POST'):
        name = request.form.get('name').lower()
        email = request.form.get('email')
        shop_name = request.form.get('shop_name').lower()
        contact = request.form.get('contact')
        location = request.form.get('location').lower()
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
    
        user = User.query.filter_by(email=email).first()
        if user:
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
            new_user = User(email=email,shop_name=shop_name, location=location, name=name, contact=contact, password= generate_password_hash(password1, method ='scrypt'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account Created!', category='success')
            return redirect(url_for('auth.home'))
        

    return render_template("sign_up.html", user=current_user)


@auth.route('/home')
@shopkeeper_login_required
def home():
    return render_template("home.html",user=current_user)

@auth.route('/inventory')
@shopkeeper_login_required
def inventory():
    return render_template("inventory_page.html", user=current_user)

@auth.route('/add_item',methods=['POST'])
@shopkeeper_login_required
def add_item():
    item_name=request.form.get('itemName').lower()
    quantity=request.form.get('itemQuantity')
    price=request.form.get('itemPrice')

    existing_item = Inventory.query.filter_by(item_name=item_name, user_id=current_user.id).first()
    if existing_item:
        flash('Item already exists in inventory!', category='error')
    else:
        new_item = Inventory(
            item_name=item_name,
            quantity=quantity,
            price=price,
            user_id=current_user.id
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item added to inventory!', category='success')

    return redirect(url_for('auth.inventory'))

@auth.route('/remove_item', methods=['POST'])
@shopkeeper_login_required
def remove_item():
    item_name = request.form.get('removeItemName').lower()

    # Validate input
    if not item_name:
        flash('Item name is required.', category='error')
    else:
        # Find item by name
        item = Inventory.query.filter_by(item_name=item_name, user_id=current_user.id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            flash('Item "{}" removed from inventory!'.format(item_name.capitalize()), category='success')
        else:
            flash('Item "{}" not found.'.format(item_name.capitalize()), category='error')

    return redirect(url_for('auth.inventory'))

@auth.route('/update_item', methods=['POST'])
@shopkeeper_login_required
def update_item():
    item_name = request.form.get('updateItemName').lower()
    new_quantity = request.form.get('updateItemQuantity')
    new_price = request.form.get('updateItemPrice')

    # Validate input
    if not item_name:
        flash('Item name is required.', category='error')
    else:
        # Find item by name
        item = Inventory.query.filter_by(item_name=item_name, user_id=current_user.id).first()
        if not item:
            flash('Item "{}" not found.'.format(item_name.capitalize()), category='error')
        else:
            # Update quantity if provided
            if new_quantity:
                item.quantity = new_quantity

            # Update price if provided
            if new_price:
                item.price = new_price

            db.session.commit()
            flash('Item "{}" updated successfully!'.format(item_name.capitalize()), category='success')

    return redirect(url_for('auth.inventory'))

@auth.route('/search_item', methods=['POST'])
@shopkeeper_login_required
def search_item():
    item_name = request.form.get('searchItemName').lower()

    # Validate input
    if not item_name:
        flash('Item name is required.', category='error')
        return redirect(url_for('auth.inventory'))

    # Find item by name
    item = Inventory.query.filter_by(item_name=item_name, user_id=current_user.id).first()
    if item:
        flash(f'Item found - Name: {item.item_name.capitalize()}, Quantity: {item.quantity}, Price: {item.price}', category='success')
    else:
        flash('Item not found.', category='error')

    return redirect(url_for('auth.inventory'))

@auth.route('/inventory_items')
@shopkeeper_login_required
def inventory_items():
    user= current_user
    return render_template('inventory_data.html',user=user)


@auth.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        # Delete the account from the database
        db.session.delete(current_user)
        db.session.commit()

        # Log out the user
        logout_user()

        # Redirect to the login page
        return redirect(url_for('auth.login'))
    else:
        # For 'GET' requests, return a confirmation form
        return render_template('delete_account.html')
        


@auth.route('/connected_consumer')
@shopkeeper_login_required
def shopkeeper_page():
    # Assuming the current user is logged in and their id is stored in session
    current_shopkeeper_id = current_user.id

    # Get all connections for the current shopkeeper
    connections = Connection.query.filter_by(shopkeeper_id=current_shopkeeper_id).all()

    # Get the consumers connected to the current shopkeeper
    connected_consumers = [connection.consumer for connection in connections]

    # Render the page
    return render_template('connected_consumer.html', connected_consumers=connected_consumers, user=current_user)


@auth.route('/debt_management/<int:shopkeeper_id>/<int:consumer_id>')
@shopkeeper_login_required
def debt_management(shopkeeper_id, consumer_id):
    # Get the consumer's debt records
    consumer_debts = Debt.query.filter_by(consumer_id=consumer_id, shopkeeper_id=shopkeeper_id).all()
    consumer = Consumer.query.filter_by(consumer_id=consumer_id).first()
    total_amount = db.session.query(func.sum(cast(Debt.amount,Integer))).filter_by(consumer_id=consumer_id, shopkeeper_id=shopkeeper_id).scalar()
    return render_template('debt_management.html',total_amount=total_amount, user=current_user, consumer=consumer, debts=consumer_debts, shopkeeper_id=shopkeeper_id)

@auth.route('/add_debt/<int:shopkeeper_id>/<int:consumer_id>', methods=['POST'])
@shopkeeper_login_required
def add_debt(consumer_id, shopkeeper_id):
    # Extract form data
    item_name = request.form.get('item-name').lower()
    amount_paid = request.form.get('amount').lower()

    # Create a new debt record
    new_debt = Debt(item=item_name, amount=amount_paid, consumer_id=consumer_id, shopkeeper_id=shopkeeper_id)
    db.session.add(new_debt)
    db.session.commit()

    # Redirect back to the debt management page
    return redirect(url_for('auth.debt_management',shopkeeper_id=shopkeeper_id, consumer_id=consumer_id))

@auth.route('/delete_debt/<int:debt_id>', methods=['DELETE'])
@shopkeeper_login_required
def delete_debt(debt_id):
    # Find the debt record to delete
    debt = Debt.query.get_or_404(debt_id)

    # Delete the debt record from the database
    db.session.delete(debt)
    db.session.commit()

    # Return a success response
    return jsonify({'message': 'Debt record deleted successfully'}), 200
    