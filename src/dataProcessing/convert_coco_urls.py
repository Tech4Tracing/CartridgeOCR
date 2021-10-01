import json

with open('CartridgeOcr/src/data/dataset/coco.json') as inF:
    annotations = json.load(inF)

for c in annotations['images']:
    c['coco_url'] = c['coco_url'].replace('AmlDatastore://','../data/images/')

for c in annotations['annotations']:
    c['iscrowd']=0

with open('CartridgeOcr/src/data/dataset/coco_xformed.json', 'w') as outF:
    json.dump(annotations, outF)