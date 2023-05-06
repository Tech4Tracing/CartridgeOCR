
from base64 import b64encode
import requests
import argparse
import os
import ssl

# TODO: the script was modified to use the AzureML endpoint.
# we no longer have a direct endpoint to query.  Consider setting one up in the annotations app.

def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

allowSelfSignedHttps(True) # this line is needed if you use self-signed certificate in your scoring service.

parser = argparse.ArgumentParser()
parser.add_argument('--endpoint', type=str, default='http://127.0.0.1:8081')
parser.add_argument('--key', type=str, required=False)
parser.add_argument('--deployment', type=str, default='dev')
args=parser.parse_args()

fn = '/mnt/c/GitHub/CartridgeOCR/data/dataset/Bing20210312HeadstampAfrica21.jpg'

url = args.endpoint #+ '/api/v0/headstamp_predict'
with open(fn, 'rb') as inF:
    bytes = inF.read()

payload = {'image': b64encode(bytes).decode(), 'render':False}
#files = [('file', ('image.jpg', bytes, 'image/jpeg'))]
key = args.key if args.key else 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'
headers = {
  'Authorization': f'Bearer {key}',
  'Content-Type': 'application/json',
  'azureml-model-deployment': args.deployment
}
response = requests.post(url, headers=headers, json=payload)
print(response.text)