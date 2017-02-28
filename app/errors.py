'''
Application error handlers.
'''
from app.models.s3 import S3ClientError
from app.models.threatstack import ThreatStackError
from app.views.s3 import S3ViewError
from flask import Blueprint, jsonify
import logging

_logger = logging.getLogger(__name__)

errors = Blueprint('errors', __name__)

@errors.app_errorhandler(S3ViewError)
@errors.app_errorhandler(S3ClientError)
@errors.app_errorhandler(ThreatStackError)
def handle_error(error):
    # err.args can be variable length.  Conver to a list ans stringify
    # contents.
    log_exception(error)
    message = [str(x) for x in error.args]
    status_code = error.status_code
    success = False
    response = {
        'success': success,
        'error': {
            'type': error.__class__.__name__,
            'message': message
        }
    }

    return jsonify(response), status_code

@errors.app_errorhandler(Exception)
def handle_unexpected_error(error):
    log_exception(error)
    status_code = 500
    success = False
    response = {
        'success': success,
        'error': {
            'type': 'UnexpectedException',
            'message': 'An unexpected error has occurred.'
        }
    }

    return jsonify(response), status_code

def log_exception(error):
    '''
    Log our exception.
    '''
    _logger.exception(error)

