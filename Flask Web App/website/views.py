from flask import Blueprint, render_template
from flask_login import login_user, login_required, logout_user, current_user

views = Blueprint('views',__name__)


@views.route('/')
def first_page():
    return render_template("fist_page.html")

