from flask import Flask

def _initialize_blueprints(application):
    '''
    Register Flask blueprints
    '''
    from views.s3 import s3
    application.register_blueprint(s3, url_prefix='/api/v1/s3')

def create_app():
    '''
    Create an app by initializing components.
    '''
    application = Flask(__name__)

    _initialize_blueprints(application)

    # Do it!
    return application
