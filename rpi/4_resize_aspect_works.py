#!/usr/bin/env python3

"""Resize the photos to fit the ILI9341 screen while maintaining aspect ratio."""

import sys
import os
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 4_resize_aspect_works.py <image_file> <basewidth>")
        sys.exit(1)

    file = sys.argv[1]
    if not sys.argv[2].isdigit():
        print("Error: <basewidth> must be a positive integer.")
        sys.exit(1)

    basewidth = int(sys.argv[2])
    new_file = f"{basewidth}.{file}"

    if os.path.exists(new_file):
        new_file = f"{basewidth}_resized.{file}"

    try:
        img = Image.open(file)
    except FileNotFoundError:
        print(f"Error: File '{file}' not found.")
        sys.exit(1)
    except IOError:
        print("Error: Unsupported file format or corrupted file.")
        sys.exit(1)
    
    # Aspect ratio calculation
    try:
        wpercent = (basewidth / float(img.size[0]))
    except ZeroDivisionError:
        print("Error: Image has zero width, cannot calculate aspect ratio.")
        sys.exit(1)
    except (ValueError, TypeError) as e:
        print(f"Error: Failed to calculate aspect ratio - {e}")
        sys.exit(1)
    
    # Height calculation
    try:
        hsize = int((float(img.size[1]) * float(wpercent)))
    except (ValueError, TypeError, OverflowError) as e:
        print(f"Error: Failed to calculate new height - {e}")
        sys.exit(1)
    
    # Image resizing
    try:
        img = img.resize((basewidth, hsize), Image.Resampling.LANCZOS)
    except (ValueError, MemoryError) as e:
        print(f"Error: Failed to resize image - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error during image resize - {e}")
        sys.exit(1)
    
    # Image saving
    try:
        img.save(new_file)
    except PermissionError:
        print(f"Error: Permission denied when saving to '{new_file}'.")
        sys.exit(1)
    except OSError as e:
        print(f"Error: Failed to save image to '{new_file}' - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error during image save - {e}")
        sys.exit(1)

    width, height = img.size
    logging.info(f"Resized image saved as: {new_file}")
    logging.info(f"Dimensions: {width} x {height}")

if __name__ == "__main__":
    main()