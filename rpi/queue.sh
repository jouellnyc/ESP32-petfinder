#!/bin/bash

# Move the raw file one by one to the root of the webserver to a static file name that the esp32 is expecting

while [ 1 ] ; do 


	for FILE in $(ls -1 *raw); do 

            echo == $FILE ==
            cp $FILE /var/www/html/256.my_photo.jpg.raw 

            sleep 25 

        done


done
