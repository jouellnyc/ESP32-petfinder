#!/bin/bash

while IFS=':' read -r name pic

do 

    wget -O "${name}.jpg" "$pic"

    sleep 1 
 
done <  pets.wget.queue.txt
