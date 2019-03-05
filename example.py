import json
import sys
import unmark_python_client

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

server_address = config['server_address']
email = config['email']
password = config['password']

client = unmark_python_client.UnmarkClient(server_address, email, password)

login_successful = client.login()

if login_successful:
    add_successful = client.add(str(sys.argv[1]))
    
    if add_successful:
        print("Add successful!")