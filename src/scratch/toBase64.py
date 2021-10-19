import base64
import sys
with open(sys.argv[1], "rb") as img_file:
    my_string = base64.b64encode(img_file.read())
print(my_string)
