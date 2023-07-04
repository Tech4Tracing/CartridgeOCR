import argparse
import requests
import logging
import os
import json
import csv

# TODO: upload should set the prediction status for the image correctly.

parser = argparse.ArgumentParser()
parser.add_argument('--collection_name', required=True)
parser.add_argument('--cookie', type=str, required=True)
parser.add_argument('--delete-existing', action='store_true', default=False)
parser.add_argument('--root-url', type=str, default="http://127.0.0.1:8080")
parser.add_argument('--source', type=str, required=True)
parser.add_argument('data_path')

args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

# Create the empty collection
base_url = f"{args.root_url}/api/v0/"
collections_url = base_url + "collections"
image_url = base_url + "images"
annotations_url = base_url + "annotations"
predictions_url = base_url + "predictions"
ammunition_url = base_url + "ammunition"

def uploadImage(image_fn, collection_id):
    with open(image_fn, "rb") as f:
        files = {"file":(image_fn, f, 'application-type')}
        mime = 'image/jpeg' if image_fn.lower().split('.')[-1] == 'jpg' else 'image/png'
        payload = {
            "collection_id": collection_id, 
            "mime_type": mime, 
            "extra_data": json.dumps({"filename": os.path.basename(image_fn)}),
            "predict": False,            
        }

        image_result = requests.post(image_url, 
                                    headers={"Cookie": f"{args.cookie}"}, 
                                    files = files, data = payload)                                      
        if image_result.status_code != 201:
            raise Exception(f"Failed to upload image {image_fn}: {image_result.text}")
        logging.info(f'Uploaded image {image_fn}: {image_result.json()}')
        image_id = image_result.json()['id']
        return image_id


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
            
            # remove the ammunition records too
            ammunition = requests.get(ammunition_url, headers={"Cookie": f"{args.cookie}"})
            if ammunition.status_code != 200:
                raise Exception(f"Failed to get ammunition: {ammunition.text}")
            for a in ammunition.json()["ammunitions"]:
                logging.info(f"Deleting ammunition {a['id']}")
                r = requests.delete(ammunition_url + f"/{a['id']}", headers={"Cookie": f"{args.cookie}"})
                if r.status_code != 204:
                    raise Exception(f"Failed to delete ammunition {a['id']}: {r.text}")

        else:
            raise Exception(f"Collection {args.collection_name} already exists")

collection_result = requests.post(collections_url, headers={"Cookie": f"{args.cookie}"}, json={"name": args.collection_name})

if collection_result.status_code != 201:
    raise Exception(f"Failed to create collection: {collection_result.text}")

logging.info(f'Created collection: {collection_result.json()}')
collection_id = collection_result.json()["id"]

# make the collection public
userscopes_url = f"{collections_url}/{collection_id}/userscopes"
user_result = requests.patch(userscopes_url, headers={"Cookie": f"{args.cookie}"}, json={"user_email": "public@tech4tracing.org", "access_level": "read"})
if user_result.status_code != 201:
    raise Exception(f"Failed to make collection public: {user_result.text}")

# Load the data and start uploading images and records
data_csv = os.path.join(args.data_path, "cartrology-vf.csv")  
data_images = os.path.join(args.data_path, "images/images") 
n = 0
with open(data_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    # item_id,caliber,item_id,cartridge_type,case_material,country,headstamp,
    # projectile,case_desc,primer,notes,data_id,projectile_markings,fn_im_headstamp,fn_im_shell
    rows = [row for row in reader]
    for row in rows:
        hs_image = os.path.join(data_images, row['fn_im_headstamp'])
        shell_image = os.path.join(data_images, row['fn_im_shell'])   
        assert(os.path.exists(hs_image))
        assert(os.path.exists(shell_image))
        hs_image_id = uploadImage(hs_image, collection_id)
        shell_image_id = uploadImage(shell_image, collection_id)    
        print(hs_image_id, shell_image_id)
        #print(row)
        # build the ammunition record

        ammunition = {
            'caliber': row['caliber'],
            'cartridge_type': row['cartridge_type'],
            'casing_material': row['case_material'],
            'country': row['country'],
            # manufacturer
            # year_start
            # year_end
            # TODO: projectile_band_markings, projectile_markings
            'headstamp_markings': row['headstamp'],
            'projectile': row['projectile_desc'],            
            'casing_description': row['case_desc'],
            'primer': row['primer'],
            'data_source': args.source,
            'notes': json.dumps({
                'orig_notes':row['notes'],
                'projectile_markings':row['projectile_markings'], 
                'projectile_band_markings':row['projectile_band_markings']}),
            'reference_collection': collection_id,
            'headstamp_image': hs_image_id,
            'profile_image': shell_image_id
             
        }
        ammunition_result = requests.post(ammunition_url, headers={"Cookie": f"{args.cookie}"}, json=ammunition)
        if ammunition_result.status_code != 201:
            raise Exception(f"Failed to upload ammunition : {ammunition_result.text}")
        logging.info(f'Uploaded ammunition: {ammunition_result.json()["id"]}')
        n+=1
        if n==20:
            break