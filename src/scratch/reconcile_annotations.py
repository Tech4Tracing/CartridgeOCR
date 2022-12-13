import sys
import os

src, dest = sys.argv[1:3]

src_files = os.listdir(src)
dst_files = os.listdir(dest)

src_sizes = {}

for f in src_files:
    sz = os.path.getsize(os.path.join(src, f))
    src_sizes[sz] = f

for f in dst_files:
    sz = os.path.getsize(os.path.join(dest, f))
    if sz in src_sizes:
        print(f"{src_sizes[sz]} {f}")
    else:
        print(f"Missing {f}")