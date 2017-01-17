# AWS S3 Model
#
# Manipulate objects in AWS S3.
import boto3
import datetime
from iso8601 import UTC
import json
import os
import time

TS_AWS_S3_BUCKET = os.environ.get('TS_AWS_S3_BUCKET')
TS_AWS_S3_PREFIX = os.environ.get('TS_AWS_S3_PREFIX', None)

def _get_alert_data_key(alert_id):
    '''
    Takes an alert ID and returns an S3 key path.
    '''
    alert_key = '/'.join(['alerts',
                          alert_id[0:2],
                          alert_id[2:4],
                          alert_id
                          ])

    if TS_AWS_S3_PREFIX:
        alert_key = '/'.join([TS_AWS_S3_PREFIX, alert_key])

    return alert_key

def is_available():
    '''
    Check ability to access S3 bucket.
    '''
    s3_client = boto3.client('s3')
    s3_client.list_objects(Bucket=TS_AWS_S3_BUCKET)

    return True

def get_alert_by_id(alert_id):
    '''
    Get alert by alert ID
    '''
    alert_key = _get_alert_data_key(alert_id)
    s3_client = boto3.client('s3')
    alert_data = s3_client.get_object(
        Bucket=TS_AWS_S3_BUCKET,
        Key=alert_key
    )

    body = alert_data.get('Body')
    body_text = body.read()

    return json.loads(body_text)

def get_alerts_by_date(start, end):
    '''
    Get alerts between given date start and end.

    both start and ed are datetime objects.
    '''
    s3_client = boto3.client('s3')

    # We store webhooks by date and time so we search for those first.
    if TS_AWS_S3_PREFIX:
        webhooks_prefix = '/'.join([TS_AWS_S3_PREFIX, 'webhooks'])
    else:
        webhooks_prefix = 'webhooks'

    # We can only get 1000 objects at a time.  Also, list_objects() was not
    # returning a Marker on truncated responses so using list_objects_v2()
    # here instead.
    webhook_objects = []
    client_continuation_token = ''
    while True:
        list_object_params = {
            'Bucket': TS_AWS_S3_BUCKET,
            'Prefix': webhooks_prefix,
        }
        if client_continuation_token:
            list_object_params['ContinuationToken'] = client_continuation_token

        webhook_response = s3_client.list_objects_v2(**list_object_params)
        webhook_objects += webhook_response.get('Contents')

        # Break if response tells us there is no more.
        if webhook_response.get('IsTruncated'):
            client_continuation_token = webhook_response.get('NextContinuationToken')
        else:
            break

    alert_ids = []
    for obj in webhook_objects:
        key = obj.get('Key')
        print(key)
        # Remove webhook path prefix (and delimiter) and split string into
        # time prefix and alert ID.
        webhook_time_prefix, alert_id = key[len(webhooks_prefix) + 1:].rsplit('/', 1)
        print(webhook_time_prefix)
        # There are more compact ways of doing the following but I prefer to
        # show the sequence of events.
        #
        # split prefix into a list of strings.
        webhook_time_prefix_list = webhook_time_prefix.split('/')
        print(webhook_time_prefix_list)
        # use list comprehension to create a list of ints.  See also:
        # map(int, webhook_time_prefix_list)
        webhook_time_prefix_ints = [int(e) for e in webhook_time_prefix_list]
        # use *expression syntax to pass in values as a set of arguments. Also
        # supply tzinfo because the datetime objects we're supplied have them.
        webhook_time = datetime.datetime(*webhook_time_prefix_ints, tzinfo=UTC)

        if start < webhook_time < end:
            alert_ids.append(alert_id)

    alerts = []
    for alert_id in alert_ids:
        alert_data = get_alert_by_id(alert_id)
        alerts.append(alert_data)

    return alerts

def put_webhook_data(alert):
    '''
    Put alert webhook data in S3 bucket.
    '''
    alert_time = time.gmtime(alert.get('created_at')/1000)
    alert_time_path = time.strftime('%Y/%m/%d/%H/%M', alert_time)

    alert_key = '/'.join(['webhooks', alert_time_path, alert.get('id')])
    if TS_AWS_S3_PREFIX:
        alert_key = '/'.join([TS_AWS_S3_PREFIX, alert_key])

    s3_client = boto3.client('s3')
    s3_client.put_object(
        Body=json.dumps(alert),
        Bucket=TS_AWS_S3_BUCKET,
        Key=alert_key
    )

    return None

def put_alert_data(alert):
    '''
    Put alert data in S3.
    '''
    alert_id = alert.get('id')
    alert_key = _get_alert_data_key(alert_id)

    s3_client = boto3.client('s3')
    s3_client.put_object(
        Body=json.dumps(alert),
        Bucket=TS_AWS_S3_BUCKET,
        Key=alert_key
    )

    return None

