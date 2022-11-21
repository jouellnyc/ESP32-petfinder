#!/usr/bin/env python3

import sys

from PIL import Image

file = sys.argv[1]
basewidth = int(sys.argv[2])
new_file=f"{basewidth}.{sys.argv[1]}"

try:
    img = Image.open(file)
except Exception as e:
    print(e)

wpercent = (basewidth/float(img.size[0]))
hsize = int((float(img.size[1])*float(wpercent)))
img = img.resize((basewidth,hsize), Image.Resampling.LANCZOS)
img.save(new_file)

width, height = img.size
print(f"{new_file} is {width} x {height}")

with open('/var/www/html/filesize.txt','w') as fh:
    fh.write(f"{width}:{height}")
