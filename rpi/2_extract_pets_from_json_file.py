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

def clean_name(name: str) -> str:
    """Clean and sanitize pet name for file/output use."""
    name = name.replace(' ', '')
    name = name.replace('(', '_').replace(')', '_')
    return name

def extract_pets(input_file: Path = Path('pets.json'), output_file: Path = Path('pets.wget.queue.txt')) -> None:
    """
    Extract pets with photos from the input JSON file and write name:url pairs to the output file.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    try:
        with input_file.open() as fh:
            data = json.load(fh)
    except FileNotFoundError:
        logging.error(f"Input file {input_file} not found.")
        return
    except json.JSONDecodeError:
        logging.error(f"Failed to parse {input_file}.")
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
            # Clean first, then check for courtesy
            cleaned_name = clean_name(name)
            if 'courtesy' in name.lower():
                skipped_courtesy += 1
                continue
            photos = k.get('photos', [])
            if not photos:
                logging.warning(f"{name} has no photos")
                skipped_no_photo += 1
                continue
            # Prefer 'small' version, fallback to first url if needed
            url = photos[0].get('small') or next(iter(photos[0].values()), None)
            if not url:
                logging.warning(f"No usable photo for {name}")
                skipped_no_photo += 1
                continue
            pets[cleaned_name] = url
        except Exception as e:
            logging.error(f"Error processing pet {k.get('name', 'UNKNOWN')}: {e}")

    lines = [f"{k}:{v}\n" for k, v in pets.items()]
    with output_file.open('w') as fh:
        fh.writelines(lines)

    logging.info(f"Wrote {len(pets)} pets to {output_file}")
    logging.info(f"Skipped {skipped_no_photo} pets with no photos and {skipped_courtesy} courtesy pets.")

def main() -> None:
    extract_pets()

if __name__ == "__main__":
    main()