#!/bin/bash

# 319 seems to work reliably and fill the whole screen, 256 works well also
# Test in a loop here or just continue on from step #3

ILI3_ASPECT=319

for FILE in $(ls -1 *jp*g); do 

    echo == $FILE ==
    ./4_resize_aspect_works.py $FILE $ILI3_ASPECT
    SMFILE="${ILI3_ASPECT}.$FILE"

    ./5_img2rgb565.py $SMFILE

done
