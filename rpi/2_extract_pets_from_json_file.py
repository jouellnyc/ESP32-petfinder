#!/usr/bin/env python3
"""
Extracts pet records from a JSON file and writes pet names and photo URLs to a queue file.
Requires: pets.json file in the same directory.
Outputs: pets.wget.queue.txt with name:url pairs.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any
import argparse

def clean_name(name: str) -> str:
    """Clean and sanitize pet name for file/output use."""
    name = name.replace(' ', '')
    name = name.replace('(', '_').replace(')', '_')
    return name

def extract_pets(input_file: Path = Path('pets.json'), output_file: Path = Path('pets.wget.queue.txt'), photo_size: str = 'small') -> None:
    """
    Extract pets with photos from the input JSON file and write name:url pairs to the output file.
    Args:
        input_file: Path to the input JSON.
        output_file: Path to the output txt.
        photo_size: Preferred photo size key ('small', 'medium', etc.)
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
    try:
        if not input_file.exists():
            logging.error(f"Input file {input_file} not found.")
            return
        with input_file.open() as fh:
            data = json.load(fh)
    except json.JSONDecodeError:
        logging.exception(f"Failed to parse {input_file}.")
        return

    if not isinstance(data, dict) or 'animals' not in data:
        logging.error("Invalid data format in pets.json")
        return

    pets: Dict[str, str] = {}
    skipped_no_photo = 0
    skipped_courtesy = 0
    for k in data['animals']:
        try:
            name = k.get('name', '').strip()
            if 'courtesy' in name.lower():
                skipped_courtesy += 1
                continue
            photos = k.get('photos', [])
            if not photos or not isinstance(photos[0], dict):
                logging.warning(f"{name} has no valid photos")
                skipped_no_photo += 1
                continue
            url = photos[0].get(photo_size) or next(iter(photos[0].values()), None)
            if not url:
                logging.warning(f"No usable photo for {name}")
                skipped_no_photo += 1
                continue
            cleaned_name = clean_name(name)
            pets[cleaned_name] = url
        except Exception as e:
            logging.exception(f"Error processing pet {k.get('name', 'UNKNOWN')}")

    with output_file.open('w') as fh:
        fh.writelines(f"{k}:{v}\n" for k, v in pets.items())

    logging.info(f"Wrote {len(pets)} pets to {output_file}")
    logging.info(f"Skipped {skipped_no_photo} pets with no photos and {skipped_courtesy} courtesy pets.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract pets with photos from a JSON file.")
    parser.add_argument('--input', type=str, default='pets.json', help='Input JSON file (default: pets.json)')
    parser.add_argument('--output', type=str, default='pets.wget.queue.txt', help='Output queue file (default: pets.wget.queue.txt)')
    parser.add_argument('--photo-size', type=str, default='small', help="Preferred photo size (default: 'small')")
    args = parser.parse_args()
    extract_pets(Path(args.input), Path(args.output), args.photo_size)

if __name__ == "__main__":
    main()