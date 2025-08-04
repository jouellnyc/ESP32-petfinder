#!/usr/bin/env python3
"""
Utility to convert images to raw RGB565 format.

This script converts image files to RGB565 format (.raw files) suitable for 
embedded displays. It supports multiple input formats and provides various 
options for customizing the conversion process.

Features:
- Converts one or multiple images to RGB565 .raw files
- Comprehensive error handling with logging
- Progress tracking for multiple file operations
- Customizable output directory
- Overwrite protection with optional bypass
- Comprehensive test suite with edge cases
- Type-safe implementation with full type hints

Usage Examples:
    # Convert single image with default output name
    python3 5_img2rgb565.py input.png
    
    # Convert single image with custom output name
    python3 5_img2rgb565.py input.png output.raw
    
    # Convert multiple images
    python3 5_img2rgb565.py input1.png input2.jpg input3.bmp
    
    # Convert with custom output directory
    python3 5_img2rgb565.py --outdir ./converted input.png
    
    # Allow overwriting existing files
    python3 5_img2rgb565.py --overwrite input.png
    
    # Run comprehensive tests
    python3 5_img2rgb565.py --test
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from os import path
from pathlib import Path
from struct import pack
from typing import List, Tuple, Optional, BinaryIO

from PIL import Image

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

@dataclass
class RGB565Config:
    """Configuration constants for RGB565 conversion."""
    R_BITS: int = 5
    G_BITS: int = 6
    B_BITS: int = 5
    R_SHIFT: int = 11
    G_SHIFT: int = 5
    B_SHIFT: int = 0
    R_MASK: int = 0x1F  # 5 bits
    G_MASK: int = 0x3F  # 6 bits
    B_MASK: int = 0x1F  # 5 bits

# Global configuration instance
RGB565 = RGB565Config()

VALID_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

class ImageConversionError(Exception):
    """Custom exception for image conversion errors."""
    pass

class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def write_bin(f: BinaryIO, pixel_list: List[Tuple[int, int, int]]) -> None:
    """
    Save image in RGB565 format (big-endian).
    
    Args:
        f: Binary file object to write to
        pixel_list: List of RGB tuples (r, g, b) where each component is 0-255
        
    Raises:
        ImageConversionError: If pixel data is invalid
    """
    if not pixel_list:
        raise ImageConversionError("Empty pixel list provided")
        
    for i, pix in enumerate(pixel_list):
        if len(pix) != 3:
            raise ImageConversionError(f"Invalid pixel format at index {i}: expected RGB tuple, got {pix}")
        
        r, g, b = pix
        if not all(0 <= component <= 255 for component in (r, g, b)):
            raise ImageConversionError(f"Invalid pixel values at index {i}: RGB({r}, {g}, {b}) - values must be 0-255")
            
        # Convert 8-bit RGB to RGB565
        r_565 = (r >> (8 - RGB565.R_BITS)) & RGB565.R_MASK
        g_565 = (g >> (8 - RGB565.G_BITS)) & RGB565.G_MASK
        b_565 = (b >> (8 - RGB565.B_BITS)) & RGB565.B_MASK
        
        rgb565_value = (r_565 << RGB565.R_SHIFT) + (g_565 << RGB565.G_SHIFT) + (b_565 << RGB565.B_SHIFT)
        f.write(pack('>H', rgb565_value))

def is_valid_image_file(filepath: str) -> bool:
    """
    Check if the file has a valid image extension.
    
    Args:
        filepath: Path to the file to check
        
    Returns:
        True if file has a supported image extension, False otherwise
    """
    if not filepath:
        return False
    ext = path.splitext(filepath)[1].lower()
    return ext in VALID_IMAGE_EXTS

def validate_output_directory(output_dir: str) -> None:
    """
    Validate that output directory exists and is writable.
    
    Args:
        output_dir: Path to output directory
        
    Raises:
        FileValidationError: If directory doesn't exist or isn't writable
    """
    output_path = Path(output_dir)
    
    if not output_path.exists():
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created output directory: {output_dir}")
        except OSError as e:
            raise FileValidationError(f"Cannot create output directory '{output_dir}': {e}")
    
    if not output_path.is_dir():
        raise FileValidationError(f"Output path '{output_dir}' is not a directory")
        
    # Test write permissions by creating a temporary file
    test_file = output_path / '.write_test'
    try:
        test_file.touch()
        test_file.unlink()
    except OSError as e:
        raise FileValidationError(f"Output directory '{output_dir}' is not writable: {e}")

def check_file_overwrite(filepath: str, allow_overwrite: bool) -> None:
    """
    Check if file exists and handle overwrite logic.
    
    Args:
        filepath: Path to file to check
        allow_overwrite: Whether to allow overwriting existing files
        
    Raises:
        FileValidationError: If file exists and overwrite is not allowed
    """
    if path.exists(filepath) and not allow_overwrite:
        raise FileValidationError(f"Output file '{filepath}' already exists. Use --overwrite to replace it.")

def convert_img_to_rgb565(in_path: str, out_path: str, allow_overwrite: bool = False) -> None:
    """
    Convert a single image to RGB565 format and write to out_path.
    
    Args:
        in_path: Input image file path
        out_path: Output .raw file path
        allow_overwrite: Whether to allow overwriting existing output files
        
    Raises:
        FileValidationError: If input file doesn't exist or output file conflicts
        ImageConversionError: If image processing fails
    """
    # Validate input file
    if not path.exists(in_path):
        raise FileValidationError(f"Input file not found: {in_path}")
        
    if not is_valid_image_file(in_path):
        raise FileValidationError(f"Unsupported file type: {in_path}")
    
    # Check output file overwrite
    check_file_overwrite(out_path, allow_overwrite)
    
    try:
        # Load and convert image
        img = Image.open(in_path).convert('RGB')
        pixels = list(img.getdata())
        
        if not pixels:
            raise ImageConversionError(f"No pixel data found in image: {in_path}")
            
    except Exception as e:
        if isinstance(e, ImageConversionError):
            raise
        raise ImageConversionError(f"Failed to open/process image '{in_path}': {e}")
    
    try:
        # Write RGB565 data
        with open(out_path, 'wb') as f:
            write_bin(f, pixels)
            
    except Exception as e:
        # Clean up partial file on error
        if path.exists(out_path):
            try:
                os.unlink(out_path)
            except OSError:
                pass
        raise ImageConversionError(f"Failed to write output file '{out_path}': {e}")
    
    logging.info(f"Converted: {in_path} -> {out_path} ({img.width}x{img.height}, {len(pixels)} pixels)")

def create_progress_bar(iterable, desc: str = "Converting"):
    """Create progress bar if tqdm is available, otherwise return plain iterable."""
    if TQDM_AVAILABLE:
        return tqdm(iterable, desc=desc, unit="file")
    else:
        logging.info(f"{desc} {len(list(iterable))} files...")
        return iterable

def process_files(input_files: List[str], output_dir: Optional[str] = None, 
                 allow_overwrite: bool = False, custom_output: Optional[str] = None) -> None:
    """
    Process multiple image files for RGB565 conversion.
    
    Args:
        input_files: List of input image file paths
        output_dir: Optional output directory (default: same as input)
        allow_overwrite: Whether to allow overwriting existing files
        custom_output: Custom output filename for single file conversion
        
    Raises:
        FileValidationError: If file validation fails
        ImageConversionError: If image conversion fails
    """
    if not input_files:
        raise ValueError("No input files provided")
    
    # Validate input files first
    for in_path in input_files:
        if not path.exists(in_path):
            raise FileValidationError(f"Input file not found: {in_path}")
        if not is_valid_image_file(in_path):
            raise FileValidationError(f"Unsupported file type: {in_path}")
    
    # Handle single file with custom output
    if len(input_files) == 1 and custom_output:
        output_files = [custom_output]
        if output_dir:
            output_files = [path.join(output_dir, path.basename(custom_output))]
    else:
        # Generate output filenames
        output_files = []
        for in_path in input_files:
            base_name = path.basename(in_path)
            out_name = base_name + '.raw'
            
            if output_dir:
                out_path = path.join(output_dir, out_name)
            else:
                out_path = path.join(path.dirname(in_path), out_name)
            
            output_files.append(out_path)
    
    # Validate output directory if specified
    if output_dir:
        validate_output_directory(output_dir)
    
    # Process files with progress tracking
    file_pairs = list(zip(input_files, output_files))
    
    for in_path, out_path in create_progress_bar(file_pairs, "Converting images"):
        try:
            convert_img_to_rgb565(in_path, out_path, allow_overwrite)
        except (FileValidationError, ImageConversionError) as e:
            logging.error(f"Failed to convert {in_path}: {e}")
            raise

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Convert images to RGB565 format for embedded displays",
        epilog="""
