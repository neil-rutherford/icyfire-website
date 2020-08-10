from flask import Blueprint

bp = Blueprint('meta', __name__)

from app.meta import routes, forms