from flask import Blueprint

bp = Blueprint('security', __name__)

from app.admin import routes