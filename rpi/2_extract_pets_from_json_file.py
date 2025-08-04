#!/usr/bin/env python3
"""
Extracts pet records from a JSON file and writes pet names and photo URLs to a queue file.
Requires: pets.json file in the same directory.
Outputs: pets.wget.queue.txt with name:url pairs.
"""
import json
import logging

def clean_name(name):
    name = name.replace(' ', '')
    name = name.replace('(', '_').replace(')', '_')
    return name

def main():
    INPUT_FILE = 'pets.json'
    OUTPUT_FILE = 'pets.wget.queue.txt'
    pets = {}

    try:
        with open(INPUT_FILE) as fh:
            data = json.load(fh)
    except FileNotFoundError:
        print(f"Input file {INPUT_FILE} not found.")
        return
    except json.JSONDecodeError:
        print(f"Failed to parse {INPUT_FILE}.")
        return

    if not isinstance(data, dict) or 'animals' not in data:
        print("Invalid data format in pets.json")
        return

    for k in data['animals']:
        try:
            photos = k.get('photos', [])
            if not photos:
                logging.warning(f"{k['name']} has no photos")
                continue
            if 'Courtesy' in k['name']:
                continue
            k['name'] = clean_name(k['name'])
            # Small pics seems easier to make larger than to make large pics smaller for the ili9341 and underlying libraries
            url = photos[0]['small']
            pets[k['name']] = url
        except Exception as e:
            logging.error(f"Error processing pet {k.get('name', 'UNKNOWN')}: {e}")

    with open(OUTPUT_FILE, 'w') as fh:
        for k, v in pets.items():
            fh.write(f"{k}:{v}\n")

if __name__ == "__main__":
    main()