from flask import render_template, current_app
from app import db
from app.errors import bp

# Tested 2020-08-04
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

# Tested 2020-08-04
@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500