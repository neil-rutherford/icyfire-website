from flask import Blueprint

bp = Blueprint('promo', __name__)

from app.promo import routes