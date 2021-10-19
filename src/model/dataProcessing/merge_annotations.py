import sys
import json

output = {}
for arg in sys.argv[1:-1]:
    o = json.load(open(arg, 'r'))
    for k in o:
        if k not in output:
            output[k] = o[k]
        elif k != 'categories':
            output[k] += o[k]

with open(sys.argv[-1], 'w', encoding='utf-8') as outF:
    outF.write(json.dumps(output))

print(f"images: {len(output['images'])}")
print(f"annotations: {len(output['annotations'])}")