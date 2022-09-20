
import argparse
import requests
import os
import json

parser = argparse.ArgumentParser()

parser.add_argument('--collection_id', type=str, default=None, required=False)
parser.add_argument('output_folder', type=str)
parser.add_argument('--overwrite', action='store_true', default=False, required=False)
parser.add_argument('--cookie', type=str, required=True)

args = parser.parse_args()

os.makedirs(args.output_folder, exist_ok=args.overwrite)

# Get annotations from the backend
# http://127.0.0.1:8080/api/v0/annotations

url = "http://127.0.0.1:8080/api/v0/annotations"
if args.collection_id:
    url += f"?collection_id={args.collection_id}"

annotations = requests.get(url, headers={"Cookie": f"{args.cookie}"})
if annotations.status_code != 200:
    raise Exception(f"Failed to get annotations: {annotations.text}")

o = annotations.json()
with open(args.output_folder + "/annotations.json", "w") as f:
    json.dump(o, f)

images = set()
for a in o["annotations"]:
    images.add(a["image_id"])

print(f"Found {len(o['annotations'])} annotations for {len(images)} images")

for i in images:
    url = f"http://127.0.0.1:8080/api/v0/images/{i}/binary"
    image = requests.get(url, headers={"Cookie": f"{args.cookie}"})
    if image.status_code != 200:
        raise Exception(f"Failed to get image {i}: {image.text}")
    else:
        with open(args.output_folder + f"/{i}.jpg", "wb") as f:
            f.write(image.content)
