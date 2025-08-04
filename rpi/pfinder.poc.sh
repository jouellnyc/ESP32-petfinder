#!/bin/bash

# pfinder.poc.sh - Batch resize and convert images for ESP32 pet display
# Usage: ./pfinder.poc.sh [ASPECT_RATIO]
# ASPECT_RATIO (ILI3_ASPECT) is optional and defaults to 319
#
# Improvements:
# 1. Robust error handling and exit codes
# 2. Optional logging and --help flag
# 3. Input validation for aspect ratio
# 4. Dependency checks for python3 and scripts
# 5. Better comments and variable naming

set -euo pipefail

show_help() {
    echo "Usage: $0 [ASPECT_RATIO]"
    echo "Batch resize and convert images for ESP32 pet display."
    echo "  ASPECT_RATIO (ILI3_ASPECT) is optional and defaults to 319."
    echo "  --help        Show this help message and exit."
}

# Parse arguments
if [[ "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

# Set aspect ratio, allow override as argument (must be numeric)
if [[ -n "${1:-}" ]]; then
    if ! [[ "$1" =~ ^[0-9]+$ ]]; then
        echo "Error: Aspect ratio must be a positive integer." >&2
        exit 2
    fi
    ILI3_ASPECT="$1"
else
    ILI3_ASPECT=319
fi

# Optional: Enable logging (uncomment to use)
# exec > >(tee -i pfinder_poc.log)
# exec 2>&1

# Dependency checks
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is not installed. Please install it." >&2
    exit 3
fi

if [ ! -x ./4_resize_aspect_works.py ]; then
    echo "Error: ./4_resize_aspect_works.py not found or not executable. Try: chmod +x 4_resize_aspect_works.py" >&2
    exit 4
fi
if [ ! -x ./5_img2rgb565.py ]; then
    echo "Error: ./5_img2rgb565.py not found or not executable. Try: chmod +x 5_img2rgb565.py" >&2
    exit 5
fi

shopt -s nullglob
IMG_FOUND=false
for IMAGE_FILE in *jp*g; do
    if [ ! -f "$IMAGE_FILE" ]; then
        continue
    fi
    IMG_FOUND=true
    echo "== Processing: $IMAGE_FILE =="
    if ! ./4_resize_aspect_works.py "$IMAGE_FILE" "$ILI3_ASPECT"; then
        echo "Error resizing $IMAGE_FILE" >&2
        continue
    fi
    RESIZED_IMAGE="${ILI3_ASPECT}.$IMAGE_FILE"
    if ! ./5_img2rgb565.py "$RESIZED_IMAGE"; then
        echo "Error processing $RESIZED_IMAGE" >&2
        continue
    fi

done
shopt -u nullglob

if ! $IMG_FOUND; then
    echo "No matching image files found."
    exit 6
fi

exit 0
