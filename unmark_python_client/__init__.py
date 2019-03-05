__all__ = ['UnmarkClient']

import urllib
import re
import json
import sys
import warnings
import requests

class UnmarkClient():

    # I'm trying to make every request to Unmark server as internal XMLHttpRequest.
    # Details in https://github.com/cdevroe/unmark/wiki/Response-Logic
    def __init__(self, server_address, email, password):

        self.server_address = server_address

        self.email = email
        self.password = password

        # Fetch CSRF Token
        self.unmark_requests_session = requests.Session()
        self._main_page_response = self.unmark_requests_session.get(self.server_address)

        if self._main_page_response.status_code == 200:
            self.csrf_token = re.findall(
                r'(?:unmark.vars.csrf_token\s+=\s+\')(.+)\';',
                self._main_page_response.text)[0]
        else:
            raise Exception(
                'Unable to fetch CSRF token from your Unmark server. '
                'Status code = ' + str(self._main_page_response.status_code))

    def login(self):

        login_response = self.unmark_requests_session.post(
            url=self.server_address+'/login',
            data={
                'email': self.email,
                'password': self.password,
                'csrf_token': self.csrf_token,
                'content_type': 'json'
            },
            headers={
                'Referer': self.server_address,
                'X-Requested-With': 'XMLHttpRequest'
            }
        )

        if login_response.status_code != 200:
            raise Exception(
                'Unable to connect to the login page. '
                'Status code = '+str(self._main_page_response.status_code))

        # With internal XMLHttpRequest, responses are given in JSON
        login_response_json = json.loads(login_response.text)

        if login_response_json['success'] is not True:
            raise Exception('Login failed from the server.')

        return True # Success

    def add(self, url):
        # Send a HEAD request first to url and determine the content-type
        try:
            page_response_head = requests.head(url)
        except requests.ConnectionError as e:
            print('Unable to create a connection to the given URL. Error = ' + str(e))
            return False
        except (requests.exceptions.InvalidSchema, requests.exceptions.MissingSchema) as e:
            print('Given URL is invalid. Error = ' + str(e))
            return False

        content_type_string = page_response_head.headers['Content-Type'].lower()

        # If the page is not a HTML code, then skip the check for <title>
        if not content_type_string.startswith('text/html'):
            warning_message = (
                'Unknown Content-Type detected. '
                'Will not attempt to get the title. '
                'Content-Type = ' + str(content_type_string)
            )

            warnings.warn(warning_message, Warning, stacklevel=2)

            # Use url as a title
            page_title = url
        else:
            # Fetch the whole page from the URL
            try:
                page_response = requests.get(url)
            except requests.ConnectionError as e:
                print('Unable to create a connection to the given URL. Error = ' + str(e))
                return False

            # Extract <title> tag
            try:
                page_title = re.findall(
                    '(?<=<title>).+?(?=</title>)',
                    page_response.text,
                    re.DOTALL)[0]
            except:
                warning_message = 'Error while extracting <title> tag.'
                warnings.warn(warning_message, Warning, stacklevel=2)
                page_title = url

        add_payload = {
            'url': url,
            'title': page_title
        }

        add_response = self.unmark_requests_session.get(
            'https://unmark.serv06.iamblogger.net/mark/add',
            params=add_payload,
            headers={
                'X-Requested-With': 'XMLHttpRequest'
            }
        )

        try:
            # With internal XMLHttpRequest, responses are given in JSON
            add_response_json = json.loads(add_response.text)

            if add_response_json['mark']['url'] == url and \
            add_response_json['mark']['active'] == '1':
                return True # Success

            raise Exception(
                "Something isn't right with the response from the server."
                " URL = " + add_response_json['mark']['url'] + ", "
                "active = "+add_response_json['mark']['active'])
        except:
            raise Exception(
                "Error occurred while parsing the server response. "
                "Probably means the add request have failed.")
