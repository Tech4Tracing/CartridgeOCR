import base64
import sys
with open(sys.argv[1], 'r') as in_file:
    with open(sys.argv[2], "wb") as img_file:
        img_bytes = base64.b64decode(in_file.read())
        img_file.write(img_bytes)
        
