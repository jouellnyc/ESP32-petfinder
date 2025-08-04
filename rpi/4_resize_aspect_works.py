#!/usr/bin/env python3

"""
Resize the photos to fit the ILI9341 screen while maintaining aspect ratio.
This script resizes an image to a specified width while maintaining its aspect ratio.

Usage:
    python3 4_resize_aspect_works.py <image_file> <basewidth>

Arguments:
    <image_file> : Path to the image file to resize.
    <basewidth>  : The desired width for the resized image (must be a positive integer).
"""

import sys
import os
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)

def validate_input(args):
    if len(args) != 3:
        logging.error("Usage: python3 4_resize_aspect_works.py <image_file> <basewidth>")
        sys.exit(1)
    if not args[2].isdigit() or int(args[2]) <= 0:
        logging.error("Error: <basewidth> must be a positive integer.")
        sys.exit(1)
    return args[1], int(args[2])

def open_image(file):
    try:
        return Image.open(file)
    except FileNotFoundError:
        logging.error(f"Error: File '{file}' not found.")
        sys.exit(1)
    except IOError:
        logging.error("Error: Unsupported file format or corrupted file.")
        sys.exit(1)

def resize_image(img, basewidth):
    try:
        wpercent = basewidth / float(img.size[0])
        hsize = int(float(img.size[1]) * wpercent)
        resized_img = img.resize((basewidth, hsize), Image.Resampling.LANCZOS)
        return resized_img
    except Exception as e:
        logging.error(f"Unexpected error during resizing: {e}")
        sys.exit(1)

def save_image(img, file, basewidth):
    new_file = f"{basewidth}_{os.path.basename(file)}"
    try:
        img.save(new_file)
        return new_file
    except Exception as e:
        logging.error(f"Unexpected error during save: {e}")
        sys.exit(1)

def main():
    file, basewidth = validate_input(sys.argv)
    img = open_image(file)
    
    logging.info(f"Original Dimensions: {img.size[0]} x {img.size[1]}")
    resized_img = resize_image(img, basewidth)
    new_file = save_image(resized_img, file, basewidth)
    
    logging.info(f"Resized image saved as: {new_file}")
    logging.info(f"New Dimensions: {resized_img.size[0]} x {resized_img.size[1]}")

if __name__ == "__main__":
    main()