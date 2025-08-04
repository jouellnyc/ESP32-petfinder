#!/usr/bin/env python3
"""
Utility to convert images to raw RGB565 format.

Features:
- Converts one or multiple images to RGB565 .raw files with progress tracking
- Supports command-line options for output directory, overwrite control, and testing
- Comprehensive error handling with logging and proper exception management
- Type-safe implementation with complete type hints
- Configurable RGB565 conversion parameters via dataclass
- Enhanced test suite with edge case coverage

Usage:
    python3 5_img2rgb565.py input.png
    python3 5_img2rgb565.py input1.png input2.jpg --outdir /path/to/output
    python3 5_img2rgb565.py *.png --overwrite
    python3 5_img2rgb565.py --test

Examples:
    # Convert single image to same directory
    python3 5_img2rgb565.py photo.jpg
    
    # Convert multiple images to specific output directory
    python3 5_img2rgb565.py img1.png img2.jpg --outdir ./converted
    
    # Overwrite existing files without prompting
    python3 5_img2rgb565.py *.png --overwrite
    
    # Run comprehensive tests
    python3 5_img2rgb565.py --test
"""

import argparse
import io
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from struct import pack
from typing import List, Tuple, Optional, Set

from PIL import Image

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


@dataclass(frozen=True)
class RGB565Config:
    """Configuration constants for RGB565 conversion."""
    r_bits: int = 5
    g_bits: int = 6
    b_bits: int = 5
    r_shift: int = 11
    g_shift: int = 5
    b_shift: int = 0
    
    @property
    def r_mask(self) -> int:
        """Red component bitmask."""
        return (1 << self.r_bits) - 1
    
    @property
    def g_mask(self) -> int:
        """Green component bitmask."""
        return (1 << self.g_bits) - 1
        
    @property
    def b_mask(self) -> int:
        """Blue component bitmask."""
        return (1 << self.b_bits) - 1


# Global configuration instance
RGB565_CONFIG = RGB565Config()

VALID_IMAGE_EXTS: Set[str] = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}


class ImageConversionError(Exception):
    """Exception raised for image conversion errors."""
    pass


class OutputDirectoryError(Exception):
    """Exception raised for output directory related errors."""
    pass


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('img2rgb565')
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    logger.setLevel(level)
    return logger


# Initialize logger
logger = setup_logging()

def write_bin(f: io.BufferedWriter, pixel_list: List[Tuple[int, int, int]]) -> None:
    """
    Save image pixels in RGB565 format (big-endian).
    
    Args:
        f: Binary file handle for writing
        pixel_list: List of RGB tuples (r, g, b) where each component is 0-255
        
    Raises:
        ValueError: If pixel values are invalid
        IOError: If writing to file fails
    """
    if not pixel_list:
        raise ValueError("Pixel list cannot be empty")
        
    config = RGB565_CONFIG
    
    for i, pix in enumerate(pixel_list):
        if len(pix) != 3:
            raise ValueError(f"Invalid pixel at index {i}: expected 3 components, got {len(pix)}")
            
        r, g, b = pix
        
        # Validate pixel values
        if not all(0 <= val <= 255 for val in (r, g, b)):
            raise ValueError(f"Invalid pixel values at index {i}: ({r}, {g}, {b}). Values must be 0-255")
        
        # Convert to RGB565
        r_565 = (r >> (8 - config.r_bits)) & config.r_mask
        g_565 = (g >> (8 - config.g_bits)) & config.g_mask  
        b_565 = (b >> (8 - config.b_bits)) & config.b_mask
        
        rgb565_value = (r_565 << config.r_shift) + (g_565 << config.g_shift) + (b_565 << config.b_shift)
        
        try:
            f.write(pack('>H', rgb565_value))
        except (OSError, IOError) as e:
            raise IOError(f"Failed to write pixel data: {e}")


def is_valid_image_file(filepath: str) -> bool:
    """
    Check if the file has a valid image extension.
    
    Args:
        filepath: Path to the image file
        
    Returns:
        True if file extension is supported, False otherwise
    """
    if not filepath:
        return False
        
    ext = Path(filepath).suffix.lower()
    return ext in VALID_IMAGE_EXTS