Examples:
  %(prog)s image.png                           # Convert to image.png.raw
  %(prog)s image.png output.raw               # Convert with custom output name  
  %(prog)s img1.jpg img2.png img3.bmp         # Convert multiple images
  %(prog)s --outdir ./converted *.png         # Convert to specific directory
  %(prog)s --overwrite --outdir ./out *.jpg   # Allow overwriting existing files
  %(prog)s --test                             # Run comprehensive test suite
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'input_files',
        nargs='*',
        help='Input image files to convert'
    )
    
    parser.add_argument(
        '--outdir',
        type=str,
        help='Output directory for converted files (default: same as input)'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Allow overwriting existing output files'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run comprehensive test suite and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )
    
    return parser.parse_args()

def main() -> None:
    """
    Main entry point for the RGB565 conversion utility.
    
    Parses command-line arguments and orchestrates the conversion process.
    """
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # Handle test mode
    if args.test:
        try:
            test_rgb565_conversion()
            sys.exit(0)
        except Exception as e:
            logging.error(f"Test suite failed: {e}")
            sys.exit(1)
    
    # Validate input arguments
    if not args.input_files:
        logging.error("No input files specified. Use --help for usage information.")
        sys.exit(1)
    
    # Handle legacy mode: single input with .raw output
    custom_output = None
    input_files = args.input_files
    
    if len(args.input_files) == 2 and args.input_files[1].lower().endswith('.raw'):
        input_files = [args.input_files[0]]
        custom_output = args.input_files[1]
        logging.info("Legacy mode: treating second argument as custom output filename")
    
    try:
        # Process the files
        process_files(
            input_files=input_files,
            output_dir=args.outdir,
            allow_overwrite=args.overwrite,
            custom_output=custom_output
        )
        
        logging.info(f"Successfully converted {len(input_files)} file(s)")
        
    except (FileValidationError, ImageConversionError, ValueError) as e:
        logging.error(f"Conversion failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Conversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

def test_rgb565_conversion() -> None:
    """
    Comprehensive test suite for RGB565 conversion functionality.
    
    Tests include:
    - Basic color conversion correctness
    - Edge cases (black, white, max values)
    - Error handling for invalid inputs
    - Boundary value testing
    """
    import io
    import tempfile
    
    logging.info("Starting RGB565 conversion test suite...")
    
    # Test 1: Basic color conversion
    logging.info("Test 1: Basic RGB565 color conversion")
    pixels = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255), (0, 0, 0)]
    expected = [0xF800, 0x07E0, 0x001F, 0xFFFF, 0x0000]  # Red, Green, Blue, White, Black
    
    f = io.BytesIO()
    write_bin(f, pixels)
    result = [int.from_bytes(f.getvalue()[i:i+2], 'big') for i in range(0, 10, 2)]
    assert result == expected, f'Basic color test failed - Expected {expected}, got {result}'
    logging.info("✓ Basic color conversion test passed")
    
    # Test 2: Boundary values
    logging.info("Test 2: Boundary value testing")
    boundary_pixels = [
        (0, 0, 0),      # Minimum values
        (255, 255, 255), # Maximum values
        (128, 128, 128), # Mid-range values
        (248, 252, 248), # Values that should map to max in RGB565
        (7, 3, 7),      # Values that should map to minimum non-zero
    ]
    
    f = io.BytesIO()
    write_bin(f, boundary_pixels)
    boundary_result = [int.from_bytes(f.getvalue()[i:i+2], 'big') for i in range(0, len(boundary_pixels)*2, 2)]
    
    # Verify boundary conversions
    expected_boundary = [0x0000, 0xFFFF, 0x8410, 0xFFFF, 0x0000]
    assert boundary_result == expected_boundary, f'Boundary test failed - Expected {expected_boundary}, got {boundary_result}'
    logging.info("✓ Boundary value test passed")
    
    # Test 3: Error handling for invalid pixel data
    logging.info("Test 3: Error handling tests")
    
    # Test empty pixel list
    try:
        f = io.BytesIO()
        write_bin(f, [])
        assert False, "Should have raised ImageConversionError for empty pixel list"
    except ImageConversionError:
        logging.info("✓ Empty pixel list error handling passed")
    
    # Test invalid pixel format
    try:
        f = io.BytesIO()
        write_bin(f, [(255, 0)])  # Missing blue component
        assert False, "Should have raised ImageConversionError for invalid pixel format"
    except ImageConversionError:
        logging.info("✓ Invalid pixel format error handling passed")
    
    # Test out-of-range pixel values
    try:
        f = io.BytesIO()
        write_bin(f, [(256, 0, 0)])  # Red > 255
        assert False, "Should have raised ImageConversionError for out-of-range values"
    except ImageConversionError:
        logging.info("✓ Out-of-range pixel value error handling passed")
    
    try:
        f = io.BytesIO()
        write_bin(f, [(-1, 0, 0)])  # Negative value
        assert False, "Should have raised ImageConversionError for negative values"
    except ImageConversionError:
        logging.info("✓ Negative pixel value error handling passed")
    
    # Test 4: File validation functions
    logging.info("Test 4: File validation tests")
    
    # Test valid image extensions
    valid_files = ['test.jpg', 'test.png', 'test.bmp', 'test.gif', 'test.tiff', 'test.webp']
    for file in valid_files:
        assert is_valid_image_file(file), f"Should recognize {file} as valid image"
    
    # Test invalid extensions
    invalid_files = ['test.txt', 'test.pdf', 'test', 'test.mp4']
    for file in invalid_files:
        assert not is_valid_image_file(file), f"Should recognize {file} as invalid image"
    
    # Test empty filename
    assert not is_valid_image_file(''), "Should reject empty filename"
    logging.info("✓ File validation tests passed")
    
    # Test 5: Output directory validation
    logging.info("Test 5: Directory validation tests")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test valid directory
        validate_output_directory(temp_dir)  # Should not raise
        
        # Test directory creation
        new_dir = os.path.join(temp_dir, 'new_subdir')
        validate_output_directory(new_dir)  # Should create and validate
        assert os.path.exists(new_dir), "Should have created new directory"
        
    logging.info("✓ Directory validation tests passed")
    
    # Test 6: Precision and data integrity
    logging.info("Test 6: Data precision tests")
    
    # Test RGB565 precision loss is within expected bounds
    test_colors = [(123, 45, 67), (200, 150, 100), (50, 75, 200)]
    f = io.BytesIO()
    write_bin(f, test_colors)
    
    # Verify we can read back and the values are within expected precision loss
    raw_data = f.getvalue()
    assert len(raw_data) == len(test_colors) * 2, "Should produce 2 bytes per pixel"
    
    for i, (r, g, b) in enumerate(test_colors):
        rgb565_bytes = raw_data[i*2:(i+1)*2]
        rgb565_val = int.from_bytes(rgb565_bytes, 'big')
        
        # Extract components back
        r_back = ((rgb565_val >> RGB565.R_SHIFT) & RGB565.R_MASK) << (8 - RGB565.R_BITS)
        g_back = ((rgb565_val >> RGB565.G_SHIFT) & RGB565.G_MASK) << (8 - RGB565.G_BITS)
        b_back = ((rgb565_val >> RGB565.B_SHIFT) & RGB565.B_MASK) << (8 - RGB565.B_BITS)
        
        # Check precision loss is within expected bounds
        assert abs(r - r_back) <= 8, f"Red precision loss too high: {r} -> {r_back}"
        assert abs(g - g_back) <= 4, f"Green precision loss too high: {g} -> {g_back}"
        assert abs(b - b_back) <= 8, f"Blue precision loss too high: {b} -> {b_back}"
    
    logging.info("✓ Data precision tests passed")
    
    logging.info("🎉 All RGB565 conversion tests passed successfully!")

if __name__ == '__main__':
    main()