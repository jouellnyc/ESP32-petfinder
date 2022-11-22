#!/bin/bash

""" Iterate throught the crawl list and download the pet pics """

while IFS=':' read -r name pic

do 

    wget -O "${name}.jpg" "$pic"

    sleep 1 
 
done <  pets.wget.queue.txt
