#!/bin/bash

# pfinder.poc.sh - Batch resize and convert images for ESP32 pet display
# Usage: ./pfinder.poc.sh [ASPECT_RATIO]
# ASPECT_RATIO (ILI3_ASPECT) is optional and defaults to 319

# Set aspect ratio, allow override as argument
ILI3_ASPECT=${1:-319}

# Optional: Enable logging (uncomment to use)
# exec > >(tee -i pfinder_poc.log)
# exec 2>&1

# Check required Python scripts exist and are executable
if [ ! -x ./4_resize_aspect_works.py ]; then
    echo "Error: ./4_resize_aspect_works.py not found or not executable." >&2
    exit 1
fi
if [ ! -x ./5_img2rgb565.py ]; then
    echo "Error: ./5_img2rgb565.py not found or not executable." >&2
    exit 1
fi

shopt -s nullglob
for FILE in *jp*g; do
    if [ ! -f "$FILE" ]; then
        echo "No matching image files found."
        break
    fi

    echo "== Processing: $FILE =="
    ./4_resize_aspect_works.py "$FILE" "$ILI3_ASPECT"
    if [ $? -ne 0 ]; then
        echo "Error resizing $FILE" >&2
        continue
    fi

    RESIZED_FILE="${ILI3_ASPECT}.$FILE"
    ./5_img2rgb565.py "$RESIZED_FILE"
    if [ $? -ne 0 ]; then
        echo "Error processing $RESIZED_FILE" >&2
        continue
    fi

done
shopt -u nullglob
