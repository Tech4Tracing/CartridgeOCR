
import argparse
import requests
import os
import json

parser = argparse.ArgumentParser()

# TODO: if we don't specify a collection id we should export individual collections and enable re-importing them

parser.add_argument('--collection_id', type=str, default=None, required=False)
parser.add_argument('output_folder', type=str)
parser.add_argument('--overwrite', action='store_true', default=False, required=False)
parser.add_argument('--cookie', type=str, required=True)
parser.add_argument('--endpoint', type=str, default="http://127.0.0.1:8080", required=False)

args = parser.parse_args()

os.makedirs(args.output_folder, exist_ok=args.overwrite)

# Get annotations from the backend
# http://127.0.0.1:8080/api/v0/annotations
root = f"{args.endpoint.rstrip('/')}/api/v0"

images_url = f"{root}/images"
if args.collection_id:
    images_url += f"?collection_id={args.collection_id}"
imagelist = requests.get(images_url, headers={"Cookie": f"{args.cookie}"})   
if imagelist.status_code != 200:
    raise Exception(f"Failed to get images: {imagelist.text}")

with open(args.output_folder + "/images.json", "w") as f:
    json.dump(imagelist.json(), f)

for i in imagelist.json()["images"]:
    url = f"{args.endpoint.rstrip('/')}/api/v0/images/{i['id']}/binary"
    image = requests.get(url, headers={"Cookie": f"{args.cookie}"})
    if image.status_code != 200:
        raise Exception(f"Failed to get image {i}: {image.text}")
    else:
        # TODO: we can't assume this will always be a jpg image.
        image_fn = (list(filter(i['notes'], lambda n: n['note_key']=='filename')) 
                    or [{'note_value':None}])[0]['note_value']
        if not image_fn:
            image_fn = f"{i['id']}.jpg"
        with open(os.path.join(args.output_folder, image_fn), "wb") as f:
            f.write(image.content)

