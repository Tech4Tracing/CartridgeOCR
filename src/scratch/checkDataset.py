import json
import os
from collections import Counter 
import sys
from shutil import copyfile

anno_fn = sys.argv[1]  # '../data/labeldata/coco_xformed.json'
print(anno_fn)
with open(anno_fn, 'r', encoding='utf-8') as inF:
    annotations = json.load(inF)

data_path = '../data/dataset'
files = os.listdir(data_path)

images = dict([(a['id'], a['file_name']) for a in annotations['images']])
# print(images.keys())
annotated = set([images[a['image_id']] for a in annotations['annotations']])
in_dataset = set(images.values())


#print(annotated)
ds1_path = '../data/dataset_annotated'
os.makedirs(ds1_path)
ds2_path = '../data/dataset_to_annotate'
os.makedirs(ds2_path)
ctr = Counter()
for f in files:
    if f in annotated:
        copyfile(os.path.join(data_path, f), os.path.join(ds1_path, f))
    else:
        copyfile(os.path.join(data_path, f), os.path.join(ds2_path, f))

    if f not in annotated:
        # print("not annotated: ",f)
        ctr['not annotated'] += 1
    if f not in in_dataset:
        # print('not in dataset ', f)
        ctr['not in dataset'] += 1

for i in in_dataset:
    if i not in files:
        # print('cant find i')
        ctr['not in files'] += 1


print('images', len(images))
print('files', len(files))
print('annotated', len(annotated))
print('not annotated', ctr['not annotated'])
print('not in dataset', ctr['not in dataset'])
print('not in files', ctr['not in files'])
