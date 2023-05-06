import argparse
import requests
import logging
import os
import json

# TODO: upload should set the prediction status for the image correctly.

parser = argparse.ArgumentParser()
parser.add_argument('--collection_name', required=True)
parser.add_argument('--cookie', type=str, required=True)
parser.add_argument('--delete-existing', action='store_true', default=False)
parser.add_argument('--root-url', type=str, default="http://127.0.0.1:8080")
parser.add_argument('collection_folder')

args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

# Create the empty collection
base_url = f"{args.root_url}/api/v0/"
collections_url = base_url + "collections"
image_url = base_url + "images"
annotations_url = base_url + "annotations"
predictions_url = base_url + "predictions"

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
images_path = os.path.join(args.collection_folder, "images.json")
if not os.path.exists(images_path):
    logging.error("No images.json file found, skipping import")
else:
    with open(images_path, 'r', encoding='utf-8') as in_images:
        images = json.load(in_images)
    logging.info(f'Images: {len(images["images"])}')
    
for image in images['images']:
    if 'filename' in image['extra_data']:
        image_fn = image['extra_data']['filename']
    else:
        image_fn = f'{image["id"]}.jpg'

    image_id = None
    logging.info(f'Importing image {image["id"]} from {image_fn}. Extra data: {image["extra_data"]} Prediction status: {image["prediction_status"]}')
    with open(os.path.join(args.collection_folder, image_fn), "rb") as f:
        files = {"file":(image_fn, f, 'application-type')}
        mime = 'image/jpeg' if image_fn.lower().split('.')[-1] == 'jpg' else 'image/png'
        payload = {
            "collection_id": collection_id, 
            "mime_type": mime, 
            "predict": False,
            "extra_data": json.dumps(image['extra_data']),
            "prediction_status": json.dumps(image['prediction_status'])
        }

        image_result = requests.post(image_url, 
                                     headers={"Cookie": f"{args.cookie}"}, 
                                     files = files, data = payload)                                      
        if image_result.status_code != 201:
            raise Exception(f"Failed to upload image {image_fn}: {image_result.text}")
        logging.info(f'Uploaded image {image}: {image_result.json()}')
        image_id = image_result.json()['id']
    
    # 2. Upload predictions
    predictions_map = {}
    for p in image['predictions']:
        logging.info(f'Importing predictions {p}')        
        p['image_id'] = image_id
        for f in ['casing_box', 'primer_box']:
            p[f] = json.loads(p[f])
        orig_prediction_id = p['id']
        del p['id']
        prediction_result = requests.post(predictions_url, headers={"Cookie": f"{args.cookie}"}, json=p)
        
        if prediction_result.status_code != 201:
            raise Exception(f"Failed to create prediction: {prediction_result.text}")

        logging.info(f'Created prediction: {prediction_result.json()}')
        predictions_map[orig_prediction_id] = prediction_result.json()['id']


    # 3. Upload annotations
    for a in image['annotations']:
        logging.info(f'Importing annotation {a}')        
        a['image_id'] = image_id
        a['geometry'] = json.loads(a['geometry'])
        a['metadata_'] = json.loads(a['metadata_'])
        orig_prediction_id = a['prediction_id']
        assert(orig_prediction_id in predictions_map)
        new_prediction_id = predictions_map[orig_prediction_id]
        a['prediction_id'] = new_prediction_id
        del a['id']
        annotation_result = requests.post(annotations_url, headers={"Cookie": f"{args.cookie}"}, json=a)
        
        if annotation_result.status_code != 201:
            raise Exception(f"Failed to create annotation: {annotation_result.text}")

        logging.info(f'Created annotation: {annotation_result.json()}')

