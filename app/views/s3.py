'''
API to archive alerts from Threat Stack to S3
'''

from flask import Blueprint, jsonify, request
import app.models.s3 as s3_model
import app.models.threatstack as threatstack_model

s3 = Blueprint('s3', __name__)

#decerator refers to the blueprint object.
@s3.route('/status', methods=['GET'])
def is_available():
    '''
    Test that Threat Stack and S3 bucket are reachable.
    '''
    s3_status = s3_model.is_available()
    s3_info = {'success': s3_status}

    ts_status = threatstack_model.is_available()
    ts_info = {'success': ts_status}

    status_code = 200
    success = True

    return jsonify(success=success, s3=s3_info, threatstack=ts_info), status_code

@s3.route('/alert', methods=['POST'])
def put_alert():
    '''
    Archive Threat Stack alerts to S3.
    '''
    webhook_data = request.get_json()
    for alert in webhook_data.get('alerts'):
        alert_full = threatstack_model.get_alert_by_id(alert.get('id'))

        s3_model.put_webhook_data(alert)
        s3_model.put_alert_data(alert_full)

    status_code = 200
    success = True
    response = {'success': success}

    return jsonify(response), status_code

