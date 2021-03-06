import urllib.request
import json
import os
import ssl
import base64
import sys
from PIL import Image
from math import sqrt
from io import BytesIO
import argparse

endpoints = {
    'local': 'http://localhost:6789',
    'aks': 'https://cartridgeocr3nta3a.westeurope.cloudapp.azure.com:443/api/v1/service/cartridgeocraks/score',
    #'aci': 'http://3ca4da63-9969-4a9e-b85a-3d28ae14b212.westeurope.azurecontainer.io/score'
    'aci': 'http://361c4fcc-d9d3-4691-a8b0-d93275148486.westeurope.azurecontainer.io/score'
}

parser = argparse.ArgumentParser()
parser.add_argument('--endpoint', choices=list(endpoints.keys()), default='local')
parser.add_argument('input')
parser.add_argument('output')

args = parser.parse_args()


def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context


allowSelfSignedHttps(True)  # this line is needed if you use self-signed certificate in your scoring service.

image = Image.open(args.input)
(w, h) = image.size
print(w, h)

maxsize = 256 * 256
if w * h > maxsize:
    factor = sqrt(maxsize / (w * h))
    w = int(w * factor)
    h = int(h * factor)
    print(f'resizing to {(w, h)}')
    image = image.resize((w, h), Image.ANTIALIAS)

buffered = BytesIO()
image.save(buffered, format="JPEG")
img_str = base64.b64encode(buffered.getvalue())
# with open(sys.argv[1], "rb") as img_file:
# b64_image = base64.b64encode(img_file.read())
# Request data goes here
print(str(img_str)[:1000])
data = {
    'image': img_str.decode('utf-8')
}

body = str.encode(json.dumps(data))
print(body[:1000])

url = endpoints[args.endpoint]
api_key = ''  # Replace this with the API key for the web service
headers = {'Content-Type': 'application/json'}  #, 'Authorization': ('Bearer ' + api_key)}

# Temporary change to test local prediction.
if 0:
    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)

        result = json.loads(response.read())
        print(response.headers)
        print('Boxes', result['boxes'])
        print('Primers', result['primers'])
        with open(args.output, 'wb') as f:
            f.write(base64.b64decode(result['image']))
            
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))

else:
    import requests
    resp = requests.post(url, body, headers=headers)
    print(resp.headers)
    print(resp.text)
