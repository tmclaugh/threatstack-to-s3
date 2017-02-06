'''
Application error handlers.
'''
from flask import Blueprint, jsonify

errors = Blueprint('errors', __name__)

@errors.app_errorhandler(Exception)
def handle_threatstack_error(error):
    status_code = 500
    success = False
    response = {
        'success': success,
        'error': {
            'type': error.__class__.__name__,
            'message': str(error.args)
        }
    }

    return jsonify(response), status_code

