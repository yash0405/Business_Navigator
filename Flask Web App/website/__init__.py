from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME= "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY']= 'vdghgfvasvdjav dj fha'
    app.config['SQLALCHEMY_DATABASE_URI']=f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .consumer import consumer

    app.register_blueprint(views,url_prefix='/')
    app.register_blueprint(auth,url_prefix='/')
    app.register_blueprint(consumer,url_prefix='/consumer')

    from .models import User, Inventory, Consumer
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()

# Set the login views
    login_manager.login_view = 'auth.login'
    login_manager.refresh_view = 'consumer.login'

# Initialize the app
    login_manager.init_app(app)

# User Loader function
    @login_manager.user_loader
    def load_user(user_id):
        if '|' not in user_id:
            return None
        user_type, user_id = user_id.split('|')
        if user_type == 'User':
            return User.query.get(int(user_id))
        elif user_type == 'Consumer':
            return Consumer.query.get(int(user_id))

    return app

def create_database(app):
    if not path.exists('website/'+ DB_NAME):
        db.create_all(app=app)
        print('Created Database!')