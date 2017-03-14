'''
Initialize flask components.
'''
from flask_lambda import FlaskLambda
import logging

_logger = logging.getLogger(__name__)

def _initialize_blueprints(application):
    '''
    Register Flask blueprints
    '''
    from app.views.s3 import s3
    application.register_blueprint(s3, url_prefix='/threatstack-to-s3/api/v1/s3')

def _initialize_errorhandlers(application):
    '''
    Initialize error handlers
    '''
    from app.errors import errors
    application.register_blueprint(errors)

def create_app():
    '''
    Create an app by initializing components.
    '''
    application = FlaskLambda(__name__)

    _initialize_errorhandlers(application)
    _initialize_blueprints(application)

    # Do it!
    return application

