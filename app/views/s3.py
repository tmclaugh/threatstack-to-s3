'''
API to archive alerts from Threat Stack to S3
'''

from app.errors import AppBaseError
import app.models.s3 as s3_model
import app.models.threatstack as threatstack_model
from flask import Blueprint, jsonify, request
import iso8601
import logging
import requests

_logger = logging.getLogger(__name__)

s3 = Blueprint('s3', __name__)

class S3ViewError(AppBaseError):
    '''
    Base S3 View error class.
    '''
    status_code = 400

class S3ViewDateParseError(S3ViewError):
    '''
    Unparseable date.
    '''

class S3ViewWebhookDataError(S3ViewError):
    '''
    There is an issue with the webhook data.
    '''

def _get_webhook_data(request):
    '''
    Handle Threat Stack vs. AWS SNS messages.
    '''
    request_data = request.get_json()
    webhook_data = None
    if 'TopicArn' in request_data.keys() and 'Message' in request_data.keys():
        if type(request_data['Message']) == dict:
            webhook_data = request_data.get('Message')
    else:
        webhook_data = request_data

    return webhook_data

def _parse_date(date):
    '''
    Parse a date string and return a datetime object.
    '''
    try:
        return iso8601.parse_date(date)
    except iso8601.ParseError:
        raise S3ViewDateParseError('Unable to parse date: {}'.format(date))

def _confirm_aws_sns_subscription(request):
    '''
    Confirm an SNS subscription
    '''
    request_data = request.get_json()
    confirmation_url = request_data.get('SubscribeURL')
    confirmation_response = requests.get(confirmation_url)
    if confirmation_response.ok:
        success = True
    else:
        success = False

    return jsonify({'success': success}), confirmation_response.status_code

# Service routes.
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
    if s3_status and ts_status:
        success = True
    else:
        success = False

    return jsonify(success=success, s3=s3_info, threatstack=ts_info), status_code

@s3.route('/alert', methods=['POST'])
def put_alert():
    '''
    Archive Threat Stack alerts to S3.
    '''
    # could be getting a message from TS or SNS.
    if request.headers['X-Amz-Sns-Message-Type'] == 'SubscriptionConfirmation':
        return _confirm_aws_sns_subscription(request)
    webhook_data = _get_webhook_data(request)

    # Check webhook data to ensure correct format.
    if webhook_data == None:
        # Can be caused by incorrect Content-Type.
        msg ='No webhook data found in request: {}'.format(webhook_data)
        raise S3ViewWebhookDataError(msg)

    if not webhook_data.get('alerts'):
        msg = 'Webhook lacks alerts: {}'.format(webhook_data)
        raise S3ViewWebhookDataError(msg)

    for alert in webhook_data.get('alerts'):
        if not alert.get('id'):
            msg = "alert lacks 'id' field: {}".format(webhook_data)
            raise S3ViewWebhookDataError(msg)

        if not alert.get('created_at'):
            msg = "alert lacks 'created_at' field: {}".format(webhook_data)
            raise S3ViewWebhookDataError(msg)

    # Process alerts in webhook
    for alert in webhook_data.get('alerts'):
        alert_full = threatstack_model.get_alert_by_id(alert.get('id'))

        s3_model.put_webhook_data(alert)
        s3_model.put_alert_data(alert_full)

    status_code = 200
    success = True
    response = {'success': success}

    return jsonify(response), status_code

@s3.route('/alert', methods=['GET'])
def get_alerts_by_form_parameters():
    '''
    Get an alert based on the
    '''
    start = request.args.get('start') or request.form.get('start')
    end = request.args.get('end') or request.form.get('end')

    # Convert to datetime objects
    start_datetime = _parse_date(start)
    end_datetime = _parse_date(end)

    alerts = s3_model.get_alerts_by_date(start_datetime, end_datetime)
    status_code = 200
    success = True
    response = {
        'success': success,
        'alerts': alerts
    }

    return jsonify(response), status_code

@s3.route('/alert/<alert_id>', methods=['GET'])
def get_alert_by_id(alert_id):
    '''
    Get an alert by alert ID.
    '''
    alert = s3_model.get_alert_by_id(alert_id)
    status_code = 200
    success = True
    response = {
        'success': success,
        'alert': alert
    }

    return jsonify(response), status_code

