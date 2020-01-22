'''
Client for communicating with Vilfo API
'''

import json
import requests

import vilfo.exceptions

class Client:
    """
    Vilfo API client
    """
    DEFAULT_TIMEOUT = 20

    def __init__(self, host, token, ssl=False):

        self._host = host
        self._token = token
        protocol = 'https://' if ssl else 'http://'
        self._base_url = protocol + host + '/api/v1'

    def _request(self, method, endpoint, headers=None, data=None, params=None, timeout=None):
        url = self._base_url + endpoint
        headers = headers or {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % self._token,
        }
        timeout = timeout or self.DEFAULT_TIMEOUT

        try:
            response = getattr(requests, method)(url, headers=headers, data=data, params=params, timeout=timeout)
        except requests.exceptions.RequestException as ex:
            raise ex

        if 404 == response.status_code:
            raise vilfo.exceptions.VilfoException()

        if 403 == response.status_code or response_content_is_login_page(response.content):
            raise vilfo.exceptions.AuthenticationException()

        return response

    def ping(self):
        response = None
        try:
            response = self._request('get', '/system/ping')
        except requests.exceptions.RequestException as ex:
            raise ex

        return json.loads(response.text)

    def get_devices(self):
        response = None
        try:
            response = self._request('get', '/devices')
        except requests.exceptions.RequestException as ex:
            raise ex

        return json.loads(response.text)

    def get_device(self, mac_address):
        response = None
        try:
            response = self._request('get', '/devices/%s' % mac_address)
        except requests.exceptions.RequestException as ex:
            raise ex

        return json.loads(response.text)

    def is_device_online(self, mac_address):
        response = None

        try:
            response = requests.get(
                self._base_url + '/devices/' + mac_address,
                headers={
                    'Authorization': 'Bearer ' + self._token })
        except requests.exceptions.RequestException as ex:
            raise ex

        try:
            result = json.loads(response.text)
            
            return result['data']['status']['online']
        except:
            return False

        return False

    def get_load(self):
        response = None

        try:
            response = self._request('get', '/dashboard/board')
        except requests.exceptions.RequestException as ex:
            raise ex

        return json.loads(response.text)

    def reboot_router(self):
        response = None
        try:
            response = requests.post(
                self._base_url + '/system/reboot'
            )
        except requests.exceptions.RequestException as ex:
            raise ex

        return json.loads(response.text)

# Utility methods
def response_content_is_login_page(response_content):
    """Returns True if the provided response_content seems to be from the Vilfo login page."""

    detectors = [
        "<title>Login | Vilfo</title>",
        "<Login-Form",
    ]

    detected_count = 0

    for detector in detectors:
        if detector in str(response_content):
            detected_count += 1

    return (detected_count >= (len(detectors) / 2)) # Allow half of the detectors to fail for now.