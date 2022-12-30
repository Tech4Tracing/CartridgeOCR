
from base64 import b64encode
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--endpoint', type=str, default='http://127.0.0.1:8081')
args=parser.parse_args()

fn = '/mnt/c/GitHub/CartridgeOCR/data/dataset/Bing20210312HeadstampAfrica21.jpg'

url = args.endpoint + '/api/v0/headstamp_predict'
with open(fn, 'rb') as inF:
    bytes = inF.read()

payload = {'image': b64encode(bytes).decode(), 'render':False}
#files = [('file', ('image.jpg', bytes, 'image/jpeg'))]
headers = {
  'x-api-key': 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx',
  'Content-Type': 'application/json'
}
response = requests.post(url, headers=headers, json=payload)
print(response.text)