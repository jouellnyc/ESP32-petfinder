#!/bin/bash

# This script moves raw files to the webserver root directory under a static filename.
# It ensures the ESP32 device can access the expected file.

# Directory to monitor for raw files
SOURCE_DIR="."
DEST_FILE="/var/www/html/256.my_photo.jpg.raw"

# Infinite loop to process files
while true; do
    # Find raw files in the source directory
    for FILE in "$SOURCE_DIR"/*.raw; do
        # Check if any .raw files exist
        if [[ -f "$FILE" ]]; then
            echo "Processing file: $FILE"

            # Check if destination file is already in use
            if [[ -f "$DEST_FILE" ]]; then
                echo "Destination file $DEST_FILE exists, waiting..."
                sleep 5
            else
                # Copy file to destination
                cp "$FILE" "$DEST_FILE"
                echo "Copied $FILE to $DEST_FILE"

                # Wait for ESP32 to process the file
                sleep 25

                # Optionally, remove or archive the processed file
                # rm "$FILE"
                # mv "$FILE" /path/to/archive/
            fi
        else
            echo "No raw files found. Waiting..."
            sleep 5
        fi
    done

done
