import json
import sys
input = sys.argv[1]  # 'CartridgeOcr/src/data/dataset/coco.json'
output = sys.argv[2]  # 'CartridgeOcr/src/data/dataset/coco_xformed.json'
outpath = '../data/images/'

with open(input) as inF:
    annotations = json.load(inF)

for c in annotations['images']:
    c['coco_url'] = c['coco_url'].replace('AmlDatastore://', outpath)

for c in annotations['annotations']:
    c['iscrowd'] = 0

with open(output, 'w') as outF:
    json.dump(annotations, outF)