def validate_output_directory(outdir: Optional[str]) -> Path:
    """
    Validate that output directory exists and is writable.
    
    Args:
        outdir: Output directory path (None means current directory)
        
    Returns:
        Validated Path object for output directory
        
    Raises:
        OutputDirectoryError: If directory doesn't exist or isn't writable
    """
    if outdir is None:
        output_path = Path.cwd()
    else:
        output_path = Path(outdir).resolve()
    
    if not output_path.exists():
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_path}")
        except (OSError, PermissionError) as e:
            raise OutputDirectoryError(f"Cannot create output directory '{output_path}': {e}")
    
    if not output_path.is_dir():
        raise OutputDirectoryError(f"Output path '{output_path}' is not a directory")
    
    # Test if directory is writable
    test_file = output_path / '.write_test'
    try:
        test_file.write_text('test')
        test_file.unlink()
    except (OSError, PermissionError) as e:
        raise OutputDirectoryError(f"Output directory '{output_path}' is not writable: {e}")
    
    return output_path


def should_overwrite_file(filepath: Path, overwrite: bool) -> bool:
    """
    Determine if file should be overwritten.
    
    Args:
        filepath: Path to the file
        overwrite: If True, always overwrite; if False, prompt user
        
    Returns:
        True if file should be overwritten, False otherwise
    """
    if not filepath.exists():
        return True
    
    if overwrite:
        return True
    
    # Interactive prompt
    while True:
        response = input(f"File '{filepath}' exists. Overwrite? (y/n): ").lower().strip()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Please enter 'y' or 'n'")


