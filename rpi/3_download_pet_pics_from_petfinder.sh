#!/bin/bash

# Iterate through the crawl list and download the pet pics

# Fail if pets.wget.queue.txt does not exist
if [ ! -f pets.wget.queue.txt ]; then
    echo "Error: pets.wget.queue.txt not found"
    exit 1
fi

while IFS=':' read -r name pic
do 
    # Only download if file does not already exist
    if [ ! -f "${name}.jpg" ]; then
        wget -O "${name}.jpg" "$pic" && \
        echo "Downloaded ${name}.jpg" >> success.log || \
        echo "Failed to download ${name}.jpg from $pic" >> error.log
    else
        echo "Skipped ${name}.jpg, file already exists." >> skipped.log
    fi
    sleep 1 
done < pets.wget.queue.txt
