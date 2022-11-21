#!/bin/bash

while [ 1 ] ; do 


	for FILE in $(ls -1 *raw); do 

            echo == $FILE ==
            cp $FILE /var/www/html/256.my_photo.jpg.raw 

            sleep 25 

        done


done