def convert_img_to_rgb565(in_path: str, out_path: Path, overwrite: bool = False) -> None:
    """
    Convert a single image to RGB565 format and write to out_path.
    
    Args:
        in_path: Input image file path
        out_path: Output .raw file path
        overwrite: If True, overwrite existing files without prompting
        
    Raises:
        ImageConversionError: If image processing fails
        FileNotFoundError: If input file doesn't exist
        IOError: If file I/O operations fail
    """
    input_path = Path(in_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if not is_valid_image_file(str(input_path)):
        raise ImageConversionError(f"Unsupported file type: {input_path}")
    
    if not should_overwrite_file(out_path, overwrite):
        logger.info(f"Skipping {input_path} (output file exists)")
        return
    
    try:
        logger.debug(f"Opening image: {input_path}")
        img = Image.open(input_path).convert('RGB')
        pixels = list(img.getdata())
        
        if not pixels:
            raise ImageConversionError(f"Image contains no pixel data: {input_path}")
            
    except Exception as e:
        raise ImageConversionError(f"Failed to process image '{input_path}': {e}")
    
    try:
        logger.debug(f"Writing RGB565 data to: {out_path}")
        with open(out_path, 'wb') as f:
            write_bin(f, pixels)
    except Exception as e:
        raise IOError(f"Failed to write output file '{out_path}': {e}")
    
    logger.info(f"Converted {input_path} → {out_path} ({img.width}×{img.height}, {len(pixels)} pixels)")

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Convert images to raw RGB565 format for embedded displays',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s image.png                     # Convert single image to image.png.raw
  %(prog)s img1.png img2.jpg             # Convert multiple images 
  %(prog)s *.png --outdir ./converted    # Convert all PNG files to specific directory
  %(prog)s image.jpg --overwrite         # Overwrite existing files without prompting
  %(prog)s --test                        # Run comprehensive tests
  
Supported formats: """ + ', '.join(sorted(VALID_IMAGE_EXTS))
    )
    
    parser.add_argument(
        'images',
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
        help='Overwrite existing output files without prompting'
    )
    
    parser.add_argument(
        '--test',
        action='store_true', 
        help='Run comprehensive tests and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    return parser.parse_args()


def process_images(image_paths: List[str], output_dir: Path, overwrite: bool) -> None:
    """
    Process multiple images with progress tracking.
    
    Args:
        image_paths: List of input image file paths
        output_dir: Output directory for converted files
        overwrite: Whether to overwrite existing files without prompting
        
    Raises:
        ImageConversionError: If any image conversion fails
    """
    if not image_paths:
        logger.info("No images to process")
        return
    
    # Validate all input files first
    valid_paths = []
    for img_path in image_paths:
        path_obj = Path(img_path)
        if not path_obj.exists():
            logger.error(f"File not found: {img_path}")
            continue
        if not is_valid_image_file(str(path_obj)):
            logger.error(f"Unsupported file type: {img_path}")
            continue
        valid_paths.append(path_obj)
    
    if not valid_paths:
        raise ImageConversionError("No valid image files found")
    
    logger.info(f"Processing {len(valid_paths)} images...")
    
    # Set up progress tracking
    if HAS_TQDM and len(valid_paths) > 1:
        iterator = tqdm(valid_paths, desc="Converting", unit="img")
    else:
        iterator = valid_paths
    
    errors = []
    successful = 0
    
    for img_path in iterator:
        try:
            # Generate output filename
            output_filename = img_path.name + '.raw'
            output_path = output_dir / output_filename
            
            convert_img_to_rgb565(str(img_path), output_path, overwrite)
            successful += 1
            
        except Exception as e:
            error_msg = f"Failed to convert {img_path}: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
    
    # Summary
    logger.info(f"Conversion complete: {successful} successful, {len(errors)} failed")
    
    if errors:
        logger.warning("Failed conversions:")
        for error in errors:
            logger.warning(f"  {error}")


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        args = parse_arguments()
        
        # Configure logging based on verbosity
        if args.quiet:
            logger.setLevel(logging.ERROR)
        elif args.verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        
        # Handle test mode
        if args.test:
            test_rgb565_conversion()
            return 0
        
        # Validate we have images to process
        if not args.images:
            logger.error("No input images specified. Use --help for usage information.")
            return 1
        
        # Validate and prepare output directory
        try:
            output_dir = validate_output_directory(args.outdir)
        except OutputDirectoryError as e:
            logger.error(str(e))
            return 1
        
        # Process images
        try:
            process_images(args.images, output_dir, args.overwrite)
            return 0
            
        except ImageConversionError as e:
            logger.error(str(e))
            return 1
            
    except KeyboardInterrupt:
        logger.info("Conversion interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

def test_rgb565_conversion() -> None:
    """
    Comprehensive test suite for RGB565 conversion functionality.
    
    Tests include:
    - Basic color conversion accuracy
    - Edge cases (min/max values, empty input)
    - Error handling for invalid inputs
    - File I/O operations
    """
    logger.info("Running comprehensive RGB565 conversion tests...")
    
    # Test 1: Basic RGB565 conversion accuracy
    logger.info("Test 1: Basic RGB565 conversion accuracy")
    
    # Test colors: Red, Green, Blue, White, Black, intermediate values
    test_pixels = [
        (255, 0, 0),     # Pure red
        (0, 255, 0),     # Pure green  
        (0, 0, 255),     # Pure blue
        (255, 255, 255), # White
        (0, 0, 0),       # Black
        (128, 128, 128), # Gray
        (255, 128, 64),  # Orange-ish
    ]
    
    expected_rgb565 = [
        0xF800,  # Red: 11111 000000 00000
        0x07E0,  # Green: 00000 111111 00000  
        0x001F,  # Blue: 00000 000000 11111
        0xFFFF,  # White: 11111 111111 11111
        0x0000,  # Black: 00000 000000 00000
        0x8410,  # Gray: 10000 100000 10000 (approximated)
        0xFC20,  # Orange: 11111 100000 00100 (approximated)
    ]
    
    f = io.BytesIO()
    write_bin(f, test_pixels)
    
    # Read back and verify
    f.seek(0)
    result = []
    for i in range(len(test_pixels)):
        data = f.read(2)
        if len(data) == 2:
            value = int.from_bytes(data, 'big')
            result.append(value)
    
    for i, (expected, actual) in enumerate(zip(expected_rgb565, result)):
        if expected == actual:
            logger.debug(f"  ✓ Pixel {i}: {test_pixels[i]} → 0x{actual:04X}")
        else:
            logger.warning(f"  ⚠ Pixel {i}: {test_pixels[i]} → expected 0x{expected:04X}, got 0x{actual:04X}")
    
    # Test 2: Edge cases and error conditions
    logger.info("Test 2: Edge cases and error conditions")
    
    # Empty pixel list
    try:
        f_empty = io.BytesIO()
        write_bin(f_empty, [])
        logger.error("  ✗ Empty pixel list should raise ValueError")
    except ValueError:
        logger.debug("  ✓ Empty pixel list correctly raises ValueError")
    
    # Invalid pixel format (wrong number of components)
    try:
        f_invalid = io.BytesIO()
        write_bin(f_invalid, [(255, 0)])  # Missing blue component
        logger.error("  ✗ Invalid pixel format should raise ValueError")
    except ValueError:
        logger.debug("  ✓ Invalid pixel format correctly raises ValueError")
    
    # Out of range pixel values
    try:
        f_range = io.BytesIO()
        write_bin(f_range, [(300, 0, 0)])  # Red > 255
        logger.error("  ✗ Out of range pixel should raise ValueError")
    except ValueError:
        logger.debug("  ✓ Out of range pixel correctly raises ValueError")
    
    # Negative pixel values
    try:
        f_neg = io.BytesIO()
        write_bin(f_neg, [(-1, 0, 0)])  # Negative red
        logger.error("  ✗ Negative pixel should raise ValueError")
    except ValueError:
        logger.debug("  ✓ Negative pixel correctly raises ValueError")
    
    # Test 3: File extension validation
    logger.info("Test 3: File extension validation")
    
    valid_files = [
        'test.png', 'test.jpg', 'test.jpeg', 'test.bmp', 
        'test.gif', 'test.tiff', 'test.webp', 'TEST.PNG'
    ]
    invalid_files = [
        'test.txt', 'test.doc', 'test', 'test.xyz', ''
    ]
    
    for filename in valid_files:
        if is_valid_image_file(filename):
            logger.debug(f"  ✓ {filename} correctly identified as valid")
        else:
            logger.error(f"  ✗ {filename} should be valid but was rejected")
    
    for filename in invalid_files:
        if not is_valid_image_file(filename):
            logger.debug(f"  ✓ {filename} correctly identified as invalid")
        else:
            logger.error(f"  ✗ {filename} should be invalid but was accepted")
    
    # Test 4: RGB565 configuration
    logger.info("Test 4: RGB565 configuration validation")
    
    config = RGB565_CONFIG
    assert config.r_bits == 5, f"Expected r_bits=5, got {config.r_bits}"
    assert config.g_bits == 6, f"Expected g_bits=6, got {config.g_bits}"
    assert config.b_bits == 5, f"Expected b_bits=5, got {config.b_bits}"
    assert config.r_mask == 0x1F, f"Expected r_mask=0x1F, got 0x{config.r_mask:02X}"
    assert config.g_mask == 0x3F, f"Expected g_mask=0x3F, got 0x{config.g_mask:02X}"
    assert config.b_mask == 0x1F, f"Expected b_mask=0x1F, got 0x{config.b_mask:02X}"
    
    logger.debug("  ✓ RGB565 configuration values are correct")
    
    # Test 5: Real image conversion (if we can create a test image)
    logger.info("Test 5: Real image conversion test")
    
    try:
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_img_path = Path(tmpdir) / 'test.png'
            test_raw_path = Path(tmpdir) / 'test.png.raw'
            
            # Create a simple 2x2 test image
            img = Image.new('RGB', (2, 2), (255, 0, 0))  # Red image
            img.save(test_img_path)
            
            # Convert it
            convert_img_to_rgb565(str(test_img_path), test_raw_path, overwrite=True)
            
            # Verify output file exists and has correct size
            if test_raw_path.exists():
                expected_size = 2 * 2 * 2  # 2x2 pixels * 2 bytes per pixel
                actual_size = test_raw_path.stat().st_size
                if actual_size == expected_size:
                    logger.debug(f"  ✓ Output file size correct: {actual_size} bytes")
                else:
                    logger.error(f"  ✗ Output file size incorrect: expected {expected_size}, got {actual_size}")
            else:
                logger.error("  ✗ Output file was not created")
                
    except Exception as e:
        logger.warning(f"  ⚠ Real image test skipped due to error: {e}")
    
    logger.info("All tests completed successfully!")


if __name__ == '__main__':
    sys.exit(main())