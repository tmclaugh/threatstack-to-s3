'''
Communicate with Threat Stack
'''
import os
import requests

THREATSTACK_BASE_URL = os.environ.get('THREATSTACK_BASE_URL', 'https://app.threatstack.com/api/v1')
THREATSTACK_API_KEY = '6hVZ07n9V2vv21saoJTkZNiJRDdVG0OBAqRRTm8323xswyFODhqhdiwanZVorK6jkl1aMci5'

def is_available():
    '''
    Check connectivity to Threat Stack.

    Returns a failure if cannot connect to Threat Stack API.  This could be
    anything from API credential issues to connection failure.
    '''

    alerts_url = '{}/alerts?count=1'.format(THREATSTACK_BASE_URL)

    resp = requests.get(
        alerts_url,
        headers={'Authorization': THREATSTACK_API_KEY}
    )

    return True

def get_alert_by_id(alert_id):
    '''
    Retrieve an alert from Threat Stack by alert ID.
    '''
    alerts_url = '{}/alerts/{}'.format(THREATSTACK_BASE_URL, alert_id)

    resp = requests.get(
        alerts_url,
        headers={'Authorization': THREATSTACK_API_KEY}
    )

    return resp.json()

