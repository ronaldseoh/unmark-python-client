__all__ = ['UnmarkClient']

import urllib
import re
import json
import sys
import requests

class UnmarkClient(object):

    # I'm trying to make every request to Unmark server as internal XMLHttpRequest.
    # Details in https://github.com/cdevroe/unmark/wiki/Response-Logic
    def __init__(self, server_address, email, password):
    
        self.server_address = server_address

        self.email = email
        self.password = password
        
        # Fetch CSRF Token
        self.requests_session = requests.Session()
        self._main_page_response = self.requests_session.get(self.server_address)

        if self._main_page_response.status_code == 200:
            self.csrf_token = re.findall('(?:unmark.vars.csrf_token\s+=\s+\')(.+)\';', self._main_page_response.text)[0]
        else:
            raise Exception('Unable to fetch CSRF token from your Unmark server. Status code = '+str(self._main_page_response.status_code))

    def login(self):

        self.login_url = self.server_address + '/login'

        login_response = self.requests_session.post(
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
            raise Exception('Unable to connect to the login page. Status code = '+str(self._main_page_response.status_code))
        else:
            # With internal XMLHttpRequest, responses are given in JSON
            login_response_json = json.loads(login_response.text)
            
            if login_response_json['success'] is not True:
                raise Exception('Login failed from the server.')
            else:
                return True # Success

    def add(self, url):
        # Fetch the title of page from the URL
        page_response = self.requests_session.get(url)
        
        page_title = re.findall('(?<=<title>).+?(?=</title>)', page_response.text, re.DOTALL)[0]

        add_payload = {
            'url': url,
            'title': page_title
        }
    
        add_response = self.requests_session.get(
            'https://unmark.serv06.iamblogger.net/mark/add',
            params=add_payload,
            headers={
                'X-Requested-With': 'XMLHttpRequest'
            }
        )
        
        try:
            # With internal XMLHttpRequest, responses are given in JSON
            add_response_json = json.loads(add_response.text)
            
            if add_response_json['mark']['url'] == url and add_response_json['mark']['active'] == '1':
                return True # Success
            else:
                raise Exception("Something isn't right with the response from the server. URL = " + add_response_json['mark']['url'] + ', active = '+add_response_json['mark']['active'])
        except:
            raise Exception("Error occurred while parsing the server response. Probably means the add request have failed.")
            
if __name__ == '__main__':
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    
    server_address = config['server_address']
    email = config['email']
    password = config['password']
    
    client = UnmarkClient(server_address, email, password)
    
    client.login()
    
    client.add(str(sys.argv[1]))
