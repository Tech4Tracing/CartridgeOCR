import argparse
import requests
import logging
import os
import json

# TODO: upload should set the prediction status for the image correctly.

parser = argparse.ArgumentParser()
parser.add_argument('--cookie', type=str, required=True)
parser.add_argument('--root-url', type=str, default="http://127.0.0.1:8080")
parser.add_argument('--email', type=str, required=True)
parser.add_argument('--name', type=str, required=True)
parser.add_argument('--superuser', action='store_true', default=False, required=False)
args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

# Create the empty collection
base_url = f"{args.root_url}/api/v0/"
users_url = base_url + "users"

payload = {
    'name': args.name,
    'email': args.email,
    'is_superuser': args.superuser
}

users_result = requests.post(users_url, headers={"Cookie": f"{args.cookie}"}, json=payload)

if users_result.status_code != 201:
    raise Exception(f"Failed to create user: {users_result.text}")

logging.info(f'Created user: {users_result.json()}')
