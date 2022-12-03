import argparse
import requests
import logging
import os
import json

parser = argparse.ArgumentParser()
parser.add_argument('--collection_name', required=True)
parser.add_argument('--cookie', type=str, required=True)
parser.add_argument('--delete-existing', action='store_true', default=False)
parser.add_argument('collection_folder')

args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

# Create the empty collection
base_url = "http://127.0.0.1:8080/api/v0/"
collections_url = base_url + "collections"
image_url = base_url + "images"
annotations_url = base_url + "annotations"

# check for existence first
collections = requests.get(collections_url, headers={"Cookie": f"{args.cookie}"})
if collections.status_code != 200:
    raise Exception(f"Failed to get collections: {collections.text}")
for c in collections.json()["collections"]:
    if c["name"] == args.collection_name:
        if args.delete_existing:
            logging.info(f"Deleting existing collection {c['id']}")
            images = requests.get(image_url, params={'collection_id': c['id']}, headers={"Cookie": f"{args.cookie}"})
            if images.status_code != 200:
                raise Exception(f"Failed to get images: {images.text}")
            for i in images.json()["images"]:
                logging.info(f"Deleting image {i['id']}")
                r = requests.delete(image_url + f"/{i['id']}", headers={"Cookie": f"{args.cookie}"})
                if r.status_code != 204:
                    raise Exception(f"Failed to delete image {i['id']}: {r.text}")
            r = requests.delete(f"{collections_url}/{c['id']}", headers={"Cookie": f"{args.cookie}"})
            if r.status_code != 204:
                raise Exception(f"Failed to delete collection {c['id']}: {r.text}")
        else:
            raise Exception(f"Collection {args.collection_name} already exists")

collection_result = requests.post(collections_url, headers={"Cookie": f"{args.cookie}"}, json={"name": args.collection_name})

if collection_result.status_code != 201:
    raise Exception(f"Failed to create collection: {collection_result.text}")

logging.info(f'Created collection: {collection_result.json()}')
collection_id = collection_result.json()["id"]

# upload the images
images = filter(lambda x: x.lower().endswith(".jpg"), os.listdir(args.collection_folder))
image_map = {}
for image in images:
    with open(os.path.join(args.collection_folder, image), "rb") as f:
        files = {"file":(image, f, 'application-type')}
        payload = {"collection_id": collection_id, "mime_type": "image/jpeg"}

        image_result = requests.post(image_url, headers={"Cookie": f"{args.cookie}"}, 
                                     files = files, data = payload)                                      
        if image_result.status_code != 201:
            raise Exception(f"Failed to upload image {image}: {image_result.text}")
        logging.info(f'Uploaded image {image}: {image_result.json()}')
        image_map[image] = image_result.json()['id']

# upload the annotations
with open(os.path.join(args.collection_folder,"annotations.json"), 'r', encoding='utf-8') as in_annot:
    annotations = json.load(in_annot)
logging.info(f'Annotations: {annotations.keys()}')
for a in annotations['annotations']:
    logging.info(f'Importing annotation {a}')
    orig_image_id = a['image_id']
    new_image_id = image_map[f'{orig_image_id}.jpg']
    a['image_id'] = new_image_id
    a['geometry'] = json.loads(a['geometry'])
    a['metadata_'] = json.loads(a['metadata_'])
    del a['id']
    annotation_result = requests.post(annotations_url, headers={"Cookie": f"{args.cookie}"}, json=a)
    
    if annotation_result.status_code != 201:
        raise Exception(f"Failed to create annotation: {annotation_result.text}")

    logging.info(f'Created annotation: {annotation_result.json()}')
