'''
API to archive alerts from Threat Stack to S3
'''

from flask import Blueprint, jsonify, request
import iso8601
import app.models.s3 as s3_model
import app.models.threatstack as threatstack_model

s3 = Blueprint('s3', __name__)

class S3ViewError(Exception):
    '''
    Base S3 View error class.
    '''

class S3ViewDateParseError(S3ViewError):
    '''
    Unparseable date.
    '''

class S3ViewWebhookDataError(S3ViewError):
    '''
    There is an issue with the webhook data.
    '''

def _parse_date(date):
    '''
    Parse a date string and return a datetime object.
    '''
    try:
        return iso8601.parse_date(date)
    except iso8601.ParseError:
        raise S3ViewDateParseError('Unable to parse date: {}'.format(date))


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
    success = True

    return jsonify(success=success, s3=s3_info, threatstack=ts_info), status_code

@s3.route('/alert', methods=['POST'])
def put_alert():
    '''
    Archive Threat Stack alerts to S3.
    '''

    webhook_data = request.get_json()

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

