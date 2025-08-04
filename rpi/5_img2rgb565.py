#!/usr/bin/env python3
"""
Utility to convert images to raw RGB565 format.

Features:
- Converts one or multiple images to RGB565 .raw files.
- Adds detailed comments, type hints, and improved error handling.
- Allows output file path customization via optional CLI argument.
- Enhanced user feedback and robust file validation.
- Refactored for testability and maintainability.

Usage:
    python3 5_img2rgb565.py input.png [output.raw]
    python3 5_img2rgb565.py input1.png input2.jpg [...]
"""

from PIL import Image
from struct import pack
from os import path
import sys
from typing import List, Tuple

# Constants for RGB565 conversion
_R_BITS = 5
_G_BITS = 6
_B_BITS = 5
_R_SHIFT = 11
_G_SHIFT = 5
_B_SHIFT = 0

VALID_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}

def error(msg: str) -> None:
    """Display error and exit."""
    print(f"Error: {msg}")
    sys.exit(-1)

def write_bin(f, pixel_list: List[Tuple[int, int, int]]) -> None:
    """Save image in RGB565 format (big-endian)."""
    for pix in pixel_list:
        r = (pix[0] >> 3) & 0x1F  # 5 bits
        g = (pix[1] >> 2) & 0x3F  # 6 bits
        b = (pix[2] >> 3) & 0x1F  # 5 bits
        f.write(pack('>H', (r << _R_SHIFT) + (g << _G_SHIFT) + (b << _B_SHIFT)))

def is_valid_image_file(filepath: str) -> bool:
    """Check if the file has a valid image extension."""
    ext = path.splitext(filepath)[1].lower()
    return ext in VALID_IMAGE_EXTS

def convert_img_to_rgb565(in_path: str, out_path: str) -> None:
    """
    Convert a single image to RGB565 format and write to out_path.
    Args:
        in_path: input image file path
        out_path: output .raw file path
    """
    try:
        img = Image.open(in_path).convert('RGB')
        pixels = list(img.getdata())
    except Exception as e:
        error(f'Failed to open/process image {in_path}: {e}')
    try:
        with open(out_path, 'wb') as f:
            write_bin(f, pixels)
    except Exception as e:
        error(f'Failed to write output file {out_path}: {e}')
    print(f'Saved: {out_path} ({img.width}x{img.height}, {len(pixels)} pixels)')

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    # If last argument is a .raw file, treat it as the output for single input
    if len(args) == 2 and args[1].lower().endswith('.raw'):
        in_files = [args[0]]
        out_files = [args[1]]
    else:
        in_files = args
        out_files = []

    for in_path in in_files:
        if not path.exists(in_path):
            error(f'File Not Found: {in_path}')
        if not is_valid_image_file(in_path):
            error(f'Unsupported file type: {in_path}')
        filename, ext = path.splitext(in_path)
        out_path = filename + ext + '.raw'
        out_files.append(out_path)

    # Process all images
    for in_path, out_path in zip(in_files, out_files):
        convert_img_to_rgb565(in_path, out_path)

def test_rgb565_conversion():
    """Basic test for RGB565 conversion correctness."""
    import io
    # Red, Green, Blue, White, Black
    pixels = [(255,0,0), (0,255,0), (0,0,255), (255,255,255), (0,0,0)]
    expected = [0xF800, 0x07E0, 0x001F, 0xFFFF, 0x0000]
    f = io.BytesIO()
    write_bin(f, pixels)
    result = [int.from_bytes(f.getvalue()[i:i+2], 'big') for i in range(0, 10, 2)]
    assert result == expected, f'Expected {expected}, got {result}'
    print('Test passed: RGB565 conversion.')

if __name__ == '__main__':
    # Run test if requested
    if '--test' in sys.argv:
        test_rgb565_conversion()
    else:
        main()